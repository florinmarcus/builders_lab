"""Front door for the public endpoint (ADR 0007). Runs before the MCP layer.

Order: health check, kill switch, lockdown, IP block, per-IP limit, secret path, API key, per-key limit.
Strangers get short generic answers and never reach the MCP layer.
"""

from __future__ import annotations

import json
import logging
import os

import anyio.to_thread

from builders_api import security
from builders_api.mcp_server.ratelimit import TokenBucket

log = logging.getLogger(__name__)


def _client_ip(scope) -> str:
    """Peer address. Behind our own proxy (Caddy or tunnel), uvicorn's proxy_headers sets it from
    X-Forwarded-For for trusted proxies only, so a caller cannot fake it."""
    return (scope.get("client") or ("unknown",))[0]


def _key_from_headers(headers: dict[bytes, bytes]) -> str | None:
    """Key from `Authorization: Bearer <key>`, `Authorization: <key>` or `X-API-Key: <key>`."""
    auth = headers.get(b"authorization", b"").decode(errors="replace").strip()
    if auth:
        if auth[:9].lower() == "bearerbl_":  # "Bearer" typed without the space
            auth = "Bearer " + auth[6:]
        word, _, rest = auth.partition(" ")
        key = rest.strip() if word.rstrip(":").lower() == "bearer" else auth
        if key:
            return key
    key = headers.get(b"x-api-key", b"").decode(errors="replace").strip()
    return key or None


def _auth_shape(headers: dict[bytes, bytes]) -> str:
    """Shape of the Authorization header for the log: first word and lengths only, never the key."""
    auth = headers.get(b"authorization", b"").decode(errors="replace")
    if not auth:
        return "none"
    word, _, rest = auth.strip().partition(" ")
    first = word if word.rstrip(":").lower() in ("bearer", "basic", "token") else f"<{len(word)} chars>"
    return f"first word {first!r}, then {len(rest.strip())} chars, total {len(auth)}"


async def _reply(send, status: int, code: str, message: str, extra_headers=()) -> None:
    body = json.dumps({"error": {"code": code, "message": message}}).encode()
    headers = [(b"content-type", b"application/json"), *extra_headers]
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


class Gateway:
    def __init__(self, app, *, mcp_paths: tuple[str, ...], guard: security.Guard | None = None,
                 per_ip_per_minute: int = 60, per_key_per_minute: int = 120) -> None:
        self.app = app
        self.mcp_paths = {p.rstrip("/") for p in mcp_paths}
        self.guard = guard or security.Guard()
        self.per_ip = TokenBucket(per_ip_per_minute)
        self.per_key = TokenBucket(per_key_per_minute)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":  # lifespan events pass through
            return await self.app(scope, receive, send)
        path = scope.get("path", "").rstrip("/")
        if path == "/healthz":
            return await _reply(send, 200, "ok", "ok")
        if await anyio.to_thread.run_sync(security.kill_switch_on):
            return await _reply(send, 503, "switched_off", "Service paused. Please try again later.")
        if self.guard.locked_down():
            return await _reply(send, 503, "paused", "Service paused. Please try again later.", [(b"retry-after", b"900")])
        ip = _client_ip(scope)
        if self.guard.is_blocked(ip):
            return await _reply(send, 403, "blocked", "Forbidden.")
        self.guard.record_request()
        if not self.per_ip.allow(ip):
            return await _reply(send, 429, "rate_limited", "Too many requests. Wait a minute.", [(b"retry-after", b"60")])
        if path not in self.mcp_paths:
            self.guard.record_failure(ip, count_for_lockdown=False)
            return await _reply(send, 404, "not_found", "Not found.")
        key = _key_from_headers(dict(scope.get("headers") or []))
        caller = await anyio.to_thread.run_sync(security.check_key, key) if key else None
        if caller is None:
            headers = dict(scope.get("headers") or [])
            reason = await anyio.to_thread.run_sync(security.key_failure_reason, key)
            log.warning("401 from %s: %s (authorization: %s; x-api-key present: %s)", ip, reason,
                        _auth_shape(headers), b"x-api-key" in headers)
            self.guard.record_failure(ip)
            return await _reply(send, 401, "unauthorised", "Missing or invalid API key.")
        if not self.per_key.allow(caller.key_prefix):
            return await _reply(send, 429, "rate_limited", "Too many requests. Wait a minute.", [(b"retry-after", b"60")])
        token = security.current_caller.set(caller)
        try:
            return await self.app(scope, receive, send)
        finally:
            security.current_caller.reset(token)


def mcp_path_from_env() -> str:
    """The MCP path includes a long random segment, e.g. /mcp/3f9c... (set MCP_PATH_SECRET)."""
    secret = os.environ.get("MCP_PATH_SECRET", "").strip()
    if len(secret) < 16:
        raise RuntimeError("MCP_PATH_SECRET must be set to a random string of at least 16 characters.")
    return f"/mcp/{secret}"


def regulations_path(mcp_path: str) -> str:
    """The regulations server sits under the same secret path (ADR 0015): /mcp/<secret>/regulations."""
    return mcp_path.rstrip("/") + "/regulations"
