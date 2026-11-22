"""Model check of figure crops: does each cut-out image show the whole figure its caption names, and nothing else?

The parsers cut figures out of PDF pages by rules. Rules go wrong (a crop cut short, a neighbour's photo or a caption
inside the box), and a bad crop gives the figure description and the search index a wrong picture. This tool asks
a model, in Claude Code on the user's plan (never Bedrock, ADR 0006), to look at each crop next to its page with the
crop box drawn on it.

    python -m system.rag.cropcheck export --source hse-hsg33     # packets -> corpus/parsed/<source>/cropcheck/
    (run the packets with Claude Code subagents or headless `claude -p`, as for model checks)
    python -m system.rag.cropcheck save --source hse-hsg33 --answers answers.jsonl --by "Sonnet, Claude Code"
    python -m system.rag.cropcheck report [--source ...]          # bad crops per source

Verdicts are saved in `corpus/cropchecks/<source>.json`, keyed by the SHA-256 of the crop image, so a crop that did
not change is not judged again, and a crop that changed (after a parser fix) is judged afresh.
A bad crop is a parser bug: fix the parser, parse again, export again (only changed crops come back).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

from system.rag.corpus import CORPUS_DIR

ROOT = CORPUS_DIR.parent
VERDICTS = ("ok", "cut", "extra", "wrong", "empty")  # plus "accepted": bad by the model, kept by a person
BAD = {"cut", "extra", "wrong", "empty"}

INSTRUCTIONS = """You check one figure crop from a guidance document. Image 1 is the crop (the cut-out picture).
Image 2 is the whole page, with the crop box drawn in red. `caption` is the figure's caption as parsed.

Give exactly one verdict:
- "ok": the red box holds the whole figure the caption names (all of its drawing or photo, its labels, key and
  source line) and nothing else of substance. The figure's own caption inside the box is fine (say so in problem).
- "cut": part of this figure lies outside the red box (a side, the top or bottom of a drawing, one of several
  photos that belong to this figure, labels or a key).
- "extra": the box also holds something that is not part of this figure: another figure or photo, another
  figure's caption, or body text.
- "wrong": the box shows a different figure from the one the caption names, or text instead of a figure.
- "empty": the box is blank or nearly blank.
If both cut and extra apply, say "cut" and describe both in problem.
Judge from the page image, not from what the caption leads you to expect. Small white margins do not matter."""

ANSWER_FORMAT = {"verdict": "ok | cut | extra | wrong | empty",
                 "problem": "one plain sentence on what is wrong, or \"\" when ok",
                 "caption_inside": "true if the figure's own caption text is inside the box"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record(source_id: str, version_id: str) -> dict:
    return json.loads((CORPUS_DIR / "versions" / source_id / f"{version_id}.json").read_text(encoding="utf-8"))


def verdicts_path(source_id: str) -> Path:
    return CORPUS_DIR / "cropchecks" / f"{source_id}.json"


def load_verdicts(source_id: str) -> dict:
    p = verdicts_path(source_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"source_id": source_id, "about": f"Model verdicts on figure crops for {source_id} (system/rag/cropcheck.py).",
            "verdicts": {}}


def figures(tree: dict) -> list[dict]:
    """Figure sections that were cut out of a page and know their box."""
    return [s for s in tree["sections"] if s["type"] == "figure" and s.get("image_path") and s.get("area")]


def overlay(page_img, area: dict, scale: float):
    """The page with the crop box drawn in red (a copy)."""
    from PIL import ImageDraw

    im = page_img.convert("RGB").copy()
    d = ImageDraw.Draw(im)
    box = [area["x0"] * scale, area["top"] * scale, area["x1"] * scale, area["bottom"] * scale]
    for w in range(3):
        d.rectangle([box[0] - w, box[1] - w, box[2] + w, box[3] + w], outline=(230, 0, 0))
    return im


def _page_renderer(pdf_path: Path, scale: float):
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    cache: dict[int, object] = {}

    def page_image(n: int):
        if n not in cache:
            page = pdf[n - 1]
            media = page.get_mediabox()
            if tuple(page.get_cropbox()) != tuple(media):  # same rule as parse_pdf.render_images
                page.set_cropbox(*media)
            cache[n] = page.render(scale=scale).to_pil()
        return cache[n]

    return page_image, pdf


def export(source_id: str, scale: float = 1.5, all_: bool = False) -> int:
    from system.rag.checks import current_trees

    done = load_verdicts(source_id)["verdicts"]
    out = CORPUS_DIR / "parsed" / source_id / "cropcheck"
    (out / "pages").mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    n = skipped = 0
    for tree in current_trees(source_id):
        figs = figures(tree)
        if not figs:
            continue
        rec = _record(source_id, tree["version_id"])
        page_image, pdf = _page_renderer(ROOT / rec["raw_path"], scale)
        for s in figs:
            crop = ROOT / s["image_path"]
            if not crop.exists():
                continue
            key = _sha(crop)[:16]
            if key in done and not all_:
                skipped += 1
                continue
            a = s["area"]
            ov = out / "pages" / f"{key}.png"
            overlay(page_image(a["page"]), a, scale).save(ov)
            n += 1
            packet = {"source_id": source_id, "version_id": tree["version_id"], "key": key, "kind": "crop",
                      "target": f"{s['id']}: {s.get('title') or ''}", "caption": s.get("title") or "",
                      "page": a["page"], "instructions": INSTRUCTIONS,
                      "answer_format": {"key": key, "kind": "crop", **ANSWER_FORMAT, "confidence": "high | medium | low"},
                      "images": [s["image_path"], ov.relative_to(ROOT).as_posix()]}
            (out / f"{n:03d}-crop-{key}.json").write_text(json.dumps(packet, ensure_ascii=False, indent=1),
                                                          encoding="utf-8")
        pdf.close()
    print(f"{n} crop packets -> {out.relative_to(ROOT)} ({skipped} crops already judged)")
    return 0


def save(source_id: str, answers_path: Path, by: str, today: str | None = None) -> int:
    out = CORPUS_DIR / "parsed" / source_id / "cropcheck"
    packets = {}
    for p in out.glob("*.json"):
        pk = json.loads(p.read_text(encoding="utf-8"))
        packets[pk["key"]] = pk
    doc = load_verdicts(source_id)
    today = today or datetime.date.today().isoformat()
    saved = rejected = 0
    for n, line in enumerate(answers_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        a = json.loads(line)
        pk = packets.get(a.get("key"))
        if not pk or a.get("verdict") not in VERDICTS:
            print(f"line {n}: unknown key or verdict: {a.get('key')} {a.get('verdict')}")
            rejected += 1
            continue
        doc["verdicts"][a["key"]] = {
            "version_id": pk["version_id"], "figure": pk["target"].split(": ", 1)[0], "page": pk["page"],
            "verdict": a["verdict"], "problem": a.get("problem") or "",
            "caption_inside": bool(a.get("caption_inside")) if not isinstance(a.get("caption_inside"), str)
            else a["caption_inside"].lower() == "true",
            "confidence": a.get("confidence") or "medium", "by": by, "date": today}
        saved += 1
    p = verdicts_path(source_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc["verdicts"] = dict(sorted(doc["verdicts"].items(), key=lambda kv: (kv[1]["version_id"], kv[1]["page"],
                                                                           kv[1]["figure"])))
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"saved {saved}, rejected {rejected} -> {p.relative_to(ROOT)}")
    return 1 if rejected else 0


def accept(source_id: str, figure: str, reason: str, by: str, today: str | None = None) -> int:
    """A person (or the lead agent) looked at a crop the model called bad and keeps it: record why."""
    doc = load_verdicts(source_id)
    hits = [v for v in doc["verdicts"].values() if v["figure"] == figure and v["verdict"] in BAD]
    if not hits:
        print(f"no bad verdict for {figure}")
        return 1
    for v in hits:
        v.update({"verdict": "accepted", "model_verdict": v["verdict"], "accepted_reason": reason, "by": by,
                  "date": today or datetime.date.today().isoformat()})
    verdicts_path(source_id).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"accepted {len(hits)}: {figure}")
    return 0


def status(source_id: str) -> dict:
    """Crops in the current trees and their verdicts: counts plus the bad and unjudged ones."""
    from system.rag.checks import current_trees

    v = load_verdicts(source_id)["verdicts"]
    res = {"crops": 0, "ok": 0, "bad": [], "unjudged": []}
    for tree in current_trees(source_id):
        for s in figures(tree):
            crop = ROOT / s["image_path"]
            if not crop.exists():
                continue
            res["crops"] += 1
            key = _sha(crop)[:16]
            got = v.get(key)
            if not got:
                res["unjudged"].append(f"{tree['version_id']} {s['id']}")
            elif got["verdict"] in BAD:
                res["bad"].append(f"{tree['version_id'][:40]} {s['id']} p{got['page']}: {got['verdict']}: {got['problem']}")
            else:
                res["ok"] += 1
    return res


def report(source_ids: list[str] | None) -> int:
    ids = source_ids or sorted(p.stem for p in (CORPUS_DIR / "cropchecks").glob("*.json"))
    for sid in ids:
        r = status(sid)
        print(f"{sid}: {r['crops']} crops, {r['ok']} ok, {len(r['bad'])} bad, {len(r['unjudged'])} not judged")
        for b in r["bad"]:
            print("   ", b)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--source", required=True)
    e.add_argument("--all", action="store_true", help="also crops already judged")
    s = sub.add_parser("save")
    s.add_argument("--source", required=True)
    s.add_argument("--answers", required=True, type=Path)
    s.add_argument("--by", required=True)
    c = sub.add_parser("accept", help="keep a crop the model called bad, with the reason")
    c.add_argument("--source", required=True)
    c.add_argument("--figure", required=True)
    c.add_argument("--reason", required=True)
    c.add_argument("--by", required=True)
    r = sub.add_parser("report")
    r.add_argument("--source", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "export":
        return export(a.source, all_=a.all)
    if a.cmd == "accept":
        return accept(a.source, a.figure, a.reason, a.by)
    if a.cmd == "save":
        return save(a.source, a.answers, a.by)
    return report(a.source)


if __name__ == "__main__":
    sys.exit(main())
