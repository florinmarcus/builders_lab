"""Deep health check for upgrades: database reachable, no pending migrations, versions unchanged.

Usage: python -m builders_api.healthcheck   (exit 0 = healthy)
"""

from __future__ import annotations

import sys

import psycopg

from builders_api import versions
from builders_api.config import database_url
from builders_api.db.migrate import MIGRATIONS_DIR


def check() -> list[str]:
    problems = []
    try:
        with psycopg.connect(database_url(), connect_timeout=5) as conn:
            applied = {r[0] for r in conn.execute("select name from schema_migrations").fetchall()}
    except Exception as exc:  # noqa: BLE001
        return [f"database: {type(exc).__name__}"]
    pending = [p.name for p in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql")) if p.name not in applied]
    if pending:
        problems.append(f"pending migrations: {', '.join(pending)}")
    problems += versions.check_lock()
    return problems


if __name__ == "__main__":
    found = check()
    print("healthy" if not found else "\n".join(found))
    sys.exit(1 if found else 0)
