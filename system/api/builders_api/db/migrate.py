"""Apply SQL migrations in order. Safe to run many times.

Usage: python -m builders_api.db.migrate
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import psycopg

from builders_api.config import database_url

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class MigrationChangedError(RuntimeError):
    """An applied migration file was edited. Add a new file instead."""


def _migrations() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))


def migrate(url: str | None = None) -> list[str]:
    """Apply pending migrations. Returns the names applied this run."""
    applied: list[str] = []
    with psycopg.connect(url or database_url()) as conn:
        conn.execute(
            """create table if not exists schema_migrations (
                   name text primary key,
                   sha256 text not null,
                   applied_at timestamptz not null default now())"""
        )
        done = dict(conn.execute("select name, sha256 from schema_migrations").fetchall())
        for path in _migrations():
            sql = path.read_text()
            digest = hashlib.sha256(sql.encode()).hexdigest()
            if path.name in done:
                if done[path.name] != digest:
                    raise MigrationChangedError(path.name)
                continue
            with conn.transaction():
                conn.execute(sql)
                conn.execute(
                    "insert into schema_migrations (name, sha256) values (%s, %s)",
                    (path.name, digest),
                )
            applied.append(path.name)
    return applied


if __name__ == "__main__":
    names = migrate()
    print("applied:", ", ".join(names) if names else "nothing new")
