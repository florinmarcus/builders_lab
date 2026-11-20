"""Tests for the corpus loader (system/rag/load.py). The database test needs Postgres with pgvector and the
corpus roles (deploy/rds/corpus-setup.sql): set CORPUS_TEST_OWNER_URL and CORPUS_TEST_READER_URL, else it skips.
CI's Postgres has no pgvector, so it skips there."""

import json
import os

import pytest

from system.rag import load as L

np = pytest.importorskip("numpy")


def write_corpus(tmp_path, n=3):
    chunks_dir, vectors_dir = tmp_path / "chunks" / "demo", tmp_path / "vectors" / "demo"
    chunks_dir.mkdir(parents=True)
    vectors_dir.mkdir(parents=True)
    chunks = [{"id": f"demo:v1:para-{i}", "source_id": "demo", "version_id": "v1", "section_id": f"para-{i}",
               "text": f"Fire doors FD30 rule {i}.", "embed_text": f"Doc › Para {i}\nFire doors FD30 rule {i}.",
               "heading_path": ["Doc", f"Para {i}"], "valid_from": "2026-01-01", "valid_to": None,
               "applies_to": "E", "legal_weight": "guidance", "references": [{"words": "Table 1"}]}
              for i in range(n)]
    (chunks_dir / "v1.jsonl").write_text("".join(json.dumps(c) + "\n" for c in chunks))
    np.save(vectors_dir / "v1.npy", np.eye(n, 1024, dtype=np.float32))
    (vectors_dir / "v1.ids.json").write_text(json.dumps([{"id": c["id"], "fp": "x"} for c in chunks]))
    return tmp_path / "chunks", tmp_path / "vectors"


def test_rows_carry_filters_vector_codes_and_the_rest_in_meta(tmp_path):
    cdir, vdir = write_corpus(tmp_path)
    r = list(L.rows(cdir, vdir))
    assert len(r) == 3 and r[0]["id"] == "demo:v1:para-0" and r[0]["applies_to"] == "E"
    assert r[0]["embedding"].startswith("[1,0,0") and r[0]["embedding"].count(",") == 1023
    assert r[0]["codes"] == "FD30" and r[0]["title"] == "Doc Para 0"
    assert json.loads(r[0]["meta"])["references"] == [{"words": "Table 1"}]


def test_vectors_out_of_step_with_chunks_are_refused(tmp_path):
    cdir, vdir = write_corpus(tmp_path)
    (vdir / "demo" / "v1.ids.json").write_text(json.dumps([{"id": "other", "fp": "x"}] * 3))
    with pytest.raises(ValueError, match="run python -m system.rag.embed"):
        list(L.rows(cdir, vdir))


@pytest.mark.skipif(not os.environ.get("CORPUS_TEST_OWNER_URL"), reason="needs Postgres with pgvector")
def test_load_replaces_the_corpus_and_the_reader_can_only_read(tmp_path):
    psycopg = pytest.importorskip("psycopg")
    cdir, vdir = write_corpus(tmp_path)
    r = L.load(os.environ["CORPUS_TEST_OWNER_URL"], cdir, vdir)
    assert r == {"chunks": 3, "avg_len": r["avg_len"], "sources": 1} and r["avg_len"] > 0
    with psycopg.connect(os.environ["CORPUS_TEST_READER_URL"]) as c:
        assert c.execute("SELECT count(*) FROM corpus.chunks").fetchone()[0] == 3
        assert c.execute("SELECT df FROM corpus.lexemes WHERE lexeme = 'fd30' AND field = 'codes'").fetchone()[0] == 3
        assert c.execute("SELECT vector_dims(embedding) FROM corpus.chunks LIMIT 1").fetchone()[0] == 1024
    # Even with read-only switched off by the reader itself, it has no right to write.
    with psycopg.connect(os.environ["CORPUS_TEST_READER_URL"], autocommit=True) as c:
        c.execute("SET default_transaction_read_only = off")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("INSERT INTO corpus.stats (schema_version) VALUES (9)")
