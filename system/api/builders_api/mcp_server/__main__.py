"""Run the MCP server: python -m builders_api.mcp_server"""

import logging
import os

import uvicorn

from builders_api.mcp_server.logredact import install_on_root, uvicorn_log_config
from builders_api.mcp_server.server import build_app

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
install_on_root()  # the MCP path secret never reaches the logs (they go to CloudWatch)
uvicorn.run(build_app(), host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")),
            proxy_headers=True,
            # Only our own reverse proxy may set the client address (X-Forwarded-For).
            forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1"),
            server_header=False,
            log_config=uvicorn_log_config())
