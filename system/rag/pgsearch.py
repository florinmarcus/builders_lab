"""Regulations search on the server: pgvector top 50, re-rank to the best few, relevance floor (ADR 0013).

Used by the MCP server through rag.search (system/rag/__init__.py) when CORPUS_READER_URL is set. Connects
only as builders_corpus_reader (read-only, deploy/rds/). Self-contained on purpose: inside the container the
package is imported as "rag", so this file uses no "system.rag" imports.

Steps: embed the question (Titan V2, London) -> the 50 nearest chunks by cosine distance that apply on the
date and to the country -> one per section -> Amazon Rerank (Frankfurt) -> drop passages below the relevance
floor -> the best few. Keyword (BM25) search is not used yet (parking lot); the tables already hold it.

Settings (environment): CORPUS_READER_URL, RAG_EMBED_REGION (eu-west-2), RAG_EMBED_MODEL
(amazon.titan-embed-text-v2:0), RAG_RERANK (1 or 0), RAG_RERANK_REGION (eu-central-1), RAG_RERANK_MODEL
(amazon.rerank-v1:0), RAG_TOP_K (50), RAG_MIN_SCORE (re-rank score below which a passage is dropped, 0.05).
"""

from __future__ import annotations

import datetime
import json
import os
import re

_clients: dict = {}


def cfg() -> dict:
    return {
        "url": os.environ.get("CORPUS_READER_URL", ""),
        "embed_region": os.environ.get("RAG_EMBED_REGION", "eu-west-2"),
        "embed_model": os.environ.get("RAG_EMBED_MODEL", "amazon.titan-embed-text-v2:0"),
        "rerank": os.environ.get("RAG_RERANK", "1") == "1",
        "rerank_region": os.environ.get("RAG_RERANK_REGION", "eu-central-1"),
        "rerank_model": os.environ.get("RAG_RERANK_MODEL", "amazon.rerank-v1:0"),
        "top_k": int(os.environ.get("RAG_TOP_K", "50")),
        "min_score": float(os.environ.get("RAG_MIN_SCORE", "0.05")),
        "schema": _schema(os.environ.get("RAG_SCHEMA", "corpus")),
    }


def _schema(name: str) -> str:
    """Which schema to read: corpus (live) or corpus_next (staging, for evals). The name goes into SQL."""
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,40}", name or ""):
        raise ValueError(f"bad RAG_SCHEMA: {name!r}")
    return name


class SearchError(RuntimeError):
    """A failure the server may retry (throttling, timeouts, 5xx), per the contract in README.md."""

    retryable = True


def _client(service: str, region: str):
    key = (service, region)
    if key not in _clients:
        import boto3
        from botocore.config import Config

        _clients[key] = boto3.client(service, region_name=region,
                                     config=Config(retries={"max_attempts": 4, "mode": "adaptive"},
                                                   connect_timeout=3, read_timeout=10))
    return _clients[key]


def embed_question(question: str) -> list[float]:
    c = cfg()
    body = json.dumps({"inputText": question[:8000], "dimensions": 1024, "normalize": True})
    r = _client("bedrock-runtime", c["embed_region"]).invoke_model(modelId=c["embed_model"], body=body)
    return json.loads(r["body"].read())["embedding"]


def rerank(question: str, texts: list[str], n: int) -> list[tuple[int, float]]:
    c = cfg()
    arn = f"arn:aws:bedrock:{c['rerank_region']}::foundation-model/{c['rerank_model']}"
    r = _client("bedrock-agent-runtime", c["rerank_region"]).rerank(
        queries=[{"type": "TEXT", "textQuery": {"text": question}}],
        sources=[{"type": "INLINE", "inlineDocumentSource": {"type": "TEXT", "textDocument": {"text": t[:8000]}}}
                 for t in texts],
        rerankingConfiguration={"type": "BEDROCK_RERANKING_MODEL", "bedrockRerankingConfiguration": {
            "numberOfResults": min(n, len(texts)), "modelConfiguration": {"modelArn": arn}}})
    return [(x["index"], x["relevanceScore"]) for x in r["results"]]


NEAREST = """
SELECT id, source_id, source_title, legal_weight, edition_date, valid_from, valid_to, section_id,
       section_title, heading_path, printed_page, url, text, embed_text, embedding <=> %(v)s::vector AS distance
FROM {schema}.chunks
WHERE (valid_from IS NULL OR valid_from <= %(d)s) AND (valid_to IS NULL OR valid_to >= %(d)s)
  AND (applies_to IS NULL OR %(c)s = ANY (string_to_array(replace(applies_to, '.', ''), '+')))
ORDER BY embedding <=> %(v)s::vector
LIMIT %(n)s
"""


def nearest_sql(schema: str) -> str:
    return NEAREST.replace("{schema}", _schema(schema))


def nearest(vector: list[float], as_of: datetime.date, country: str, n: int, url: str | None = None,
            schema: str | None = None) -> list[dict]:
    import psycopg
    from psycopg.rows import dict_row

    c = cfg()
    v = "[" + ",".join(f"{x:.7g}" for x in vector) + "]"
    with psycopg.connect(url or c["url"], connect_timeout=5, row_factory=dict_row) as conn:
        return conn.execute(nearest_sql(schema or c["schema"]), {"v": v, "d": as_of, "c": country, "n": n}).fetchall()


def one_per_section(rows: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        key = (r["source_id"], r["section_id"])
        if key not in seen:  # a table and its rows, or the parts of a split paragraph, count once
            seen.add(key)
            out.append(r)
    return out


def passage(r: dict, score: float) -> dict:
    path = [x for x in (r.get("heading_path") or []) if x]
    section = path[-1] if path else (r.get("section_title") or r["section_id"])
    if re.fullmatch(r"\(\w{1,4}\)|Text|Note", section) and len(path) > 1:  # "(3)" alone says nothing
        section = f"{path[-2]} {section}" if section.startswith("(") else path[-2]
    iso = lambda d: d.isoformat() if hasattr(d, "isoformat") else (d or "")
    note = None
    if r.get("valid_to"):
        note = f"Text valid until {iso(r['valid_to'])}"
    elif r.get("valid_from") and r.get("edition_date") and r["valid_from"] > r["edition_date"]:
        note = f"Text valid from {iso(r['valid_from'])}"
    return {"text": r["text"], "source": r.get("source_title") or r["source_id"], "section": section,
            "edition_date": iso(r.get("edition_date") or r.get("valid_from")), "url": r.get("url") or "",
            "score": round(float(score), 4), "edition_note": note, "legal_weight": r.get("legal_weight"),
            "printed_page": r.get("printed_page"), "section_id": r["section_id"], "chunk_id": r["id"]}


def candidates(question: str, as_of_date: datetime.date | None = None, country: str = "E", embed=None,
               url: str | None = None, n: int | None = None) -> list[dict]:
    """The first stage: nearest chunks, one per section, in distance order (what search re-ranks; evals
    score Recall@50 on this)."""
    c = cfg()
    vec = (embed or embed_question)(question)
    return one_per_section(nearest(vec, as_of_date or datetime.date.today(), country, n or c["top_k"], url))


def search(question: str, as_of_date: datetime.date | None = None, country: str = "E", limit: int = 5,
           embed=None, rerank_fn=None, url: str | None = None) -> list[dict]:
    """Best passages first (contract: system/rag/README.md). [] when nothing passes the relevance floor."""
    c = cfg()
    if not question.strip():
        return []
    as_of = as_of_date or datetime.date.today()
    try:
        rows = candidates(question, as_of, country, embed, url)
        if not rows:
            return []
        if not c["rerank"]:
            return [passage(r, 1 - float(r["distance"])) for r in rows[:limit]]
        order = (rerank_fn or rerank)(question, [r["embed_text"] for r in rows], limit)
    except Exception as e:  # AWS or database trouble: let the server retry, then fall back
        if type(e).__name__ in ("ProgrammingError", "UndefinedTable", "InsufficientPrivilege"):
            raise
        raise SearchError(f"regulations search failed: {type(e).__name__}") from e
    return [passage(rows[i], s) for i, s in order if s >= c["min_score"]][:limit]
