"""Terminology layer: Romanian <-> UK English builder terms (ADR 0001, ADR 0012). Plain code, no model.

Source of truth: research/domain/glossary.md (the table). glossary.json is generated from it:
  python -m builders_api.terminology --build      (from system/api)
tests/test_terminology.py fails if glossary.json is out of date.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import cache
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
JSON_FILE = HERE / "glossary.json"
SOURCE = HERE.parents[3] / "research" / "domain" / "glossary.md"
MISMATCH_ROWS = {1, 32, 41, 42, 47, 108}  # the two systems do not match: never translate word for word


def fold(text: str) -> str:
    """Lower case, no diacritics, no curly quotes: 'Perete de rezistență' -> 'perete de rezistenta'."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[„“”\"'’]", "", text)


def _variants(cell: str) -> list[str]:
    """'deviz (estimativ) / ofertă' -> ['deviz', 'deviz estimativ', 'oferta']"""
    out = []
    for part in cell.split("/"):
        part = part.strip()
        if not part or part in ("—", "-"):
            continue
        bare = re.sub(r"\(.*?\)", "", part).strip()
        full = re.sub(r"[()]", "", part).strip()
        for v in {fold(bare), fold(full)}:
            v = re.sub(r"[^a-z0-9 ]+", " ", v)
            v = re.sub(r"\s+", " ", v).strip()
            if len(v) >= 3:
                out.append(v)
    return sorted(set(out), key=lambda v: (-len(v), v))


def build(source: Path = SOURCE) -> list[dict[str, Any]]:
    entries, section = [], ""
    for line in source.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        if cells[0].startswith("**"):
            section = cells[0].strip("*")
            continue
        if not cells[0].isdigit():
            continue
        n, ro, en, note, status = int(cells[0]), cells[1], cells[2], cells[3], cells[4]
        entries.append({
            "n": n, "section": section, "ro": ro, "en": en, "note": note, "status": status,
            "mismatch": n in MISMATCH_ROWS or en.lower().startswith("(no exact equivalent)"),
            "ro_keys": _variants(ro), "en_keys": _variants(re.sub(r"\(no exact equivalent\)", "", en, flags=re.I)),
        })
    return entries


@cache
def entries() -> list[dict[str, Any]]:
    return json.loads(JSON_FILE.read_text())["entries"]


def _stem(word: str) -> str:
    """Drop a final vowel on longer words so Romanian endings still match: perete -> peret (pereti, peretele)."""
    return word[:-1] if len(word) > 4 and word[-1] in "aeiu" else word


def _matches(key: str, tokens: list[str]) -> bool:
    """All key words, in order and next to each other, each the start of a text word (exact for short words)."""
    kws = key.split()
    for i in range(len(tokens) - len(kws) + 1):
        if all((tokens[i + j] == k) if len(k) <= 3 else tokens[i + j].startswith(_stem(k)) for j, k in enumerate(kws)):
            return True
    return False


def lookup(text: str, direction: str = "auto", limit: int = 15) -> dict[str, Any]:
    tokens = re.sub(r"[^a-z0-9 ]+", " ", fold(text)).split()
    dirs = ["ro", "en"] if direction == "auto" else [direction.split("-")[0]]
    hits = []
    for e in entries():
        for d in dirs:
            matched = next((k for k in e[f"{d}_keys"] if _matches(k, tokens)), None)
            if matched:
                hits.append((len(matched), d, matched, e))
                break
    hits.sort(key=lambda h: (-h[0], h[3]["n"]))
    seen, out = set(), []
    for _, d, matched, e in hits:
        if e["n"] in seen:
            continue
        seen.add(e["n"])
        out.append({"matched": matched, "from": d, "romanian": e["ro"], "english": e["en"], "note": e["note"],
                    "mismatch": e["mismatch"], "status": e["status"]})
    return {
        "terms": out[:limit],
        "note": "Use the English terms when calling other tools. Where mismatch is true, explain the difference "
                "instead of translating word for word. Status 'unverified' means a native-speaker check is pending.",
    }
