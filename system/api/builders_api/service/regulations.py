"""search_regulations: the corpus session's `rag.search` if present, else a small fallback.

Contract (system/rag/README.md): rag.search(question, as_of_date=None) -> list of passages,
each with text, source, section, edition_date (YYYY-MM-DD), url, and optional score.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys
from functools import cache
from pathlib import Path
from typing import Any

from builders_api.config import rag_dir
from builders_api.db import connection
from builders_api.errors import UpstreamError, ValidationError
from builders_api.retry import with_retries

log = logging.getLogger(__name__)
FALLBACK_FILE = Path(__file__).resolve().parents[1] / "regulations_fallback" / "passages.json"
REQUIRED = ("text", "source", "section", "edition_date", "url")


@cache
def _corpus_search():
    """Return rag.search, or None if the corpus module is not there yet."""
    parent = str(rag_dir())
    if parent not in sys.path:
        sys.path.append(parent)
    try:
        import rag  # type: ignore[import-not-found]
    except ImportError:
        return None
    fn = getattr(rag, "search", None)
    return fn if callable(fn) else None


@cache
def _fallback() -> list[dict]:
    return json.loads(FALLBACK_FILE.read_text())["passages"]


MIN_MATCH_SHARE = 0.5  # a passage must contain at least half of the question's meaningful words


def _search_fallback(question: str, as_of: dt.date | None, limit: int) -> list[dict]:
    """Keyword search over the small fallback set. Returns [] rather than unrelated passages:
    a passage counts only if it holds at least half of the question's words (stemmed, stop words dropped)."""
    passages = [p for p in _fallback() if not as_of or dt.date.fromisoformat(p["edition_date"]) <= as_of]
    if not passages:
        return []
    with connection() as conn:
        q = conn.execute("select plainto_tsquery('english', %s)::text as q", (question,)).fetchone()["q"]
        if not q:
            return []
        lexemes = sorted({t.strip().strip("'") for t in q.split("&") if t.strip()})
        need = max(1, -(-len(lexemes) * MIN_MATCH_SHARE // 1)) if len(lexemes) > 1 else 1
        rows = conn.execute(
            """select p->>'id' as id,
                      ts_rank(doc, to_tsquery('english', %(q)s)) as score,
                      (select count(*) from unnest(%(lex)s::text[]) l where doc @@ to_tsquery('english', quote_literal(l))) as hits
               from jsonb_array_elements(%(p)s::jsonb) p,
                    lateral to_tsvector('english', (p->>'section') || ' ' || (p->>'keywords') || ' ' || (p->>'text')) doc
               order by score desc""",
            {"q": q.replace(" & ", " | "), "lex": lexemes, "p": json.dumps(passages)},
        ).fetchall()
    by_id = {p["id"]: p for p in passages}
    good = [r for r in rows if r["hits"] >= need and r["score"] > 0]
    return [{**by_id[r["id"]], "score": round(float(r["score"]), 4), "matched_words": f"{r['hits']}/{len(lexemes)}"}
            for r in good[:limit]]


def search_regulations(question: str, as_of_date: str | None = None, limit: int = 5) -> dict[str, Any]:
    question = (question or "").strip()
    if not question:
        raise ValidationError("Ask a question to search the regulations.")
    as_of = None
    if as_of_date:
        try:
            as_of = dt.date.fromisoformat(as_of_date)
        except ValueError:
            raise ValidationError("as_of_date must look like 2026-11-21.") from None
    corpus = _corpus_search()
    if corpus is not None:
        try:
            raw = with_retries(lambda: corpus(question, as_of_date=as_of))
        except Exception as exc:  # noqa: BLE001
            log.exception("corpus search failed")
            raise UpstreamError(
                "The regulations search is not answering right now.", retryable=bool(getattr(exc, "retryable", False))
            ) from None
        passages = [p for p in raw if all(p.get(k) for k in REQUIRED)][:limit]
        dropped = len(raw) - len(passages) if len(raw) <= limit else 0
        if dropped:
            log.warning("corpus returned %s passages without required fields", dropped)
        backend = "corpus"
    else:
        passages = _search_fallback(question, as_of, limit)
        backend = "fallback"
    out = [
        {k: p.get(k) for k in ("source", "section", "edition_date", "url", "text", "score", "edition_note")}
        for p in passages
    ]
    result: dict[str, Any] = {"question": question, "as_of_date": as_of_date, "backend": backend, "passages": out}
    if backend == "fallback":
        result["note"] = (
            "Small fallback set (Construction Act payment sections, Building Regulations reg 3, GOV.UK approval guide). "
            "The full regulations corpus is not connected yet."
        )
        if as_of:
            result["note"] += " Fallback holds current versions only."
    if not out:
        result["note"] = (result.get("note", "") + " No passage matched: say so, do not answer from memory.").strip()
    return result
