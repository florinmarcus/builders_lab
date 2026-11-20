"""Load the small test seed (system/data/mock/db_seed.sql). Deletes and reloads the mock firm.

Usage: python -m builders_api.db.seed
"""

from __future__ import annotations

import os

import psycopg

from builders_api.config import database_url, mock_dir


def seed(url: str | None = None) -> None:
    sql = (mock_dir() / "db_seed.sql").read_text()
    with psycopg.connect(url or os.environ.get("MIGRATE_DATABASE_URL") or database_url()) as conn:
        with conn.transaction():
            conn.execute(sql)


if __name__ == "__main__":
    seed()
    print("seed loaded")
