"""Parse the Home Office fire safety booklets of 2023-2024 into document trees.

    python -m system.rag.parse_booklet --source fso-guidance-collection

Design: architecture/design/ingest/design.md, ADR 0010. Four files of fso-guidance-collection share one
template: "Check your fire safety responsibilities under Section 156 of the Building Safety Act 2022", "... under
the Fire Safety (England) Regulations 2022", "A Guide to making your small block of flats safe from fire" and
"... small paying-guest-accommodation safe from fire".

- A cover and a licence page, Contents, then chapters with a 35pt title ("1. Introduction", "Duties of the
  Responsible Person (general)"). A running header (8pt) and a repeat of the chapter title (12pt, magenta) at the
  top of each page are dropped; the page number is read from the header.
- Two columns of Helvetica Neue Light 12pt. A chapter opens with a lead paragraph in 14pt Medium.
- Headings in 16pt Bold, sub-headings in 15pt, and short bold 12pt lines (also naming the photo below them).
- Callouts: 14pt regular text on a drawn shape ("You have a responsibility to make sure ...") are boxes.
- Figures with a caption above ("Figure 5 – Internal flat layout", or just "Figure 1"), photos without one.
- Footnotes in 11pt at the foot of the page, cited by raised numbers.
- The checklist chapters are forms: the questions are kept as paragraphs, the "Yes", "No" and "N/A" boxes dropped.

Ids are "<booklet>:<local id>" ("small-flats:5-fire-safety-measures-compartmentation-para-2"), unique across the
source. The builder reuses parse_flats (figures below captions, pictures without a caption, lists, footnotes) and
parse_guide (reading order of two columns).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter

from system.rag.corpus import CORPUS_DIR, slugify
from system.rag.fixes import index, load_fixes
from system.rag.parse_flats import FlatsBuilder, drop_blank_pictures, join_line
from system.rag.parse_guide import _inside, _x1, guide_title, records, read_guide, short_slug, split_wide
from system.rag.parse_pdf import BULLET_RE, _join_all, _segment, render_images

PARSER = "home-office-booklet-pdf/0.1"
MODULE = "parse_booklet"
# Short names for the ids, by version id prefix (corpus/versions/fso-guidance-collection).
SLUGS = {
    "check-your-fire-safety-responsibilities-under-sect--": "bsa-section-156",
    "check-your-fire-safety-responsibilities-under-the--": "fire-safety-england-regs",
    "making-your-small-block-of-flats-safe-from-fire--": "small-flats",
    "making-your-small-paying-guest-accommodation-safe--": "small-paying-guest",
}
TITLE_SIZE = 30.0              # chapter titles are 35pt
CAPTION_RE = re.compile(r"^Figure\s+(\d{1,2})(?:\s*[–-]\s*(.*))?$")
CHAPTER_RE = re.compile(r"^(\d{1,2})\.\s+(\S.*)$")
FORM_WORDS = {"Yes", "No", "N/A"}
MAGENTA = (0.9, 0.0, 0.49)


def slug_for(version_id: str) -> str | None:
    return next((s for p, s in SLUGS.items() if version_id.startswith(p)), None)


class BookletBuilder(FlatsBuilder):
    """The 2023-2024 booklet template. Own set-up and main loop; figures, pictures, lists and footnotes as in
    FlatsBuilder; the reading order of two columns from GuideBuilder._order."""

    MIN_PICTURE = (62, 62)  # the round icons beside "Smoking:", "Cooking:" (about 45pt) are decoration
    GROW_KEYS = True        # floor plans: labels and keys in small print round the drawing

    def __init__(self, doc: dict, meta: dict, fixes: list[dict] | None = None):  # noqa: D107 (own set-up)
        self.meta = meta
        self.fixes = index(fixes)
        self.doc_tables = doc.get("tables", [])
        self.page_width = doc.get("page_width") or 595.0
        self.page_height = doc.get("page_height") or 842.0
        self.pages = {int(k): v for k, v in (doc.get("pages") or {}).items()}
        self.title = guide_title(meta.get("title") or meta.get("source_id", ""))
        self.slug = meta.get("slug") or slug_for(meta.get("version_id", "")) or slugify(self.title)[:30]
        self.images = doc.get("images", [])
        self.graphics = [g for g in doc.get("graphics", []) if g["bottom"] > 0
                         and g["top"] < self.size_of(g["page"])[1]]
        self.page_count = doc.get("page_count") or max((l["page"] for l in doc["lines"]), default=0)
        self.sections, self.by_id, self.issues, self.checks = [], {}, [], []
        self.printed: dict[int, str] = {}
        self.markers: list = []
        self.claimed: set[int] = set()
        self.anchors: dict[int, list[dict]] = {}
        self._fills, self._objects, self._body_fonts = {}, {}, {}
        self.box_rects, self.boxes, self.figures = [], [], []
        self.definitions = []
        self.lines = self._clean(doc["lines"])
        self._metrics()
        self._callouts()
        self._captions()
        self._pictures()
        self._loose_tables()
        self._order()

    # -------------------------------------------------- set-up passes

    def _clean(self, lines: list[dict]) -> list[dict]:
        """Drop the running header (keep its page number), the magenta repeat of the chapter title, the cover and
        licence pages, and the boxes of the checklist forms."""
        out = []
        caps = {(l["page"], l["text"].strip().casefold()) for l in lines if not l["text"].strip().isupper()}
        for l in lines:
            t = l["text"].strip()
            if l["page"] <= 2 or not t:
                continue
            if t.isupper() and (l["page"], t.casefold()) in caps:
                continue  # a hidden capitals copy of a visible line (the sample fire action notice)
            if l["top"] > 790 and re.fullmatch(r"\d{1,3}", t):
                continue  # a page number printed inside a reproduced page
            if l["top"] < 55 and l["size"] <= 8.5:
                if re.fullmatch(r"\d{1,3}", t):
                    self.printed[l["page"]] = t
                continue
            ws = l.get("words") or []
            if l["top"] < 100 and ws and tuple(ws[0].get("c") or ()) == MAGENTA:
                continue
            for part in self._split_labels(split_wide(l)):
                words = [w for w in part.get("words") or [] if w["text"] not in FORM_WORDS]
                if not words:
                    continue  # "Yes", "No", "N/A" beside a question in a checklist
                if len(words) < len(part["words"]):
                    part = {**part, "words": words, "text": " ".join(w["text"] for w in words)}
                out.append(part)
        return out

    @staticmethod
    def _split_labels(parts: list[dict]) -> list[dict]:
        """Labels of two drawings side by side read as one line ("2 2", "1 Stair 1 Stair"): cut small print at
        gaps wider than 40 points (split_wide keeps a number with the words after it)."""
        out = []
        for l in parts:
            ws = l.get("words") or []
            if l["size"] >= 11 or len(ws) < 2:
                out.append(l)
                continue
            start = 0
            for k in range(1, len(ws)):
                if ws[k]["x0"] - ws[k - 1].get("x1", ws[k - 1]["x0"]) > 40:
                    out.append(_segment(l, ws[start:k]))
                    start = k
            out.append(_segment(l, ws[start:]) if start else l)
        return out

    def tab_x(self, page: int) -> float:
        return self.size_of(page)[0] - 25  # no side tab

    def _callouts(self) -> None:
        """Callouts: 14pt regular (not Medium) lines, close together, set on a drawn shape: one box each."""
        run: list[dict] = []

        def flush():
            if run:
                text = _join_all(x["text"].strip() for x in run)
                rect = {"page": run[0]["page"], "top": run[0]["top"], "bottom": run[-1]["top"] + run[-1]["size"],
                        "x0": min(x["x0"] for x in run), "x1": max(_x1(x) for x in run)}
                block = {"kind": "box", "title": None, "text": text, "page": run[0]["page"], "box": rect}
                self.boxes.append(block)
                self.claimed.update(id(x) for x in run)
                self.anchors.setdefault(id(run[0]), []).append(block)
            run.clear()

        for l in sorted(self.lines, key=lambda l: (l["page"], l["x0"] > 300, l["top"])):
            callout = 13.5 <= l["size"] <= 14.5 and l["font"].split("-")[-1] in ("HelveticaNeue", "Roman") \
                and "Medium" not in l["font"] and "Bold" not in l["font"]
            if callout and run and run[-1]["page"] == l["page"] and 0 < l["top"] - run[-1]["top"] < 1.6 * l["size"] \
                    and abs(l["x0"] - run[-1]["x0"]) < 30:
                run.append(l)
            elif callout:
                flush()
                run.append(l)
            else:
                continue
        flush()

    def _captions(self) -> None:
        """Figure captions in bold 12pt above the picture: "Figure 5 – Internal flat layout" or "Figure 1"."""
        for l in self.lines:
            m = CAPTION_RE.match(l["text"].strip())
            if not m or id(l) in self.claimed or not self.heavy_line(l):
                continue
            cap = {"page": l["page"], "top": l["top"], "bottom": l["top"] + l["size"] + 1, "x0": l["x0"], "x1": _x1(l)}
            self.claimed.add(id(l))
            block = {"kind": "figure", "number": m.group(1), "caption_box": cap, "page": l["page"],
                     "title": (m.group(2) or "").strip(), "caption_above": True}
            self.figures.append(block)
            self.anchors.setdefault(id(l), []).append(block)
        for block in self.figures:
            self._figure_below(block)

    def column(self, page: int, top: float, bottom: float, x0: float, x1: float) -> tuple[float, float]:
        """A figure takes the page width, unless running text sits in the other column just below its caption:
        then it keeps to its own column."""
        w, _ = self.size_of(page)
        mid = w * 0.53
        beside = [l for l in self.lines if l["page"] == page and id(l) not in self.claimed and self.body_line(l)
                  and top + 15 <= l["top"] <= top + 95 and ((l["x0"] >= mid - 20) != (x0 >= mid - 20))]
        if not beside:
            return 40.0, w - 30.0
        return (40.0, mid - 6) if x0 < mid - 20 else (mid - 20, w - 30.0)

    # -------------------------------------------------- the main pass

    def build(self) -> dict:
        mode = "content"
        chapter = h2 = h3 = h4 = None
        para = last = None
        counts: Counter = Counter()
        self.footnotes: list[tuple[int, str, str]] = []
        last_note = -1

        def parent():
            return h4 or h3 or h2 or chapter

        def heading(level: int, title: str, page: int) -> dict:
            host = {2: chapter, 3: h2 or chapter, 4: h3 or h2 or chapter}[level] or self._doc_for(page)
            anchor = chapter or host
            return self.sec(f"{self.local(anchor)}-{short_slug(title, 4)}", "heading", host, None, title,
                            [*host["heading_path"], title], page)

        i = 0
        while i < len(self.lines):
            l = self.lines[i]
            i += 1
            t = l["text"].strip()
            if l["size"] >= TITLE_SIZE and id(l) not in self.claimed:
                parts, prev = [t], l
                while i < len(self.lines) and self.lines[i]["page"] == l["page"] \
                        and self.lines[i]["size"] >= TITLE_SIZE and 0 < self.lines[i]["top"] - prev["top"] < 1.6 * l["size"]:
                    prev = self.lines[i]
                    parts.append(prev["text"].strip())
                    i += 1
                title = " ".join(parts)
                para = h2 = h3 = h4 = None
                if title == "Contents":
                    mode = "skip"
                    continue
                mode = "content"
                m = CHAPTER_RE.match(title)
                chapter = self.sec(f"{m.group(1)}-{short_slug(m.group(2), 3)}" if m else short_slug(title, 4),
                                   "chapter", None, m.group(1) if m else None, m.group(2) if m else title,
                                   [self.title, title], l["page"])
                continue
            if mode == "skip":
                continue
            for b in self.anchors.get(id(l), []):
                self.place(b, parent() or self._doc_for(l["page"]))
            if id(l) in self.claimed:
                continue
            heavy = self.heavy_line(l)
            # ---- headings: 16pt bold, 15pt regular, short bold 12pt lines (wrapped lines merged)
            level = 2 if heavy and 15.5 <= l["size"] < TITLE_SIZE else 3 if 14.6 <= l["size"] < 15.5 and not heavy \
                else 4 if heavy and 11.5 <= l["size"] <= 12.5 and not BULLET_RE.match(t) else None
            if level:
                group, j = [l], i
                while j < len(self.lines) and self.lines[j]["page"] == l["page"] and id(self.lines[j]) not in self.claimed \
                        and self.lines[j]["font"] == l["font"] and abs(self.lines[j]["size"] - l["size"]) < 0.3 \
                        and 0 < self.lines[j]["top"] - group[-1]["top"] < 1.6 * l["size"]:
                    group.append(self.lines[j])
                    j += 1
                title = _join_all(x["text"].strip() for x in group)
                if not title.endswith((".", ",", ";")) and len(title.split()) <= (25 if level < 4 else 16):
                    i = j
                    sec = heading(level, title, l["page"])
                    if level == 2:
                        h2, h3, h4 = sec, None, None
                    elif level == 3:
                        h3, h4 = sec, None
                    else:
                        h4 = sec
                    para = None
                    continue
            # ---- footnotes: 11pt at the foot of the page
            if 10.5 <= l["size"] <= 11.5 and l["top"] > 640:
                m = re.match(r"^(\d{1,2})\s+(.*)$", t)
                if m:
                    self.footnotes.append((l["page"], m.group(1).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")),
                                           m.group(2)))
                elif self.footnotes and self.footnotes[-1][0] == l["page"] and last_note == i - 1:
                    p, mark, text = self.footnotes[-1]
                    self.footnotes[-1] = (p, mark, f"{text}{'' if text.endswith(('/', '-', '_')) else ' '}{t}")
                else:
                    self.footnotes.append((l["page"], "", t))
                last_note = i
                continue
            # ---- running text: one section per paragraph
            host = parent() or self._doc_for(l["page"])
            form = bool(chapter) and bool(re.search(r"checklist|template", chapter["title"] or "", re.I))
            short = form and len(t.split()) <= 5 and not BULLET_RE.match(t) and l["size"] < 13
            if para is not None and para["parent_id"] == host["id"] and short and para.get("_short") \
                    and last["page"] == l["page"] and 0 < l["top"] - last["top"] < 2.6 * l["size"]:
                para["text"] += "\n" + t  # the options of a form, one per line ("Brick slips", "Glass")
            elif para is not None and para["parent_id"] == host["id"] and self._goes_on(para, last, l):
                para["text"] = join_line(para["text"], t)
                para["_short"] = False
            else:
                counts[host["id"]] += 1
                para = self.sec(f"{self.local(host)}-para-{counts[host['id']]}", "paragraph", host, None, None,
                                list(host["heading_path"]), l["page"], join_line("", t))
                para["_short"] = short
            last = l
        for s in self.sections:
            s.pop("_short", None)
        self._attach_notes()
        self.attach_grids()
        for s in self.sections:
            if s["type"] in ("table", "figure") and not self.apply_fix(s):
                self.checks.append({
                    "kind": s["type"], "section_id": s["id"], "file_page": s["file_page"],
                    "key": self.check_key(s), "area": s.get("area"), "spans": s.get("spans"),
                    "question": ("Check this table's rows and columns against the page image and write one "
                                 "sentence per row." if s["type"] == "table" else
                                 "Describe this figure in two or three plain sentences for search."),
                })
        return {
            **{k: self.meta.get(k) for k in ("source_id", "version_id", "valid_from", "valid_to", "sha256")},
            "title": self.title, "parser": PARSER, "page_width": self.page_width,
            "sections": self.sections, "definitions": [], "issues": self.issues, "checks": self.checks,
        }

    def _doc_for(self, page: int) -> dict:
        sid = f"{self.slug}:document"
        return self.by_id.get(sid) or self.sec("document", "chapter", None, None, self.title, [self.title], page)


def build_tree(doc: dict, meta: dict, fixes: list[dict] | None = None) -> dict:
    return BookletBuilder(doc, meta, fixes).build()


# ---------------------------------------------------------------- command line

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    a = ap.parse_args(argv)
    import yaml

    doc = yaml.safe_load((CORPUS_DIR / "sources.yaml").read_text(encoding="utf-8"))
    src = next((s for s in doc["sources"] if s["id"] == a.source), None)
    root = CORPUS_DIR.parent
    fixes = load_fixes(a.source)
    todo = records(a.source, src, MODULE)
    if not todo:
        print(f"no files of {a.source} go to {MODULE} (sources.yaml parser.files)")
    for r in todo:
        raw = root / r["raw_path"]
        if not raw.exists():
            print(f"missing raw file: {r['raw_path']}")
            continue
        tree = build_tree(read_guide(raw), {**r, "title": r.get("part_title") or a.source}, fixes=fixes)
        out = CORPUS_DIR / "parsed" / a.source / f"{r['version_id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        drop_blank_pictures(raw, tree)
        render_images(raw, tree, out.parent / r["version_id"])
        out.write_text(json.dumps(tree, ensure_ascii=False, indent=1), encoding="utf-8")
        types = Counter(s["type"] for s in tree["sections"])
        print(f"{r['version_id']}: {dict(types)}, {len(tree['issues'])} issues, {len(tree['checks'])} model checks "
              f"-> {out.relative_to(root)}")
        for x in tree["issues"]:
            print(f"  issue: {x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
