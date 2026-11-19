"""Tests need a throwaway Postgres. Set TEST_DATABASE_URL; that database is wiped."""

from __future__ import annotations

import os

import psycopg
import pytest

from builders_api import db
from builders_api.db.migrate import migrate
from builders_api.db.seed import seed


@pytest.fixture()
def db_url(monkeypatch) -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("drop schema public cascade; create schema public;")
    migrate(url)
    monkeypatch.setenv("DATABASE_URL", url)
    db.reset_pool()
    yield url
    db.reset_pool()


@pytest.fixture()
def conn(db_url):
    with psycopg.connect(db_url) as c:
        yield c


@pytest.fixture()
def seeded(db_url) -> str:
    seed(db_url)
    return db_url
