"""Tests for the server search (system/rag/pgsearch.py). Logic tests use fake models and fake rows; the database
test needs Postgres with pgvector loaded by system.rag.load (CORPUS_TEST_READER_URL), else it skips."""

import datetime
import importlib
import os

import pytest

from system.rag import pgsearch as P


def row(i, section=None, **kw):
    return {"id": f"c{i}", "source_id": "adb", "source_title": "AD B", "legal_weight": "statutory-guidance",
            "edition_date": datetime.date(2026, 9, 30), "valid_from": datetime.date(2026, 9, 30),
            "valid_to": kw.get("valid_to"), "section_id": section or f"para-{i}", "section_title": None,
            "heading_path": ["AD B", "Section 3", kw.get("title", f"Paragraph 3.{i}")], "printed_page": "26",
            "url": "https://x#page=38", "text": f"text {i}", "embed_text": f"AD B › Section 3\ntext {i}", "distance": 0.1 * i}


def test_rerank_order_floor_and_one_passage_per_section(monkeypatch):
    rows = [row(1), row(2, section="para-1"), row(3), row(4)]
    monkeypatch.setattr(P, "nearest", lambda v, d, c, n, url=None: rows)
    seen = {}

    def fake_rerank(q, texts, n):
        seen["texts"] = texts
        return [(2, 0.9), (0, 0.4), (1, 0.01)]  # the last is below the floor (0.05)

    got = P.search("fire doors", embed=lambda q: [0.0] * 1024, rerank_fn=fake_rerank)
    assert [p["chunk_id"] for p in got] == ["c4", "c1"]  # c2 was the same section as c1
    assert len(seen["texts"]) == 3 and seen["texts"][0].startswith("AD B ›")
    assert got[0]["section"] == "Paragraph 3.4" and got[0]["edition_date"] == "2026-09-30"


def test_nothing_relevant_returns_empty(monkeypatch):
    monkeypatch.setattr(P, "nearest", lambda v, d, c, n, url=None: [row(1)])
    assert P.search("best pizza", embed=lambda q: [0.0] * 1024, rerank_fn=lambda q, t, n: [(0, 0.001)]) == []
    assert P.search("   ") == []


def test_aws_or_network_trouble_is_retryable(monkeypatch):
    def boom(q):
        raise TimeoutError("slow")
    with pytest.raises(P.SearchError) as e:
        P.search("fire doors", embed=boom)
    assert e.value.retryable is True


def test_dated_copy_gets_an_edition_note():
    p = P.passage(row(1, valid_to=datetime.date(2029, 9, 1)), 0.5)
    assert p["edition_note"] == "Text valid until 2029-09-01"


def test_rag_offers_search_only_with_the_reader_url(monkeypatch):
    import system.rag as rag
    monkeypatch.delenv("CORPUS_READER_URL", raising=False)
    assert not hasattr(importlib.reload(rag), "search")
    monkeypatch.setenv("CORPUS_READER_URL", "postgresql://reader@example/builders_corpus")
    assert not hasattr(importlib.reload(rag), "search")  # not switched on yet
    monkeypatch.setenv("RAG_ENABLED", "on")
    assert callable(importlib.reload(rag).search)
    monkeypatch.delenv("CORPUS_READER_URL")
    monkeypatch.delenv("RAG_ENABLED")
    importlib.reload(rag)


@pytest.mark.skipif(not os.environ.get("CORPUS_TEST_READER_URL"), reason="needs Postgres with pgvector and a loaded corpus")
def test_nearest_filters_by_date_and_country_in_the_database():
    import psycopg
    url = os.environ["CORPUS_TEST_READER_URL"]
    with psycopg.connect(url) as c:
        vec = c.execute("SELECT embedding::text FROM corpus.chunks WHERE valid_to IS NOT NULL LIMIT 1").fetchone()
    if not vec:
        pytest.skip("no dated chunk in the test corpus")
    v = [float(x) for x in vec[0].strip("[]").split(",")]
    later = P.nearest(v, datetime.date(2030, 1, 1), "E", 5, url)
    assert all(r["valid_to"] is None or r["valid_to"] >= datetime.date(2030, 1, 1) for r in later)
    assert later and all(r["source_id"] for r in later)
