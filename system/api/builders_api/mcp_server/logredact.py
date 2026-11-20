"""Keep the MCP path secret out of the logs.

Request lines from uvicorn include the full path, and the MCP path holds a secret
(MCP_PATH_SECRET). Logs are shipped to CloudWatch (deploy/compose.aws.yaml), so every log
record is masked before it is written: the secret becomes "<path-secret>".
"""

from __future__ import annotations

import copy
import logging
import os

MASK = "<path-secret>"


class RedactSecret(logging.Filter):
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.secret = os.environ.get("MCP_PATH_SECRET", "").strip()

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.secret:
            return True
        message = record.getMessage()
        if self.secret in message:
            record.msg = message.replace(self.secret, MASK)
            record.args = None
        return True


def uvicorn_log_config() -> dict:
    """uvicorn's own logging config, with the filter on its handlers."""
    from uvicorn.config import LOGGING_CONFIG

    cfg = copy.deepcopy(LOGGING_CONFIG)
    cfg.setdefault("filters", {})["redact"] = {"()": "builders_api.mcp_server.logredact.RedactSecret"}
    for handler in cfg["handlers"].values():
        handler.setdefault("filters", []).append("redact")
    return cfg


def install_on_root() -> None:
    """Mask records from the app's own loggers too (they go through the root handler)."""
    for handler in logging.getLogger().handlers:
        handler.addFilter(RedactSecret())
