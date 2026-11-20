"""Hybrid search over the corpus chunks (ADR 0013): BM25 keywords and Titan V2 vectors, top 50 each, merged with
reciprocal rank fusion, then re-ranked in Frankfurt to the best few. Keyword-only works with no AWS access.

    python -m system.rag.search --build                 # index every corpus/chunks/*/*.jsonl
    python -m system.rag.search "do I need a licence to remove asbestos insulating board"

The index is a single SQLite file (corpus/search.sqlite, not in git; RAG_INDEX overrides the path). search()
follows the contract in system/rag/README.md and adds legal_weight, section_id and chunk_id to each passage.
It is not yet wired into the live server (rag/__init__.py does not export it): whether to use keyword search,
vectors or both is decided by evals (parking lot).

Keywords: SQLite FTS5 with the Porter stemmer on the breadcrumb + text, plus a separate column of codes
("B1", "2.5", "7(2)", "FD30") so they match whole; bm25 with codes weighted highest. Vectors: the chunk vectors
from system/rag/embed.py (corpus/vectors/), exact cosine search in memory (3,000 chunks need no vector index).
Filters on both lists: the passage must apply on as_of_date (today if not given) and to the country (England by
default). One passage per section.

Settings (environment): RAG_MODE (hybrid, vector or keyword; default hybrid, keyword if no vectors are built),
RAG_RERANK (1 or 0, default 1), RAG_RERANK_MODEL (default amazon.rerank-v1:0), RAG_RERANK_REGION (default
eu-central-1: no Bedrock re-rank model in London, checked 20 Nov 2026), RAG_TOP_K (candidates per list, default 50).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

from system.rag.corpus import CORPUS_DIR

ROOT = CORPUS_DIR.parent
CODE_RE = re.compile(r"\b(?:[A-Z]{1,2}\d+(?:\.\d+)*(?:\(\d+\))?|\d+\.\d+(?:\.\d+)*[a-z]?|\d+[A-Z]?\(\d+\)|FD\s?\d+S?)\b")
STOP = set("""a an the and or of to in on for with by is are be can do does i we my our you your it this that what
which who how when where should must need needs have has at from as if any all there their them they me am was
were will would could may might shall not no yes about into than then so such""".split())


def index_path() -> Path:
    return Path(os.environ.get("RAG_INDEX") or CORPUS_DIR / "search.sqlite")


def codes(text: str) -> str:
    return " ".join(c.replace(" ", "").replace(".", "_").replace("(", "_").replace(")", "")
                    for c in CODE_RE.findall(text))


def build(out: Path | None = None) -> int:
    """(Re)build the index from every chunk file. Returns the number of chunks."""
    out = out or index_path()
    if out.exists():
        out.unlink()
    db = sqlite3.connect(out)
    db.execute("CREATE VIRTUAL TABLE chunks USING fts5(title, body, codes, chunk_id UNINDEXED, meta UNINDEXED, "
               "tokenize='porter unicode61')")
    db.execute("CREATE TABLE meta (chunk_id TEXT PRIMARY KEY, meta TEXT)")
    n = 0
    for path in sorted((CORPUS_DIR / "chunks").glob("*/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            c = json.loads(line)
            meta = {k: c.get(k) for k in ("source_id", "source_title", "legal_weight", "kind", "version_id",
                                          "edition_date", "valid_from", "valid_to", "applies_to", "section_id",
                                          "section_number", "section_title", "heading_path", "printed_page",
                                          "url", "chunk_type", "text", "embed_text")}
            title = " ".join(p for p in c.get("heading_path") or [] if p)
            db.execute("INSERT INTO chunks VALUES (?,?,?,?,?)",
                       (title, c["text"], codes(c["embed_text"]), c["id"], json.dumps(meta, ensure_ascii=False)))
            db.execute("INSERT INTO meta VALUES (?,?)", (c["id"], json.dumps(meta, ensure_ascii=False)))
            n += 1
    db.commit()
    db.close()
    return n


def _query(question: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z]{2,}", question) if w.lower() not in STOP]
    parts = [f'"{w}"' for w in dict.fromkeys(w.lower() for w in words)]
    parts += [f'codes:"{c}"' for c in codes(question).split()]
    return " OR ".join(parts)


def _applies(meta: dict, as_of: str, country: str) -> bool:
    if meta.get("valid_from") and meta["valid_from"] > as_of:
        return False
    if meta.get("valid_to") and meta["valid_to"] < as_of:
        return False
    a = (meta.get("applies_to") or "").replace(".", "")
    return not a or country in a.split("+")


def settings() -> dict:
    return {"mode": os.environ.get("RAG_MODE", "hybrid"), "rerank": os.environ.get("RAG_RERANK", "1") == "1",
            "rerank_model": os.environ.get("RAG_RERANK_MODEL", "amazon.rerank-v1:0"),
            "rerank_region": os.environ.get("RAG_RERANK_REGION", "eu-central-1"),
            "top_k": int(os.environ.get("RAG_TOP_K", "50"))}


def keyword_candidates(db, question: str, as_of: str, country: str, n: int) -> list[tuple[str, dict]]:
    q = _query(question)
    if not q:
        return []
    rows = db.execute("SELECT chunk_id, meta FROM chunks WHERE chunks MATCH ? "
                      "ORDER BY bm25(chunks, 2.0, 1.0, 5.0) LIMIT ?", (q, n * 4)).fetchall()
    out = [(cid, json.loads(m)) for cid, m in rows]
    return [x for x in out if _applies(x[1], as_of, country)][:n]


_vectors = None


def load_vectors():
    """All chunk vectors and their ids, from corpus/vectors/ (None if not built)."""
    global _vectors
    if _vectors is None:
        import numpy as np

        ids, mats = [], []
        for npy in sorted((CORPUS_DIR / "vectors").glob("*/*.npy")):
            ids += [p["id"] for p in json.loads(npy.with_suffix(".ids.json").read_text(encoding="utf-8"))]
            mats.append(np.load(npy))
        _vectors = (ids, np.vstack(mats)) if mats else (None, None)
    return _vectors


def vector_candidates(db, question: str, as_of: str, country: str, n: int, embed=None) -> list[tuple[str, dict]]:
    import numpy as np

    ids, mat = load_vectors()
    if ids is None:
        return []
    if embed is None:
        from system.rag.embed import embed_text as embed
    q = np.asarray(embed(question)[0], dtype=np.float32)
    order = np.argsort(-(mat @ q))
    out = []
    for i in order:
        row = db.execute("SELECT meta FROM meta WHERE chunk_id = ?", (ids[i],)).fetchone()
        if row is None:
            continue
        m = json.loads(row[0])
        if _applies(m, as_of, country):
            out.append((ids[i], m))
            if len(out) >= n:
                break
    return out


def rrf(*lists: list[tuple[str, dict]], k: int = 60) -> list[tuple[str, dict, float]]:
    """Reciprocal rank fusion: each list adds 1 / (k + rank) to a chunk's score. k is fixed (ADR 0013)."""
    score: dict[str, float] = {}
    meta: dict[str, dict] = {}
    for lst in lists:
        for rank, (cid, m) in enumerate(lst, start=1):
            score[cid] = score.get(cid, 0.0) + 1.0 / (k + rank)
            meta[cid] = m
    return sorted(((c, meta[c], s) for c, s in score.items()), key=lambda x: -x[2])


def rerank(question: str, texts: list[str], n: int) -> list[tuple[int, float]]:
    """Order texts by how well they answer the question with the Bedrock Rerank API. Returns (index, score)."""
    import boto3

    cfg = settings()
    client = boto3.client("bedrock-agent-runtime", region_name=cfg["rerank_region"])
    arn = f"arn:aws:bedrock:{cfg['rerank_region']}::foundation-model/{cfg['rerank_model']}"
    r = client.rerank(
        queries=[{"type": "TEXT", "textQuery": {"text": question}}],
        sources=[{"type": "INLINE", "inlineDocumentSource": {"type": "TEXT", "textDocument": {"text": t[:8000]}}}
                 for t in texts],
        rerankingConfiguration={"type": "BEDROCK_RERANKING_MODEL", "bedrockRerankingConfiguration": {
            "numberOfResults": min(n, len(texts)), "modelConfiguration": {"modelArn": arn}}})
    return [(x["index"], x["relevanceScore"]) for x in r["results"]]


def _passage(cid: str, m: dict, score: float) -> dict:
    path = [x for x in (m.get("heading_path") or []) if x]
    section = path[-1] if path else (m.get("section_title") or m["section_id"])
    if re.fullmatch(r"\(\w{1,4}\)|Text|Note", section) and len(path) > 1:  # "(3)" alone says nothing
        section = f"{path[-2]} {section}" if section.startswith("(") else path[-2]
    note = None
    if m.get("valid_to"):
        note = f"Text valid until {m['valid_to']}"
    elif m.get("valid_from") and m["valid_from"] > (m.get("edition_date") or ""):
        note = f"Text valid from {m['valid_from']}"
    return {"text": m["text"], "source": m.get("source_title") or m["source_id"], "section": section,
            "edition_date": m.get("edition_date") or m.get("valid_from") or "", "url": m.get("url") or "",
            "score": round(score, 4), "edition_note": note, "legal_weight": m.get("legal_weight"),
            "printed_page": m.get("printed_page"), "section_id": m["section_id"], "chunk_id": cid}


def _one_per_section(items):
    seen, out = set(), []
    for it in items:
        key = (it[1]["source_id"], it[1]["section_id"])
        if key not in seen:  # a table and its rows, or the parts of a split paragraph, count once
            seen.add(key)
            out.append(it)
    return out


def search(question: str, as_of_date: datetime.date | None = None, country: str = "E", limit: int = 5,
           mode: str | None = None, use_rerank: bool | None = None, embed=None, rerank_fn=None) -> list[dict]:
    """Best passages first, as the server contract asks (system/rag/README.md)."""
    path = index_path()
    if not path.exists():
        raise FileNotFoundError(f"search index not built: {path} (run python -m system.rag.search --build)")
    cfg = settings()
    mode = mode or cfg["mode"]
    if mode != "keyword" and load_vectors()[0] is None:
        mode = "keyword"  # no vectors built yet
    use_rerank = cfg["rerank"] if use_rerank is None else use_rerank
    as_of = (as_of_date or datetime.date.today()).isoformat()
    n = cfg["top_k"]
    db = sqlite3.connect(path)
    try:
        kw = keyword_candidates(db, question, as_of, country, n) if mode in ("keyword", "hybrid") else []
        vec = vector_candidates(db, question, as_of, country, n, embed) if mode in ("vector", "hybrid") else []
    finally:
        db.close()
    merged = _one_per_section(rrf(kw, vec))[:n]
    if not merged:
        return []
    if use_rerank:
        order = (rerank_fn or rerank)(question, [m.get("embed_text") or m["text"] for _, m, _ in merged], limit)
        return [_passage(merged[i][0], merged[i][1], s) for i, s in order][:limit]
    return [_passage(c, m, s) for c, m, s in merged[:limit]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", nargs="?")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--as-of")
    ap.add_argument("--mode", choices=["hybrid", "vector", "keyword"])
    ap.add_argument("--no-rerank", action="store_true")
    a = ap.parse_args(argv)
    if a.build:
        print(f"{build()} chunks -> {index_path()}")
    if a.question:
        when = datetime.date.fromisoformat(a.as_of) if a.as_of else None
        for p in search(a.question, when, limit=5, mode=a.mode, use_rerank=False if a.no_rerank else None):
            print(f"{p['score']:7.2f}  {p['source'][:40]} | {p['section'][:60]} | {p['legal_weight']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
