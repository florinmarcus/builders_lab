"""End to end: start the real MCP server over HTTP and call tools with an MCP client."""

import json
import socket
import threading
import time

import anyio
import pytest
import uvicorn

import mcp
from builders_api import versions
from builders_api.mcp_server.server import build_app


@pytest.fixture()
def server_url(seeded, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1000")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = uvicorn.Server(uvicorn.Config(build_app(), host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    thread.join(timeout=5)


def _payload(result) -> dict:
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    return json.loads(result.content[0].text)


def test_tools_over_http(server_url, conn):
    async def run():
        async with mcp.Client(server_url) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            ok = _payload(await client.call_tool("get_payment_dates", {"job": "office"}))
            missing = _payload(await client.call_tool("get_job", {"job": "Mill Lane"}))
            sync = _payload(await client.call_tool("sync_inbox", {}))
            return names, ok, missing, sync

    names, ok, missing, sync = anyio.run(run)
    assert names == {"list_jobs", "get_job", "list_missing_items", "search_job_documents",
                     "search_regulations", "get_payment_dates", "sync_inbox"}
    assert ok["ai_notice"].startswith("AI-generated") and ok["job"]["ref"] == "KWY-4"
    assert missing["error"]["code"] == "not_found" and "Traceback" not in json.dumps(missing)
    assert sync["error"]["code"] == "not_configured"

    rows = conn.execute("select name, status, error_type, version_id, sources from traces order by id").fetchall()
    assert [(r[0], r[1]) for r in rows] == [("get_payment_dates", "ok"), ("get_job", "error"), ("sync_inbox", "error")]
    assert rows[0][3] == versions.get("tool_description", "get_payment_dates").id
    assert rows[0][4] and rows[1][2] == "not_found"
    used = conn.execute("select used from quota_usage where metric = 'tool_calls'").fetchone()[0]
    assert used == 3
