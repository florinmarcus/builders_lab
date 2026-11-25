"""Build the regulations library description that the about_regulations_library tool reads (S100).

    python -m system.rag.library          # writes system/api/builders_api/regulations_fallback/library.json
    python -m system.rag.library --check  # fails if the file is out of date with corpus/sources.yaml

The file holds what the server cannot read from the corpus database: publisher, kind and topics of the documents
we hold, the documents we do not hold and why (link_only, restricted and non-English sources), the scope and the
known weak parts. The live part (load date, documents and passages loaded, edition dates) comes from the corpus
database at call time (pgsearch.about). tests/test_library.py fails when this file is stale.

Every line here must be something we know. Reasons for a gap are worked out from sources.yaml fields only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from system.rag.corpus import REPO_ROOT as REPO, load_sources

OUT = REPO / "system" / "api" / "builders_api" / "regulations_fallback" / "library.json"

# Kept by hand. Each line is a rule the corpus or search code applies, with its source.
SCOPE = [
    "England only: search returns rules that apply in England (UK-wide and GB-wide documents included). Wales, "
    "Scotland and Northern Ireland have their own rules, not covered.",
    "English text only (ADR 0012, S130): translations and Romanian leaflets are not in the library.",
    "Versions in force on or after 1 January 2025 (ADR 0016). Older editions are not held.",
    "Text only: drawings, diagrams and photos are not read, only their captions and the text around them.",
    "Only documents we may copy (Open Government Licence). Paid standards and contracts are listed as gaps.",
]

KNOWN_WEAK_PARTS = [
    "Tables in Approved Documents and guidance PDFs: a check on 23 Nov 2026 found a serious reading problem on about "
    "1 in 8 of the pages it sampled, mostly tables. Fixes are in progress; quote tables with care.",
    "Each search returns the best few passages only. A broad question can miss the rule it needs: split it into "
    "short searches, one per topic.",
]

QUALITY = ("How often search finds the right passage is not measured yet (S151). Until then, answer only from the "
           "passages returned and cite them.")

TYPES = {  # sources.yaml kind -> (type, label)
    "legislation": ("law", "Laws and regulations"),
    "approved-document": ("approved_document", "Approved Documents (building regulations guidance)"),
    "hse-guidance": ("hse_guidance", "HSE guidance and approved codes of practice"),
    "guidance": ("guidance", "Government and official guidance"),
    "tax-guidance": ("tax_guidance", "HMRC guidance (CIS, VAT)"),
    "standard": ("standard", "British and industry standards"),
    "contract": ("contract", "Standard building contracts"),
}

REASONS = {  # in the order the tool lists them: the gaps a builder meets most first
    "paid_standard": "Paid or copyrighted standard: we may not copy it, so we hold only the link.",
    "paid_contract": "Paid standard contract: we may not copy it, so we hold only the link.",
    "licence_unclear": "Licence unclear or not checked yet: not copied until it is.",
    "link_only": "Link only: the publisher's terms bar copying, or the text could not be fetched.",
    "not_english": "Not in English: the library holds English text only.",
    "withdrawn": "Withdrawn or out of date: listed so we know it has gone.",
}


def type_of(kind: str) -> tuple[str, str]:
    return TYPES.get(kind, ("other", "Other documents"))


def reason_of(src: dict) -> str | None:
    """Why we do not hold this source, or None when we do (an English source we ingest)."""
    english = (src.get("language") or "en") == "en"
    if src.get("mode") == "ingest" and english:
        return None
    if src.get("status") in ("withdrawn", "out-of-date"):
        return "withdrawn"
    if not english:
        return "not_english"
    if src.get("kind") == "standard":
        return "paid_standard"
    if src.get("kind") == "contract":
        return "paid_contract"
    if src.get("mode") == "restricted" or src.get("licence") == "unclear":
        return "licence_unclear"
    return "link_only"


def build(sources: dict | None = None) -> dict:
    srcs = (sources or load_sources())["sources"]
    held, not_held = [], []
    for s in srcs:
        why = reason_of(s)
        base = {"id": s["id"], "title": s["title"], "publisher": s.get("publisher"), "type": type_of(s["kind"])[0],
                "url": s.get("url")}
        if why is None:
            held.append({**base, "status": s.get("status"),
                         "topics": [t for t in (s.get("topics") or []) if t != "romanian"]})
        else:
            not_held.append({**base, "reason": why, "why_it_matters": (s.get("why") or "").strip(),
                             "priority": s.get("priority") or 9})
    order = list(REASONS)
    not_held.sort(key=lambda g: (order.index(g["reason"]), g["priority"], g["title"]))
    for g in not_held:
        del g["priority"]
    return {
        "about": "Built by python -m system.rag.library from corpus/sources.yaml. Do not edit by hand.",
        "scope": SCOPE,
        "known_weak_parts": KNOWN_WEAK_PARTS,
        "quality": QUALITY,
        "types": {t: label for t, label in TYPES.values()},
        "reasons": REASONS,
        "documents": held,
        "not_held": not_held,
    }


def render(lib: dict) -> str:
    return json.dumps(lib, indent=1, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail if the file is out of date")
    args = ap.parse_args(argv)
    text = render(build())
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT.relative_to(REPO)} is out of date: run python -m system.rag.library", file=sys.stderr)
            return 1
        print("library.json is up to date")
        return 0
    OUT.write_text(text)
    lib = json.loads(text)
    print(f"wrote {OUT.relative_to(REPO)}: {len(lib['documents'])} held, {len(lib['not_held'])} not held")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
