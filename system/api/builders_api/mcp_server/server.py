"""MCP server (official SDK's MCPServer, the successor of FastMCP) over streamable HTTP.

Every tool: daily quota check, one trace row, structured errors (never a stack trace).
Demo only: no login, every call acts for the mock firm in DEMO_FIRM_SLUG. Real use needs OAuth.

Run: python -m builders_api.mcp_server  (HOST, PORT, DATABASE_URL from the environment)
"""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import Callable
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from builders_api import quotas, versions
from builders_api.config import demo_firm_slug, rate_limit_per_minute
from builders_api.db import connection
from builders_api.errors import AppError
from builders_api.mcp_server.ratelimit import RateLimitMiddleware
from builders_api.service import documents, inbox, jobs, payments, regulations
from builders_api.tracing import Span, traced

log = logging.getLogger(__name__)
AI_NOTICE = "AI-generated, check before use. Mock data only."
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)


def _sources(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect cited sources from a tool result for the trace row (ids and labels only)."""
    found: list[dict[str, Any]] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            if x.get("type") in ("email", "document") and "id" in x:
                found.append({"type": x["type"], "id": x["id"], "label": x.get("label")})
            elif "edition_date" in x and "url" in x:
                found.append({"type": "regulation", "source": x.get("source"), "section": x.get("section"),
                              "edition_date": x.get("edition_date")})
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(result)
    unique = {repr(sorted(s.items())): s for s in found}
    return list(unique.values())[:100]


def run_tool(name: str, call: Callable[[uuid.UUID], dict[str, Any]]) -> dict[str, Any]:
    """Wrap one tool call: firm, quota, trace, errors."""
    version = versions.get("tool_description", name)
    span = Span(trace_id=uuid.uuid4(), kind="tool", name=name, version_id=version.id)
    try:
        with traced(span):
            span.firm_id = jobs.firm_id(demo_firm_slug())
            quotas.consume(span.firm_id, "tool_calls")
            result = call(span.firm_id)
            span.sources = _sources(result)
        return {"ai_notice": AI_NOTICE, **result, "trace_id": str(span.trace_id)}
    except AppError as exc:
        return {"error": exc.to_dict(), "trace_id": str(span.trace_id)}
    except Exception:  # noqa: BLE001 - logged here, never shown to the user
        log.exception("tool %s failed (trace %s)", name, span.trace_id)
        return {
            "error": {
                "code": "internal_error",
                "message": "Something went wrong on our side. Please try again; quote this trace id if it keeps failing.",
                "retryable": False,
            },
            "trace_id": str(span.trace_id),
        }


def build_server() -> MCPServer:
    instructions = versions.get("server_instructions", "instructions")
    server = MCPServer(
        name="oakline-builders-demo",
        title="Builders Lab demo (Oakline Build, mock data)",
        instructions=instructions.text,
        version=instructions.id,
    )

    def desc(name: str) -> str:
        return versions.get("tool_description", name).text

    @server.tool(description=desc("list_jobs"), annotations=READ_ONLY)
    def list_jobs(since_days: int = 1) -> dict[str, Any]:
        return run_tool("list_jobs", lambda f: jobs.list_jobs(f, since_days))

    @server.tool(description=desc("get_job"), annotations=READ_ONLY)
    def get_job(job: str) -> dict[str, Any]:
        return run_tool("get_job", lambda f: jobs.get_job(f, job))

    @server.tool(description=desc("list_missing_items"), annotations=READ_ONLY)
    def list_missing_items(job: str) -> dict[str, Any]:
        return run_tool("list_missing_items", lambda f: jobs.list_missing_items(f, job))

    @server.tool(description=desc("search_job_documents"), annotations=READ_ONLY)
    def search_job_documents(query: str, job: str | None = None, limit: int = 10) -> dict[str, Any]:
        return run_tool("search_job_documents", lambda f: documents.search_job_documents(f, query, job, limit))

    @server.tool(description=desc("search_regulations"), annotations=READ_ONLY)
    def search_regulations(question: str, as_of_date: str | None = None) -> dict[str, Any]:
        return run_tool("search_regulations", lambda f: regulations.search_regulations(question, as_of_date))

    @server.tool(description=desc("get_payment_dates"), annotations=READ_ONLY)
    def get_payment_dates(job: str) -> dict[str, Any]:
        return run_tool("get_payment_dates", lambda f: payments.get_payment_dates(f, job))

    @server.tool(description=desc("sync_inbox"), annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
    def sync_inbox() -> dict[str, Any]:
        return run_tool("sync_inbox", lambda f: inbox.sync_inbox(f))

    return server


def startup_checks() -> None:
    """Refuse to start if a versioned text was edited in place; record versions in the database."""
    versions.active()
    with connection() as conn:
        versions.register(conn)


def build_app():
    startup_checks()
    server = build_server()
    host = os.environ.get("HOST", "127.0.0.1")
    allowed = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
    security = None
    if allowed:  # behind a tunnel: accept the public host name(s)
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed + ["127.0.0.1:*", "localhost:*"],
            allowed_origins=["https://claude.ai", "https://claude.com"],  # Claude often sends no Origin at all
        )
    app = server.streamable_http_app(stateless_http=True, json_response=True, transport_security=security, host=host)
    return RateLimitMiddleware(app, rate_limit_per_minute())
