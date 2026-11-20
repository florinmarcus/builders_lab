"""Validate the search chunks before they are embedded and loaded (corpus/OVERNIGHT-PLAN.md, S3).

    python -m system.rag.validate_chunks            # all corpus/chunks/*/*.jsonl; writes corpus/chunk-validation.md

Errors (exit code 1): a required field missing or empty; duplicate chunk ids; text too long for one Titan
embedding (it would be cut); page furniture left in the text (watermarks, "Page N of M" footers, dingbat bullets).
Warnings: very short chunks (they say little on their own) and long ones (above the chunker's split size).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from system.rag.corpus import CORPUS_DIR

REQUIRED = ("id", "source_id", "version_id", "section_id", "text", "embed_text", "heading_path", "url")
TOO_LONG = 20_000      # characters: dense text reaches Titan's 8,192-token limit around here
LONG = 4_000           # above the chunker's 2,500-character split size, with room for tables
SHORT = 25
JUNK = [
    (re.compile(r"O\s?N\s?L\s?I\s?N\s?E\s+V\s?E\s?R\s?S\s?I\s?O\s?N"), "watermark 'ONLINE VERSION'"),
    (re.compile(r"\bPage \d+ of \d+\b"), "page footer 'Page N of M'"),
    (re.compile(r"[■▪]"), "dingbat bullet"),
    (re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]"), "control character"),
]


def check_chunk(c: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    cid = c.get("id") or "(no id)"
    for f in REQUIRED:
        v = c.get(f)
        if v is None or v == "" or v == []:
            errors.append(f"{cid}: missing {f}")
    text = c.get("text") or ""
    for rx, name in JUNK:
        if rx.search(text):
            errors.append(f"{cid}: {name} in text")
    if len(text) > TOO_LONG:
        errors.append(f"{cid}: too long for one embedding ({len(text)} characters)")
    elif len(text) > LONG:
        warnings.append(f"{cid}: long ({len(text)} characters)")
    if text and len(text.strip()) < SHORT:
        warnings.append(f"{cid}: short ({len(text.strip())} characters): {text.strip()!r}")
    return errors, warnings


def validate(chunks_dir: Path | None = None) -> dict:
    chunks_dir = chunks_dir or CORPUS_DIR / "chunks"
    errors, warnings, seen = [], [], Counter()
    per_source, n = Counter(), 0
    for f in sorted(chunks_dir.glob("*/*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            n += 1
            per_source[c.get("source_id")] += 1
            seen[c.get("id")] += 1
            e, w = check_chunk(c)
            errors += e
            warnings += w
    errors += [f"{cid}: duplicate id ({k} times)" for cid, k in seen.items() if k > 1]
    return {"chunks": n, "sources": len(per_source), "errors": errors, "warnings": warnings}


def write_report(r: dict, path: Path | None = None) -> None:
    path = path or CORPUS_DIR / "chunk-validation.md"
    kinds = Counter(re.sub(r"^[^:]+:\s*", "", w).split(" (")[0] for w in r["warnings"])
    lines = ["# Chunk validation", "", "Made by `python -m system.rag.validate_chunks` (corpus/OVERNIGHT-PLAN.md, S3).", "",
             f"- Chunks: {r['chunks']} from {r['sources']} sources.",
             f"- Errors: {len(r['errors'])}. Warnings: {len(r['warnings'])} ("
             + ", ".join(f"{k} {v}" for k, v in kinds.most_common()) + ").", ""]
    if r["errors"]:
        lines += ["## Errors", ""] + [f"- {e}" for e in r["errors"][:300]] + [""]
    if r["warnings"]:
        lines += ["## Warnings (first 200)", ""] + [f"- {w}" for w in r["warnings"][:200]] + [""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    r = validate()
    write_report(r)
    print(f"{r['chunks']} chunks from {r['sources']} sources: {len(r['errors'])} errors, {len(r['warnings'])} warnings")
    for e in r["errors"][:15]:
        print("  ERROR", e)
    return 1 if r["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
