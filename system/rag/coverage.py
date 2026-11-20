"""Coverage of the corpus: which sources are parsed, checked and chunked (corpus/OVERNIGHT-PLAN.md, S1).

    python -m system.rag.coverage            # writes corpus/coverage.md and prints the summary

One row per source in scope (mode ingest, fetched; restricted and link-only sources are out of scope tonight).
For each: current versions and their file types, raw file present, the parser assigned in sources.yaml (or the
one that fits the file type), parsed trees, open model checks, chunk files.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from system.rag.corpus import CORPUS_DIR, load_sources

ROOT = CORPUS_DIR.parent


def fitting_parser(src: dict, media_types: set[str]) -> str:
    """The parser family that fits a source by its fetch method and file types."""
    if src.get("fetch", {}).get("method") == "legislation" or "application/xml" in media_types:
        return "parse_legislation"
    if media_types and media_types <= {"text/html", "application/xhtml+xml"}:
        return "parse_html"
    if "application/pdf" in media_types:
        return "parse_adoc" if src.get("kind") == "approved-document" else "parse_pdf"
    if "text/html" in media_types:
        return "parse_html"
    return "unknown"


def in_scope(src: dict) -> bool:
    return src.get("mode") == "ingest" and src.get("fetch", {}).get("method", "none") != "none"


def current_records(sid: str) -> list[dict]:
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (CORPUS_DIR / "versions" / sid).glob("*.json")]
    return [r for r in recs if r.get("valid_to") is None]


def row(src: dict) -> dict:
    sid = src["id"]
    recs = current_records(sid)
    media = {r.get("media_type", "") for r in recs}
    raw_ok = sum(1 for r in recs if (ROOT / r["raw_path"]).exists())
    trees = list((CORPUS_DIR / "parsed" / sid).glob("*.json"))
    checks = 0
    for t in trees:
        try:
            checks += len(json.loads(t.read_text(encoding="utf-8")).get("checks", []))
        except (json.JSONDecodeError, OSError):
            checks += 1
    chunks = list((CORPUS_DIR / "chunks" / sid).glob("*.jsonl"))
    assigned = (src.get("parser") or {}).get("module")
    fits = fitting_parser(src, media)
    if chunks and not checks:
        status = "chunked"
    elif trees and checks:
        status = "parsed, open checks"
    elif trees:
        status = "parsed"
    elif raw_ok < len(recs) or not recs:
        status = "raw missing"
    else:
        status = "to parse"
    return {"id": sid, "priority": src.get("priority", 3), "kind": src.get("kind"), "parts": len(recs),
            "raw": f"{raw_ok}/{len(recs)}", "media": ", ".join(sorted(m.split("/")[-1] for m in media if m)),
            "assigned": assigned or "", "fits": fits, "trees": len(trees), "checks": checks,
            "chunk_files": len(chunks), "status": status}


def build() -> list[dict]:
    return [row(s) for s in load_sources()["sources"] if in_scope(s)]


def write(rows: list[dict], path: Path | None = None) -> str:
    path = path or CORPUS_DIR / "coverage.md"
    by_status = Counter(r["status"] for r in rows)
    by_family = Counter(r["assigned"] or r["fits"] for r in rows)
    lines = ["# Corpus coverage", "",
             "Made by `python -m system.rag.coverage` (corpus/OVERNIGHT-PLAN.md, S1). In scope: sources with mode "
             "`ingest` that are fetched. Restricted and link-only sources are out of scope tonight.", "",
             f"- Sources in scope: {len(rows)}.",
             "- By status: " + ", ".join(f"{k} {v}" for k, v in by_status.most_common()) + ".",
             "- By parser (assigned, else the one that fits): " + ", ".join(f"{k} {v}" for k, v in by_family.most_common()) + ".",
             "", "| id | priority | kind | parts | raw | file types | parser assigned | fits | trees | open checks | chunk files | status |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["priority"], r["fits"], r["id"])):
        lines.append(f"| {r['id']} | {r['priority']} | {r['kind']} | {r['parts']} | {r['raw']} | {r['media']} | "
                     f"{r['assigned']} | {r['fits']} | {r['trees']} | {r['checks']} | {r['chunk_files']} | {r['status']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines[4] + "\n" + lines[5] + "\n" + lines[6]


def main(argv: list[str] | None = None) -> int:
    print(write(build()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
