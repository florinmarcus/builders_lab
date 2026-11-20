"""End to end: start the real MCP server over HTTP (behind the Gateway) and call it."""

import datetime as dt
import json
import socket
import threading
import time

import anyio
import httpx2 as httpx
import pytest
import uvicorn

import mcp
from builders_api import security, versions
from builders_api.admin import create_key, extend_key, revoke_key
from builders_api.mcp_server.server import build_app

SECRET = "test-path-secret-0123456789"


@pytest.fixture()
def server(seeded, monkeypatch):
    monkeypatch.setenv("MCP_PATH_SECRET", SECRET)
    monkeypatch.setenv("API_KEY_PEPPER", "test-pepper")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1000")
    security._kill_cache = (0.0, False)
    guard = security.Guard(fail_limit=3, lockdown_failures_per_min=1000)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    srv = uvicorn.Server(uvicorn.Config(build_app(guard), host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.05)
    base = f"http://127.0.0.1:{port}"
    yield {"base": base, "url": f"{base}/mcp/{SECRET}", "guard": guard}
    srv.should_exit = True
    thread.join(timeout=5)


def _payload(result) -> dict:
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    return json.loads(result.content[0].text)


def _call(url: str, key: str, tool: str, args: dict):
    async def run():
        from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
        async with create_mcp_http_client(headers={"Authorization": f"Bearer {key}"}) as client:
            async with mcp.Client(streamable_http_client(url, http_client=client)) as c:
                names = {t.name for t in (await c.list_tools()).tools}
                return names, _payload(await c.call_tool(tool, args))
    return anyio.run(run)


def test_tools_over_http_with_key(server, conn):
    key = create_key("oakline", "test", dt.date.today() + dt.timedelta(days=60))
    names, ok = _call(server["url"], key, "get_payment_dates", {"job": "office"})
    assert names == {"list_jobs", "get_job", "list_missing_items", "search_job_documents",
                     "search_regulations", "get_payment_dates", "sync_inbox", "save_facts", "verify_answer", "lookup_terms", "get_job_timeline"}
    assert ok["ai_notice"].startswith("AI-generated") and ok["job"]["ref"] == "KWY-4"
    assert "access_notice" not in ok and "untrusted_content_notice" in ok
    _, missing = _call(server["url"], key, "get_job", {"job": "Mill Lane"})
    assert missing["error"]["code"] == "not_found" and "Traceback" not in json.dumps(missing)
    rows = conn.execute("select name, status, version_id, firm_id from traces order by id").fetchall()
    assert [(r[0], r[1]) for r in rows] == [("get_payment_dates", "ok"), ("get_job", "error")]
    assert rows[0][2] == versions.get("tool_description", "get_payment_dates").id and rows[0][3]


def test_strangers_get_nothing(server):
    with httpx.Client() as h:
        assert h.get(server["base"] + "/healthz").status_code == 200
        assert h.post(server["base"] + "/mcp", json={}).status_code == 404
        r = h.post(server["url"], json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert r.status_code == 401 and "tools" not in r.text
        bad = {"Authorization": "Bearer bl_deadbeef_wrong"}
        assert h.post(server["url"], json={}, headers=bad).status_code == 401  # 3rd failure (404, 401, 401)
        assert h.post(server["url"], json={}, headers=bad).status_code == 403  # now this IP is blocked


def test_expiry_messages(server):
    key = create_key("oakline", "test", dt.date.today() + dt.timedelta(days=5))
    _, out = _call(server["url"], key, "list_jobs", {})
    assert "access_notice" in out and "Contact Florin" in out["access_notice"]
    prefix = key.split("_")[1]
    extend_key(prefix, dt.date.today() - dt.timedelta(days=30))  # past the 7-day grace
    _, out = _call(server["url"], key, "list_jobs", {})
    assert out["error"]["code"] == "access_ended" and "jobs" not in out
    extend_key(prefix, dt.date.today() + dt.timedelta(days=90))  # renewal: same key works again
    _, out = _call(server["url"], key, "list_jobs", {})
    assert "jobs" in out and "access_notice" not in out


def test_revoked_key_and_kill_switch(server):
    key = create_key("oakline", "test", dt.date.today() + dt.timedelta(days=60))
    auth = {"Authorization": f"Bearer {key}", "Accept": "application/json, text/event-stream"}
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    with httpx.Client() as h:
        assert h.post(server["url"], json=body, headers=auth).status_code == 200
        security.set_kill_switch(True)
        assert h.post(server["url"], json=body, headers=auth).status_code == 503
        security.set_kill_switch(False)
        assert h.post(server["url"], json=body, headers=auth).status_code == 200
        revoke_key(key.split("_")[1])
        assert h.post(server["url"], json=body, headers=auth).status_code == 401
