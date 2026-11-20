"""The model-check step, the same way every time (ADR 0010).

The parsers list what code could not decide as "checks" in the parsed tree. This module turns those
checks into packets with fixed instructions and a fixed answer format, saves the model's answers as
fixes after checking them, and lints every fix file. The runbook is the project skill
.claude/skills/corpus-document/SKILL.md.

    python -m system.rag.checks export --source hse-hsg227    # packets for the open checks
    python -m system.rag.checks save --source hse-hsg227 --answers answers.jsonl --by "..."
    python -m system.rag.checks lint [--source hse-hsg227]     # rules for every fix file (also a test)
    python -m system.rag.checks review --source hse-hsg227     # one sheet of all figure crops to look at

Packets go to corpus/parsed/<source>/checks/ (not in git). One answer per line in answers.jsonl:

    {"key": "...", "kind": "table", "value": {...}, "reason": "...", "evidence": "...", "confidence": "high"}

Tables in one family (same title before " for ", e.g. the HSG227 worked examples) must share one layout.
export sends only the first table of a new family; once its fix is saved, the next export sends the rest
with that fix as their template. lint fails if a family's saved fixes have different columns.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

from system.rag.corpus import CORPUS_DIR
from system.rag.fixes import FIX_KINDS, fixes_path, load_fixes

ROOT = CORPUS_DIR.parent
KEY_RE = re.compile(r"^[0-9a-f]{16}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONFIDENCE = {"high", "medium", "low"}

INSTRUCTIONS = {
    "table": """Rebuild this table from the page image(s). The library grid is a hint only; it can split or merge cells.
- columns: the column headings as printed (the lowest header row). If the first column holds a heading
  and a sub-heading on separate lines (a factor and its sub-factors), use two columns for them.
- rows: one list per printed data row, as many cells as columns. Copy the words exactly; keep units,
  symbols and spelling as printed (even typos). Repeat a row heading on every row it covers, so each row
  stands alone. A value printed once for a group (an overall score, a total) stays on the row where it
  is printed; other rows get "". Totals rows: the label in the first column, the value in its column.
- heading_rows: the indexes (from 0) of rows that are only a sub-heading ("Loose insulation") or a second
  header row inside the table. They get no sentence. A row with only its first cell filled is always one.
- sentences: one plain sentence per other row, in the same order. Start with what the table is about (from its
  title), then the row's facts in the table's own words. Add nothing that is not in the row and title.
- If a template is given, use exactly its columns and its sentence pattern.""",
    "figure": """Describe this figure in two or three plain sentences for search.
- Say what kind of figure it is (photo, diagram, flow chart) and what it shows.
- Include printed labels, numbers and steps exactly as printed. For a flow chart, give the steps in order.
- Describe only what you can see. Do not judge whether something contains asbestos or is safe.""",
    "applies_to": """Decide which country this copy applies to: "E" (England) or "W" (Wales).
Use the amendment notes and dates as evidence. Quote the note you relied on in "evidence".""",
    "requirement_code": """Give the requirement code this Part should have (for example "T1"). Use the Approved Document
for the Part as evidence and quote it with its page in "evidence".""",
}

FIX_KIND_OF_CHECK = {"table": "table", "figure": "figure_description",
                     "applies_to": "applies_to", "requirement_code": "requirement_code"}

ANSWER_FORMAT = {
    "table": {"columns": ["..."], "rows": [["...", "..."]], "heading_rows": [], "sentences": ["..."]},
    "figure_description": "Two or three plain sentences.",
    "applies_to": "E or W",
    "requirement_code": "T1",
}


# ---------------------------------------------------------------- trees and families

def current_trees(source_id: str) -> list[dict]:
    paths = sorted((CORPUS_DIR / "parsed" / source_id).glob("*.json"))
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def family(title: str | None) -> str | None:
    """A table family: the title before " for " ("Priority assessment algorithm for the boiler room").
    Titles without " for " have no family."""
    if not title or " for " not in title:
        return None
    return title.split(" for ", 1)[0].strip().lower()


def _target_title(target: str) -> str:
    return target.split(": ", 1)[1] if ": " in target else target


def _sentence_count(text: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s])


# ---------------------------------------------------------------- lint

def lint_fixes(source_id: str, fixes: list[dict]) -> list[str]:
    """Rules every saved fix must pass. Returns problems as plain sentences (empty list = fine)."""
    bad: list[str] = []
    seen: set[tuple[str, str]] = set()
    families: dict[str, tuple[str, list]] = {}
    for f in fixes:
        name = f"{source_id} {f.get('kind')} {f.get('target', f.get('key'))!r}"
        for field in ("key", "kind", "value", "target", "reason", "by", "date"):
            if field not in f or f[field] in (None, ""):
                bad.append(f"{name}: missing {field}")
        if not KEY_RE.match(str(f.get("key", ""))):
            bad.append(f"{name}: key is not 16 hex characters")
        if f.get("kind") not in FIX_KINDS:
            bad.append(f"{name}: unknown kind")
        if f.get("date") and not DATE_RE.match(str(f["date"])):
            bad.append(f"{name}: date is not YYYY-MM-DD")
        if f.get("confidence") and f["confidence"] not in CONFIDENCE:
            bad.append(f"{name}: confidence must be high, medium or low")
        if (f.get("key"), f.get("kind")) in seen:
            bad.append(f"{name}: duplicate fix for the same content")
        seen.add((f.get("key"), f.get("kind")))
        v = f.get("value")
        if f.get("kind") == "table":
            bad += [f"{name}: {p}" for p in _lint_table(v)]
            fam = family(_target_title(f.get("target", "")))
            if fam and isinstance(v, dict):
                if fam in families and families[fam][1] != v.get("columns"):
                    bad.append(f"{name}: columns differ from {families[fam][0]!r} in the same family "
                               f"({families[fam][1]} vs {v.get('columns')})")
                families.setdefault(fam, (f.get("target", ""), v.get("columns")))
        elif f.get("kind") == "figure_description":
            if not isinstance(v, str) or len(v) < 40:
                bad.append(f"{name}: description too short")
            elif not 1 <= _sentence_count(v) <= 6:
                bad.append(f"{name}: description should be a few sentences, has {_sentence_count(v)}")
        elif f.get("kind") == "applies_to" and v not in ("E", "W"):
            bad.append(f"{name}: applies_to must be E or W")
        elif f.get("kind") == "requirement_code" and not re.match(r"^[A-Z]\d+(\.\d+)?[A-Z]?$", str(v)):
            bad.append(f"{name}: requirement code looks wrong")
    return bad


def _lint_table(v) -> list[str]:
    if not isinstance(v, dict):
        return ["value must have columns, rows and sentences"]
    cols, rows, sents = v.get("columns"), v.get("rows"), v.get("sentences")
    bad = []
    if not cols or not all(isinstance(c, str) and c.strip() for c in cols):
        bad.append("every column needs a heading")
    if not rows or not all(isinstance(r, list) for r in rows):
        return bad + ["rows must be a list of lists"]
    if cols and any(len(r) != len(cols) for r in rows):
        bad.append(f"every row needs {len(cols)} cells")
    if cols and any(r == cols for r in rows):
        bad.append("header row repeated inside rows")
    heads = v.get("heading_rows", [])
    if not isinstance(heads, list) or not all(isinstance(i, int) and 0 <= i < len(rows) for i in heads):
        return bad + ["heading_rows must be row indexes"]
    lone = [i for i, r in enumerate(rows) if r and r[0].strip() and not any(c.strip() for c in r[1:])]
    if set(lone) - set(heads):
        bad.append(f"rows {sorted(set(lone) - set(heads))} have only a first cell: list them in heading_rows")
    want = len(rows) - len(set(heads))
    if not isinstance(sents, list) or len(sents) != want:
        bad.append(f"one sentence per row that is not a heading: {want} rows, {len(sents or [])} sentences")
    elif not all(isinstance(s, str) and s.strip().endswith((".", "?")) for s in sents):
        bad.append("every sentence must end with a full stop")
    return bad


def lint(source_ids: list[str] | None = None) -> list[str]:
    ids = source_ids or sorted(p.stem for p in (CORPUS_DIR / "fixes").glob("*.json"))
    bad = []
    for sid in ids:
        bad += lint_fixes(sid, load_fixes(sid))
    return bad


# ---------------------------------------------------------------- export

def packets(source_id: str, trees: list[dict], fixes: list[dict]) -> tuple[list[dict], list[str]]:
    """Packets for the open checks, and the ids held back until the first of their family is saved."""
    saved_families: dict[str, dict] = {}
    for f in fixes:
        fam = family(_target_title(f.get("target", ""))) if f["kind"] == "table" else None
        if fam and fam not in saved_families:
            saved_families[fam] = f
    out, held, sent_families = [], [], set()
    for tree in trees:
        S = {s["id"]: s for s in tree["sections"]}
        for c in tree.get("checks", []):
            kind = c["kind"]
            fix_kind = FIX_KIND_OF_CHECK.get(kind, kind)
            sec = S.get(c.get("section_id"), {})
            title = sec.get("title")
            target = f"{sec['id']}: {title}" if sec else c.get("question", "")
            p = {
                "source_id": source_id, "version_id": tree.get("version_id"), "key": c["key"],
                "kind": fix_kind, "target": target, "instructions": INSTRUCTIONS[kind],
                "answer_format": {"key": c["key"], "kind": fix_kind, "value": ANSWER_FORMAT[fix_kind],
                                  "reason": "...", "evidence": "...", "confidence": "high | medium | low"},
                "images": c.get("images", []), "check": c,
            }
            if sec:
                p["section"] = {k: sec.get(k) for k in ("id", "title", "text", "labels", "grid", "printed_page")}
            fam = family(title) if kind == "table" else None
            if fam:
                if fam in saved_families:
                    t = saved_families[fam]
                    p["template"] = {"from": t["target"], "columns": t["value"]["columns"],
                                     "rows": t["value"]["rows"][:3], "sentences": t["value"]["sentences"][:3]}
                elif fam in sent_families:
                    held.append(target)
                    continue
                else:
                    sent_families.add(fam)
                    p["first_of_family"] = fam
            out.append(p)
    return out, held


def export(source_id: str) -> int:
    trees = current_trees(source_id)
    if not trees:
        print(f"no parsed tree for {source_id}: run the parser first")
        return 1
    ps, held = packets(source_id, trees, load_fixes(source_id))
    d = CORPUS_DIR / "parsed" / source_id / "checks"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.json"):
        old.unlink()
    for i, p in enumerate(ps, start=1):
        (d / f"{i:03d}-{p['kind']}-{p['key']}.json").write_text(json.dumps(p, ensure_ascii=False, indent=1),
                                                                 encoding="utf-8")
    print(f"{len(ps)} packets -> {d.relative_to(ROOT)}")
    if held:
        print(f"{len(held)} held back until the first table of their family is saved: run export again after save")
    return 0


# ---------------------------------------------------------------- save

def save(source_id: str, answers_path: Path, by: str, today: str | None = None) -> int:
    """Check each answer against its packet and the lint rules; save the good ones, report the rest."""
    d = CORPUS_DIR / "parsed" / source_id / "checks"
    by_key = {}
    for p in d.glob("*.json"):
        pk = json.loads(p.read_text(encoding="utf-8"))
        by_key[(pk["key"], pk["kind"])] = pk
    path = fixes_path(source_id)
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "source_id": source_id, "about": f"Saved model fixes for {source_id} (ADR 0010).", "fixes": []}
    fixes = doc["fixes"]
    today = today or datetime.date.today().isoformat()
    saved, rejected = 0, 0
    for n, line in enumerate(answers_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        a = json.loads(line)
        pk = by_key.get((a.get("key"), a.get("kind")))
        if not pk:
            print(f"line {n}: no open check with key {a.get('key')} and kind {a.get('kind')}")
            rejected += 1
            continue
        fix = {"key": a["key"], "kind": a["kind"], "target": pk["target"], "value": a.get("value"),
               "reason": a.get("reason") or "", "evidence": a.get("evidence") or "", "by": by,
               "confidence": a.get("confidence") or "medium", "date": today}
        if pk.get("template") and isinstance(fix["value"], dict) and fix["value"].get("columns") != pk["template"]["columns"]:
            print(f"line {n} ({pk['target']}): columns differ from the template {pk['template']['columns']}")
            rejected += 1
            continue
        others = [f for f in fixes if (f["key"], f["kind"]) != (fix["key"], fix["kind"])]
        problems = [p for p in lint_fixes(source_id, others + [fix]) if pk["target"] in p or fix["key"] in p]
        if problems:
            print(f"line {n}: " + "; ".join(problems))
            rejected += 1
            continue
        doc["fixes"] = fixes = others + [fix]
        saved += 1
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"saved {saved}, rejected {rejected} -> {path.relative_to(ROOT)}")
    return 1 if rejected else 0


# ---------------------------------------------------------------- review sheet

def review(source_id: str) -> int:
    """One image with every figure crop and its id, to look at after each parse."""
    from PIL import Image, ImageDraw

    for tree in current_trees(source_id):
        figs = [s for s in tree["sections"] if s["type"] == "figure" and s.get("image_path")]
        if not figs:
            continue
        thumbs = []
        for s in figs:
            im = Image.open(ROOT / s["image_path"]).convert("RGB")
            im.thumbnail((360, 300))
            tile = Image.new("RGB", (380, 330), "white")
            tile.paste(im, (10, 24))
            ImageDraw.Draw(tile).text((10, 6), f"{s['id']}: {(s.get('title') or '')[:48]}", fill="black")
            thumbs.append(tile)
        cols = 4
        sheet = Image.new("RGB", (cols * 380, ((len(thumbs) + cols - 1) // cols) * 330), (230, 230, 230))
        for i, t in enumerate(thumbs):
            sheet.paste(t, ((i % cols) * 380, (i // cols) * 330))
        out = CORPUS_DIR / "parsed" / source_id / f"{tree['version_id']}-figures.png"
        sheet.save(out)
        print(f"{len(figs)} figures -> {out.relative_to(ROOT)}")
    return 0


# ---------------------------------------------------------------- command line

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("export", "review"):
        sub.add_parser(name).add_argument("--source", required=True)
    s = sub.add_parser("save")
    s.add_argument("--source", required=True)
    s.add_argument("--answers", required=True, type=Path)
    s.add_argument("--by", required=True, help='who answered, e.g. "model check, Claude Code subagent"')
    l = sub.add_parser("lint")
    l.add_argument("--source", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "export":
        return export(a.source)
    if a.cmd == "save":
        return save(a.source, a.answers, a.by)
    if a.cmd == "review":
        return review(a.source)
    bad = lint(a.source)
    for b in bad:
        print(b)
    print("fixes ok" if not bad else f"{len(bad)} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
