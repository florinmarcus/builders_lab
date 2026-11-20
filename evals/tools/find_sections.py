"""Find section ids in the parsed trees, for the golden set's LABELLING pass (not the business pass).

    python evals/tools/find_sections.py car2012 regulation 7          # sections whose number/title/text match
    python evals/tools/find_sections.py hse-l143 "licensed work" --text  # also show the start of each text
    python evals/tools/find_sections.py adb --ids para-3.22 table-c1     # show these exact ids

Prints "<source_id>:<section_id> | type | breadcrumb tail | (text start)". Use these keys in expected_sections.
Prefer the section that holds the answer itself (a regulation or clause, a numbered paragraph, a table) over
chapters and headings. Only current trees (valid_to empty) are searched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP = {"part", "chapter", "appendix", "schedule", "schedule-part", "heading", "block", "back-matter", "references"}


def sections(source_id: str):
    for t in sorted((ROOT / "corpus" / "parsed" / source_id).glob("*.json")):
        d = json.loads(t.read_text(encoding="utf-8"))
        if "sections" not in d or d.get("valid_to"):
            continue
        for s in d["sections"]:
            yield s


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sid, rest = argv[0], argv[1:]
    show_text = "--text" in rest
    rest = [r for r in rest if r != "--text"]
    if rest and rest[0] == "--ids":
        want = set(rest[1:])
        hits = [s for s in sections(sid) if s["id"] in want]
    else:
        words = [w.lower() for w in rest]
        hits = []
        for s in sections(sid):
            hay = " ".join([s["id"], str(s.get("number") or ""), s.get("title") or "", " ".join(s.get("heading_path") or []),
                            (s.get("text") or "")[:3000]]).lower()
            if all(w in hay for w in words):
                hits.append(s)
    for s in hits[:60]:
        tail = " › ".join((s.get("heading_path") or [])[-2:])
        line = f"{sid}:{s['id']} | {s['type']}{' (heading only)' if s['type'] in SKIP else ''} | {tail}"
        if show_text:
            line += " | " + " ".join((s.get("text") or "").split())[:160]
        print(line)
    if len(hits) > 60:
        print(f"... {len(hits) - 60} more; add words to narrow")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
