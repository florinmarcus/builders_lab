"""Load the corpus chunks and vectors into Postgres with pgvector (ADR 0013, deploy/rds/).

    python -m system.rag.load                  # owner URL from Parameter Store (/builders-lab/admin/corpus_owner_url)
    CORPUS_OWNER_URL=postgresql://... python -m system.rag.load

Runs as builders_corpus_owner. Reads corpus/chunks/*/*.jsonl and corpus/vectors/*/*.npy (made by system.rag.chunk
and system.rag.embed) and replaces the contents of schema "corpus" in one transaction, so readers see either
the old corpus or the new one, never half. The server reads these tables as builders_corpus_reader.

Tables (schema corpus):
- chunks: one row per chunk: filter fields, text, embed_text, the vector (vector(1024)), a tsvector of the
  breadcrumb + text ("english" stemming), a tsvector of codes ("simple": B1, 7_2, FD30 kept whole), and the
  document length in words, for BM25.
- lexemes: document frequency of every word and code (for BM25's IDF).
- stats: number of chunks, average length, when and from what the corpus was loaded.
Postgres's own ranking (ts_rank) is not BM25; search computes BM25 from these tables (ADR 0013).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from system.rag.corpus import CORPUS_DIR
from system.rag.localsearch import codes

ROOT = CORPUS_DIR.parent
SCHEMA_VERSION = 1
OWNER_PARAM = "/builders-lab/admin/corpus_owner_url"

READER_ROLE = "builders_corpus_reader"
SCHEMA_RE = re.compile(r"^[a-z_][a-z0-9_]{0,40}$")

DDL = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS corpus.chunks (
    id            text PRIMARY KEY,
    source_id     text NOT NULL,
    source_title  text,
    kind          text,
    legal_weight  text,
    version_id    text NOT NULL,
    edition_date  date,
    valid_from    date,
    valid_to      date,
    applies_to    text,
    section_id    text NOT NULL,
    section_title text,
    heading_path  jsonb,
    printed_page  text,
    url           text,
    chunk_type    text,
    text          text NOT NULL,
    embed_text    text NOT NULL,
    meta          jsonb,
    embedding     vector(1024),
    tsv           tsvector,
    codes_tsv     tsvector,
    doc_len       integer
);
CREATE INDEX IF NOT EXISTS chunks_tsv ON corpus.chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS chunks_codes ON corpus.chunks USING gin (codes_tsv);
CREATE INDEX IF NOT EXISTS chunks_dates ON corpus.chunks (valid_from, valid_to);
CREATE TABLE IF NOT EXISTS corpus.lexemes (lexeme text, field text, df integer, PRIMARY KEY (lexeme, field));
CREATE TABLE IF NOT EXISTS corpus.stats (
    schema_version integer, chunk_count integer, avg_len double precision, avg_codes double precision,
    loaded_at timestamptz DEFAULT now(), sources jsonb
);
"""

COLUMNS = ("id", "source_id", "source_title", "kind", "legal_weight", "version_id", "edition_date", "valid_from",
           "valid_to", "applies_to", "section_id", "section_title", "heading_path", "printed_page", "url",
           "chunk_type", "text", "embed_text", "meta")
TOP_LEVEL = set(COLUMNS) - {"meta"}


def rows(chunks_dir: Path | None = None, vectors_dir: Path | None = None):
    """Each chunk as a row (dict), with its vector as pgvector text ("[0.1,0.2,...]")."""
    import numpy as np

    chunks_dir = chunks_dir or CORPUS_DIR / "chunks"
    vectors_dir = vectors_dir or CORPUS_DIR / "vectors"
    for f in sorted(chunks_dir.glob("*/*.jsonl")):
        chunks = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        rel = f.relative_to(chunks_dir)
        npy = (vectors_dir / rel.parent / rel.stem).with_suffix(".npy")
        ids_path = npy.with_suffix(".ids.json")
        if not npy.exists():
            raise FileNotFoundError(f"no vectors for {rel}: run python -m system.rag.embed")
        ids = [p["id"] for p in json.loads(ids_path.read_text(encoding="utf-8"))]
        mat = np.load(npy)
        if ids != [c["id"] for c in chunks]:
            raise ValueError(f"vectors out of date for {rel}: run python -m system.rag.embed")
        for c, v in zip(chunks, mat):
            r = {k: c.get(k) for k in TOP_LEVEL}
            r["heading_path"] = json.dumps(c.get("heading_path") or [], ensure_ascii=False)
            r["meta"] = json.dumps({k: v2 for k, v2 in c.items() if k not in TOP_LEVEL and k != "id"},
                                   ensure_ascii=False)
            r["embedding"] = "[" + ",".join(f"{x:.7g}" for x in v.tolist()) + "]"
            r["title"] = " ".join(p for p in c.get("heading_path") or [] if p)
            r["codes"] = codes(c["embed_text"])
            yield r


def owner_url() -> str:
    url = os.environ.get("CORPUS_OWNER_URL")
    if url:
        return url
    import boto3

    return boto3.client("ssm", region_name="eu-west-2").get_parameter(
        Name=OWNER_PARAM, WithDecryption=True)["Parameter"]["Value"]


def check_schema(schema: str) -> str:
    """Only plain lower-case names (corpus, corpus_next, corpus_prev): the name goes into SQL."""
    if not SCHEMA_RE.match(schema or ""):
        raise ValueError(f"bad schema name: {schema!r}")
    return schema


def ddl(schema: str = "corpus") -> str:
    s = check_schema(schema)
    return f"CREATE SCHEMA IF NOT EXISTS {s};" + "\n" + DDL.replace("corpus.", f"{s}.")


def grants(schema: str = "corpus") -> str:
    """Explicit grants: default privileges belong to a schema and do not follow a rename (promote.py)."""
    s = check_schema(schema)
    return (f"GRANT USAGE ON SCHEMA {s} TO {READER_ROLE};" + "\n"
            + f"GRANT SELECT ON ALL TABLES IN SCHEMA {s} TO {READER_ROLE};")


def load(url: str, chunks_dir: Path | None = None, vectors_dir: Path | None = None, schema: str = "corpus") -> dict:
    """Replace the corpus in one schema (default: the live one) in one transaction. Returns counts."""
    import psycopg

    s = check_schema(schema)
    data = list(rows(chunks_dir, vectors_dir))
    with psycopg.connect(url) as conn:
        with conn.transaction():
            conn.execute(ddl(s))
            conn.execute(f"TRUNCATE {s}.chunks, {s}.lexemes, {s}.stats")
            cols = ", ".join(COLUMNS)
            params = ", ".join(f"%({c})s" for c in COLUMNS)
            with conn.cursor() as cur:
                cur.executemany(
                    f"INSERT INTO {s}.chunks ({cols}, embedding, tsv, codes_tsv) VALUES ({params}, "
                    "%(embedding)s::vector, to_tsvector('english', %(title)s || ' ' || %(text)s), "
                    "to_tsvector('simple', %(codes)s))", data)
            # Document length for BM25: every word occurrence, not just distinct words.
            conn.execute(f"UPDATE {s}.chunks c SET doc_len = (SELECT coalesce(sum(array_length(u.positions, 1)), 0) "
                         "FROM unnest(c.tsv) u)")
            conn.execute(f"INSERT INTO {s}.lexemes SELECT word, 'text', ndoc FROM ts_stat('SELECT tsv FROM {s}.chunks')")
            conn.execute(f"INSERT INTO {s}.lexemes SELECT word, 'codes', ndoc FROM ts_stat("
                         f"'SELECT codes_tsv FROM {s}.chunks') ON CONFLICT DO NOTHING")
            sources = sorted({r["source_id"] for r in data})
            conn.execute(f"INSERT INTO {s}.stats (schema_version, chunk_count, avg_len, avg_codes, sources) "
                         f"SELECT %s, count(*), avg(doc_len), avg(length(codes_tsv)), %s FROM {s}.chunks",
                         (SCHEMA_VERSION, json.dumps(sources)))
            conn.execute(grants(s))
            n, avg = conn.execute(f"SELECT chunk_count, avg_len FROM {s}.stats").fetchone()
    return {"chunks": n, "avg_len": round(avg or 0, 1), "sources": len(sources)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schema", default="corpus", help="target schema: corpus (live) or corpus_next (staging)")
    a = ap.parse_args(argv)
    r = load(owner_url(), schema=a.schema)
    print(f"loaded {r['chunks']} chunks from {r['sources']} sources (average {r['avg_len']} words) into schema {a.schema}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
