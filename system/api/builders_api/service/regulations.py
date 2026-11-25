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
LIBRARY_FILE = FALLBACK_FILE.with_name("library.json")  # built by python -m system.rag.library
REQUIRED = ("text", "source", "section", "edition_date", "url")


@cache
def _rag_fn(name: str):
    """Return rag.<name>, or None if the corpus module (or that function) is not there."""
    parent = str(rag_dir())
    if parent not in sys.path:
        sys.path.append(parent)
    try:
        import rag  # type: ignore[import-not-found]
    except ImportError:
        return None
    fn = getattr(rag, name, None)
    return fn if callable(fn) else None


def _corpus_search():
    return _rag_fn("search")


def _corpus_about():
    return _rag_fn("about")


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


# ---- about_regulations_library (S100) ----

PARTS = ("summary", "contents", "gaps")
WEIGHT_TYPE = {"law": "law", "statutory-guidance": "approved_document", "approved-code": "hse_guidance",
               "guidance": "guidance"}
EXAMPLES_PER_GAP = 4


@cache
def _library() -> dict:
    return json.loads(LIBRARY_FILE.read_text())


def _held_documents(lib: dict) -> tuple[dict[str, Any], list[dict], list[dict]]:
    """(version, loaded documents, documents listed but not loaded) from the live corpus, or the fallback set."""
    meta = {d["id"]: d for d in lib["documents"]}
    about = _corpus_about()
    if about is None:
        by_src: dict[str, dict] = {}
        for p in _fallback():
            d = by_src.setdefault(p["source"], {"title": p["source"], "type": "law", "publisher": None,
                                                "edition_date": p["edition_date"], "url": p["url"].split("#")[0],
                                                "passages": 0, "topics": []})
            d["passages"] += 1
        version = {"backend": "fallback", "loaded_at": None, "documents": len(by_src),
                   "passages": len(_fallback()),
                   "note": "Only a small fallback set is connected (Construction Act payment sections, Building "
                           "Regulations reg 3, GOV.UK approval guide). The full library is not connected."}
        return version, list(by_src.values()), []
    try:
        live = with_retries(about)
    except Exception as exc:  # noqa: BLE001
        log.exception("corpus about failed")
        raise UpstreamError("The regulations library is not answering right now.",
                            retryable=bool(getattr(exc, "retryable", False))) from None
    docs = []
    for s in live["sources"]:
        m = meta.get(s["source_id"], {})
        doc = {"title": s.get("title") or m.get("title") or s["source_id"],
               "type": m.get("type") or WEIGHT_TYPE.get(s.get("legal_weight"), "other"),
               "publisher": m.get("publisher"), "edition_date": s.get("edition_date"),
               "url": s.get("url") or m.get("url"), "passages": s.get("passages"), "topics": m.get("topics", [])}
        if s.get("next_from"):
            doc["newer_version_from"] = s["next_from"]
        docs.append(doc)
    loaded = {s["source_id"] for s in live["sources"]}
    missing = [{"title": d["title"], "publisher": d.get("publisher"), "url": d.get("url")}
               for d in lib["documents"] if d["id"] not in loaded]
    version = {"backend": "corpus", "loaded_at": live.get("loaded_at"), "documents": len(docs),
               "passages": live.get("passages"), "schema_version": live.get("schema_version")}
    return version, docs, missing


def about_regulations_library(part: str = "summary") -> dict[str, Any]:
    """What the regulations library holds, which version is loaded, what it does not hold and why, and how good
    search is. part: summary (default, short), contents (every document) or gaps (every missing document)."""
    part = (part or "summary").strip().lower()
    if part not in PARTS:
        raise ValidationError("part must be summary, contents or gaps.")
    lib = _library()
    version, docs, missing = _held_documents(lib)
    version |= {"nation": "England", "versions_in_force_from": "2025-01-01", "language": "English"}
    types = lib["types"]
    order = list(types)
    docs.sort(key=lambda d: (order.index(d["type"]) if d["type"] in order else len(order), d["title"]))
    gaps: dict[str, list[dict]] = {}
    for g in lib["not_held"]:
        gaps.setdefault(g["reason"], []).append(g)
    result: dict[str, Any] = {"part": part, "version": version}

    if part == "summary":
        counts: dict[str, int] = {}
        topics: dict[str, int] = {}
        for d in docs:
            counts[d["type"]] = counts.get(d["type"], 0) + 1
            for t in d.get("topics") or []:
                topics[t] = topics.get(t, 0) + 1
        result["contents"] = {
            "by_type": [{"type": t, "label": types.get(t, "Other documents"), "documents": n}
                        for t, n in counts.items()],
            "by_topic": dict(sorted(topics.items(), key=lambda kv: (-kv[1], kv[0]))),
        }
        result["gaps"] = {
            "scope": lib["scope"],
            "not_held": [{"reason": lib["reasons"][r], "documents": len(gs),
                          "examples": [g["title"] for g in gs[:EXAMPLES_PER_GAP]]} for r, gs in gaps.items()],
            "listed_but_not_loaded": len(missing),
            "known_weak_parts": lib["known_weak_parts"],
        }
        result["more"] = "Call again with part 'contents' for every document, or part 'gaps' for every missing one."
    elif part == "contents":
        result["documents"] = [{k: v for k, v in d.items() if k != "topics"} for d in docs]
    else:
        result["scope"] = lib["scope"]
        result["not_held"] = [{"reason": lib["reasons"][r],
                               "documents": [{k: g[k] for k in ("title", "publisher", "url", "why_it_matters")}
                                             for g in gs]} for r, gs in gaps.items()]
        result["listed_but_not_loaded"] = {
            "note": "Free documents we plan to hold that are not in the loaded library yet (still being cleaned, or "
                    "loaded in a later version).", "documents": missing}
        result["known_weak_parts"] = lib["known_weak_parts"]
    result["quality"] = lib["quality"]
    return result
