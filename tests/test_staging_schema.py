"""Staging schema for overnight corpus loads (corpus/OVERNIGHT-PLAN.md, S0).

New corpora load into schema corpus_next; the server keeps reading schema corpus until promote swaps them.
Unit tests need no database. The database test skips unless CORPUS_TEST_OWNER_URL / CORPUS_TEST_READER_URL are set.
"""

import os

import pytest

from system.rag import load as L
from system.rag import pgsearch as P
from system.rag import promote as PR


def test_schema_names_are_checked():
    for good in ("corpus", "corpus_next", "corpus_prev"):
        assert L.check_schema(good) == good
    for bad in ("Corpus", "corpus; drop table x", "", "1corpus", "a" * 60, "corpus.chunks"):
        with pytest.raises(ValueError):
            L.check_schema(bad)


def test_loader_ddl_and_queries_use_the_chosen_schema():
    sql = L.ddl("corpus_next")
    assert "CREATE SCHEMA IF NOT EXISTS corpus_next" in sql
    assert "corpus_next.chunks" in sql and "corpus_next.lexemes" in sql and "corpus_next.stats" in sql
    assert "corpus.chunks" not in sql.replace("corpus_next.chunks", "")
    grants = L.grants("corpus_next")
    assert "GRANT USAGE ON SCHEMA corpus_next TO builders_corpus_reader" in grants
    assert "GRANT SELECT ON ALL TABLES IN SCHEMA corpus_next TO builders_corpus_reader" in grants


def test_default_schema_is_still_corpus(monkeypatch):
    monkeypatch.delenv("RAG_SCHEMA", raising=False)
    assert P.cfg()["schema"] == "corpus"
    assert "FROM corpus.chunks" in P.nearest_sql("corpus")


def test_search_can_read_another_schema(monkeypatch):
    monkeypatch.setenv("RAG_SCHEMA", "corpus_next")
    assert P.cfg()["schema"] == "corpus_next"
    assert "FROM corpus_next.chunks" in P.nearest_sql(P.cfg()["schema"])
    monkeypatch.setenv("RAG_SCHEMA", "corpus; drop")
    with pytest.raises(ValueError):
        P.cfg()


def test_candidates_are_what_search_reranks(monkeypatch):
    rows = [{"id": f"c{i}", "source_id": "s", "section_id": f"sec{i % 3}", "embed_text": f"t{i}", "text": f"t{i}",
             "distance": i / 10} for i in range(6)]
    monkeypatch.setenv("RAG_HYBRID", "0")  # vector path only (hybrid fusion: tests/test_pgsearch.py)
    monkeypatch.setattr(P, "nearest", lambda v, d, c, n, url=None, schema=None: rows)
    cands = P.candidates("q", embed=lambda q: [0.0])
    assert [r["section_id"] for r in cands] == ["sec0", "sec1", "sec2"]  # one per section, in order
    got = P.search("q", embed=lambda q: [0.0], rerank_fn=lambda q, texts, n: [(2, 0.9), (0, 0.5)])
    assert [p["section_id"] for p in got] == ["sec2", "sec0"]


def test_promote_and_rollback_sql_swap_in_one_transaction():
    up = PR.promote_sql()
    assert up.index("DROP SCHEMA IF EXISTS corpus_prev CASCADE") < up.index("ALTER SCHEMA corpus RENAME TO corpus_prev")
    assert up.index("ALTER SCHEMA corpus RENAME TO corpus_prev") < up.index("ALTER SCHEMA corpus_next RENAME TO corpus")
    assert "GRANT SELECT ON ALL TABLES IN SCHEMA corpus TO builders_corpus_reader" in up
    down = PR.rollback_sql()
    assert down.index("ALTER SCHEMA corpus RENAME TO corpus_failed") < down.index("ALTER SCHEMA corpus_prev RENAME TO corpus")


@pytest.mark.skipif(not os.environ.get("CORPUS_TEST_OWNER_URL"), reason="needs Postgres with pgvector")
def test_staging_load_leaves_the_live_schema_alone(tmp_path):
    psycopg = pytest.importorskip("psycopg")
    from tests.test_load import write_corpus

    cdir, vdir = write_corpus(tmp_path, n=4)
    owner = os.environ["CORPUS_TEST_OWNER_URL"]
    with psycopg.connect(owner) as c:
        before = c.execute("SELECT to_regclass('corpus.stats') IS NOT NULL").fetchone()[0] and \
            c.execute("SELECT max(loaded_at) FROM corpus.stats").fetchone()[0]
    r = L.load(owner, cdir, vdir, schema="corpus_next")
    assert r["chunks"] == 4
    with psycopg.connect(owner) as c:
        after = c.execute("SELECT to_regclass('corpus.stats') IS NOT NULL").fetchone()[0] and \
            c.execute("SELECT max(loaded_at) FROM corpus.stats").fetchone()[0]
    assert before == after
    with psycopg.connect(os.environ["CORPUS_TEST_READER_URL"]) as c:
        assert c.execute("SELECT count(*) FROM corpus_next.chunks").fetchone()[0] == 4
