"""Settings from environment variables (see .env.example). No secrets in code."""

from __future__ import annotations

import os


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
    return url
