"""Settings from environment variables (see .env.example). No secrets in code."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
    return url


def demo_firm_slug() -> str:
    """The demo has no login: every call acts for this one mock firm (real use needs OAuth)."""
    return os.environ.get("DEMO_FIRM_SLUG", "oakline")


def rate_limit_per_minute() -> int:
    return int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))


def mock_dir() -> Path:
    return Path(os.environ.get("MOCK_DIR", REPO_ROOT / "system" / "data" / "mock"))


def rag_dir() -> Path:
    """Parent of the corpus session's `rag` package (system/)."""
    return Path(os.environ.get("RAG_PARENT_DIR", REPO_ROOT / "system"))
