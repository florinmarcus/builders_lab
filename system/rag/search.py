"""Keyword search over the corpus chunks (SQLite full-text search). No model, no server needed.

    python -m system.rag.search --build                 # index every corpus/chunks/*/*.jsonl
    python -m system.rag.search "do I need a licence to remove asbestos insulating board"

The index is a single SQLite file (corpus/search.sqlite, not in git; RAG_INDEX overrides the path). search()
follows the contract in system/rag/README.md and adds legal_weight, section_id and chunk_id to each passage.
It is not yet wired into the live server (rag/__init__.py does not export it): whether to use keyword search,
vectors or both is decided by evals (parking lot).

How it ranks: SQLite FTS5 with the Porter stemmer on the breadcrumb + text, plus a separate column of codes
("B1", "2.5", "7(2)", "FD30") so they match whole; bm25 with codes weighted highest. Filters: the passage must
apply on as_of_date (today if not given) and to the country (England by default).
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
    n = 0
    for path in sorted((CORPUS_DIR / "chunks").glob("*/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            c = json.loads(line)
            meta = {k: c.get(k) for k in ("source_id", "source_title", "legal_weight", "kind", "version_id",
                                          "edition_date", "valid_from", "valid_to", "applies_to", "section_id",
                                          "section_number", "section_title", "heading_path", "printed_page",
                                          "url", "chunk_type", "text")}
            title = " ".join(p for p in c.get("heading_path") or [] if p)
            db.execute("INSERT INTO chunks VALUES (?,?,?,?,?)",
                       (title, c["text"], codes(c["embed_text"]), c["id"], json.dumps(meta, ensure_ascii=False)))
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


def search(question: str, as_of_date: datetime.date | None = None, country: str = "E", limit: int = 8) -> list[dict]:
    """Best passages first, as the server contract asks (system/rag/README.md)."""
    path = index_path()
    if not path.exists():
        raise FileNotFoundError(f"search index not built: {path} (run python -m system.rag.search --build)")
    q = _query(question)
    if not q:
        return []
    as_of = (as_of_date or datetime.date.today()).isoformat()
    db = sqlite3.connect(path)
    rows = db.execute("SELECT chunk_id, meta, bm25(chunks, 2.0, 1.0, 5.0) AS r FROM chunks WHERE chunks MATCH ? "
                      "ORDER BY r LIMIT 200", (q,)).fetchall()
    db.close()
    out, seen = [], set()
    for cid, meta_s, rank in rows:
        m = json.loads(meta_s)
        if not _applies(m, as_of, country):
            continue
        key = (m["source_id"], m["section_id"])
        if key in seen:  # one passage per section (a table and its rows count once)
            continue
        seen.add(key)
        path = [x for x in (m.get("heading_path") or []) if x]
        section = path[-1] if path else (m.get("section_title") or m["section_id"])
        if re.fullmatch(r"\(\w{1,4}\)|Text|Note", section) and len(path) > 1:  # "(3)" alone says nothing
            section = f"{path[-2]} {section}" if section.startswith("(") else path[-2]
        note = None
        if m.get("valid_to"):
            note = f"Text valid until {m['valid_to']}"
        elif m.get("valid_from") and m["valid_from"] > (m.get("edition_date") or ""):
            note = f"Text valid from {m['valid_from']}"
        out.append({"text": m["text"], "source": m.get("source_title") or m["source_id"], "section": section,
                    "edition_date": m.get("edition_date") or m.get("valid_from") or "", "url": m.get("url") or "",
                    "score": round(-rank, 3), "edition_note": note, "legal_weight": m.get("legal_weight"),
                    "printed_page": m.get("printed_page"), "section_id": m["section_id"], "chunk_id": cid})
        if len(out) >= limit:
            break
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", nargs="?")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--as-of")
    a = ap.parse_args(argv)
    if a.build:
        print(f"{build()} chunks -> {index_path()}")
    if a.question:
        when = datetime.date.fromisoformat(a.as_of) if a.as_of else None
        for p in search(a.question, when, limit=5):
            print(f"{p['score']:7.2f}  {p['source'][:40]} | {p['section'][:60]} | {p['legal_weight']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
