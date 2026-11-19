"""Database access. One small pool per process."""

from __future__ import annotations

import atexit
from contextlib import contextmanager
from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from builders_api.config import database_url

_pool: ConnectionPool | None = None


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(database_url(), min_size=1, max_size=5, kwargs={"row_factory": dict_row}, open=True)
        atexit.register(reset_pool)
    return _pool


def reset_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
    _pool = None


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    with pool().connection() as conn:
        yield conn
