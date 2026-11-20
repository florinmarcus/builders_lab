"""Saved model fixes for the parsers (ADR 0010).

A fix records a decision the code could not make on its own: which copy of a duplicated
Schedule 1 Part is England's, a requirement code missing from the XML, later table and diagram
checks for PDFs. Fixes are small, reviewable and needed to rebuild a parse, so they live in git:
corpus/fixes/<source_id>.json

Each fix is linked to a fingerprint of the content it is about (content_key), not to the whole
file. The same table in the next version of the law has the same fingerprint, so the fix carries
over. If the content changes, the fix no longer matches and the check comes back.

    {"source_id": "br2010",
     "fixes": [{"key": "...", "kind": "applies_to", "value": "E", "target": "...",
                "reason": "...", "evidence": "...", "by": "...", "date": "2026-11-20"}]}
"""

from __future__ import annotations

import hashlib
import json

from system.rag.corpus import CORPUS_DIR

FIX_KINDS = {"applies_to", "requirement_code"}


def content_key(text: str) -> str:
    """Fingerprint of a piece of content: SHA-256 of its whitespace-collapsed text, first 16 hex characters."""
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()[:16]


def fixes_path(source_id: str):
    return CORPUS_DIR / "fixes" / f"{source_id}.json"


def load_fixes(source_id: str) -> list[dict]:
    p = fixes_path(source_id)
    if not p.exists():
        return []
    doc = json.loads(p.read_text(encoding="utf-8"))
    fixes = doc.get("fixes", [])
    for f in fixes:
        if f.get("kind") not in FIX_KINDS or not f.get("key") or "value" not in f:
            raise ValueError(f"bad fix in {p}: {f}")
    return fixes


def index(fixes: list[dict] | None) -> dict[tuple[str, str], dict]:
    return {(f["key"], f["kind"]): f for f in (fixes or [])}
