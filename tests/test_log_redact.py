"""The MCP path secret must never reach the logs (they go to CloudWatch)."""

import logging

from builders_api.mcp_server.logredact import RedactSecret, uvicorn_log_config

SECRET = "s3cr3t-path-0123456789abcdef"


def record(msg, args):
    return logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, msg, args, None)


def test_access_line_is_masked(monkeypatch):
    monkeypatch.setenv("MCP_PATH_SECRET", SECRET)
    r = record('%s - "%s %s HTTP/%s" %d', ("1.2.3.4:0", "POST", f"/mcp/{SECRET}", "1.1", 200))
    assert RedactSecret().filter(r) is True
    assert r.getMessage() == '1.2.3.4:0 - "POST /mcp/<path-secret> HTTP/1.1" 200'
    assert SECRET not in r.getMessage()


def test_plain_message_is_masked_and_others_untouched(monkeypatch):
    monkeypatch.setenv("MCP_PATH_SECRET", SECRET)
    r = record(f"request to /mcp/{SECRET}/x failed", None)
    RedactSecret().filter(r)
    assert r.getMessage() == "request to /mcp/<path-secret>/x failed"
    r2 = record("401 from %s: %s", ("5.6.7.8", "bad key"))
    RedactSecret().filter(r2)
    assert r2.getMessage() == "401 from 5.6.7.8: bad key"


def test_without_a_secret_nothing_changes(monkeypatch):
    monkeypatch.delenv("MCP_PATH_SECRET", raising=False)
    r = record("GET /healthz", None)
    assert RedactSecret().filter(r) and r.getMessage() == "GET /healthz"


def test_uvicorn_config_puts_the_filter_on_both_handlers():
    cfg = uvicorn_log_config()
    for h in ("default", "access"):
        assert "redact" in cfg["handlers"][h]["filters"]
