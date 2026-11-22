"""Parse the Home Office "Fire safety risk assessment" guides (2006 series) into document trees.

    python -m system.rag.parse_guide --source fso-guidance-collection

Design: architecture/design/regulations-corpus.md, ADR 0010. The guides share one template, unlike the HSE guides
that parse_pdf reads (numbered paragraphs, captions below photos):

- Parts ("Part 1 Fire risk assessment"), then Steps (Part 1, a white "STEP 1 ..." banner) or Sections (Part 2,
  "Section 1 ..."), appendices, references and an index. Titles are set large (16pt and up).
- Numbered headings ("1.3 Dangerous substances: storage, display and use", "3.4.1 ...", "B1 ...") in bold, and
  sub-headings without a number in bold at body size ("Voids", "Flammable liquids"). Styles are told apart by
  role (size, weight, colour, typeface against the body text), not by font name: the guides use different fonts.
- Body text in one column (Part 1, Helvetica) or two (Part 2, Garamond); no paragraph numbers. One paragraph
  section per real paragraph, under the lowest heading, with the full heading path.
- "Case study" (and, in the disabled people guide, "Example") boxes on a shaded rectangle.
- Figure and table captions ("Figure 14: An example of poor storage") in italics, ABOVE the picture in Part 2
  and BELOW it in Part 1. The picture is found from what is drawn next to the caption: its frame, image or the
  drawing's lines. Photos are cut to their own pixels when the page is rendered (parse_pdf.photo_box).
- A side tab ("Part 2 • Further guidance ...") and page numbers are dropped; raised footnote numbers are kept as
  superscripts ("Order¹") and the footnotes go to the paragraph that cites them.

Section ids are unique across the whole source (many guides share it): "<guide>:<local id>", for example
"offices-shops:1-3-dangerous-substances-para-2". The tree format is parse_pdf's, so chunk.py and checks.py work
unchanged. Which files this parser takes is set in corpus/sources.yaml (parser.files).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter

from system.rag.corpus import CORPUS_DIR, parser_for, slugify
from system.rag.fixes import index, load_fixes
from system.rag.parse_pdf import (
    BULLET_RE, Builder, _is_bold, _is_bullet_word, _join, _join_all, _segment, normalise_bullet, read_pdf,
    render_images,
)

PARSER = "fire-risk-guide-pdf/0.1"
MODULE = "parse_guide"
TITLE_SIZE = 15.5  # Part, Section, Appendix and front-matter titles are 16pt and up; headings at most 13pt
CAPTION_RE = re.compile(r"^(Figure|Table)\s*(\d{1,3}[a-z]?)\s*[:.]?\s*(.*)$")
NUM_HEAD_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,3})\.?\s+(\S.*)$")      # "1.3 Dangerous ...", "3.4.1 ..."
APP_HEAD_RE = re.compile(r"^([A-H])\.?(\d{1,2}(?:\.\d{1,2}){0,2})\s+(\S.*)$")  # "B1 Fire-resisting ...", "A.1 ..."
STEP_RE = re.compile(r"^STEP\s+(\d)\b\s*[:\-–]?\s*(.*)$", re.I)
PART_RE = re.compile(r"^Part\s+(\d+)\b\s*[:\-–]?\s*(.*)$")
SECTION_RE = re.compile(r"^Section\s+(\d+)\b\s*[:\-–]?\s*(.*)$")
APPENDIX_RE = re.compile(r"^Appendix\s+([A-H]|\d{1,2})\b\s*[:\-–]?\s*(.*)$")
CHAPTER_NUM_RE = re.compile(r"^(\d{1,2})\s+([A-Z].*)$")                      # "1 Background" (disabled people guide)
BOX_TITLES = ("case study", "example")
BOX_HEAD_RE = re.compile(r"^(Case study|Example)(\s+\d+)?:?$", re.I)
SKIP_TITLES = {"contents", "index"}
BACK_MATTER = {"references": "references", "further reading": "back-matter"}
SENTENCE_END = re.compile(r"[.!?:]['’”)]?$|\.\)$")
STOP_WORDS = {"and", "of", "for", "the", "a", "in", "on", "to"}
WHITE = {(1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 0.0)}


# ---------------------------------------------------------------- small helpers

def guide_slug(title: str) -> str:
    """A short, stable name for a guide from its title: "Fire safety risk assessment: offices and shops" ->
    "offices-shops". Words like "and" and "of" and any bracketed note are left out."""
    t = re.sub(r"\(.*?\)", "", title.split(":", 1)[-1])
    words = [w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in STOP_WORDS]
    return "-".join(words) or slugify(title)


def guide_title(title: str) -> str:
    """The guide's title without a bracketed note ("(single document, including appendices)")."""
    return re.sub(r"\s*\(.*?\)\s*$", "", title).strip()


def short_slug(text: str, words: int = 5) -> str:
    """The first few words of a heading as an id part: "Dangerous substances: storage, display and use" ->
    "dangerous-substances-storage-display"."""
    ws = re.findall(r"[a-z0-9]+", text.lower())[:words]
    return "-".join(ws) or "untitled"


def is_heavy(font: str) -> bool:
    """Bold or medium weight (headings use both: "3.4.1 ..." is set in a medium weight)."""
    return _is_bold(font) or "Medium" in font or bool(re.search(r"-Md(Cn|It)?$", font))


def is_italic(font: str) -> bool:
    return "Italic" in font or "Oblique" in font or bool(re.search(r"-(Lt|Bd|Md)?(It|Ita|O)$", font))


def family(font: str) -> str:
    return font.split("-")[0]


def split_wide(l: dict) -> list[dict]:
    """Cut a line at wide gaps between words. pdfplumber joins words at the same height across columns, and
    beside a figure ("... the oxygen supplies that will    Figure 2: The fire triangle"). Not after a bullet
    or a heading number ("1.1      Identify sources of ignition")."""
    ws = l.get("words") or []
    parts, start = [], 0
    for k in range(1, len(ws)):
        a, b = ws[k - 1], ws[k]
        gap = b["x0"] - a.get("x1", a["x0"])
        back = b["x0"] < a["x0"] - 1  # the text jumps back left: the next column's words
        if not back and (gap < max(14.0, 1.6 * b.get("s", l["size"])) or _is_bullet_word(a, l["font"])):
            continue
        if not back and k - start == 1 and re.fullmatch(r"([A-H]\.?)?\d{1,2}(\.\d{1,2}){0,3}\.?", a["text"]):
            continue
        parts.append(ws[start:k])
        start = k
    if not parts:
        return [l]
    parts.append(ws[start:])
    return [normalise_bullet(_segment(l, p)) for p in parts]


def _x1(l: dict) -> float:
    ws = l.get("words") or []
    return max((w.get("x1", w["x0"]) for w in ws), default=l["x0"] + 5 * len(l["text"]))


def _inside(l: dict, box: dict, pad: float = 2.0) -> bool:
    """The line's middle lies inside the box (same page)."""
    if l["page"] != box["page"]:
        return False
    cx, cy = (l["x0"] + _x1(l)) / 2, l["top"] + l["size"] / 2
    return box["x0"] - pad <= cx <= box["x1"] + pad and box["top"] - pad <= cy <= box["bottom"] + pad


def _union(boxes: list[dict]) -> dict:
    return {"page": boxes[0]["page"], "top": min(b["top"] for b in boxes), "bottom": max(b["bottom"] for b in boxes),
            "x0": min(b["x0"] for b in boxes), "x1": max(b["x1"] for b in boxes)}


def _touches(a: dict, b: dict, gap: float) -> bool:
    return a["x0"] - gap <= b["x1"] and b["x0"] - gap <= a["x1"] and a["top"] - gap <= b["bottom"] \
        and b["top"] - gap <= a["bottom"]


# ---------------------------------------------------------------- the builder

class GuideBuilder(Builder):
    """Builds the tree from read_pdf data (lines, images, ruled tables, graphics). Reuses parse_pdf's Builder for
    sections, grids from ruled tables, saved model fixes and check keys; the layout rules are its own."""

    def __init__(self, doc: dict, meta: dict, fixes: list[dict] | None = None):  # noqa: D107 (own set-up)
        self.meta = meta
        self.fixes = index(fixes)
        self.doc_tables = doc.get("tables", [])
        self.page_width = doc.get("page_width") or 595.0
        self.page_height = doc.get("page_height") or 842.0
        self.pages = {int(k): v for k, v in (doc.get("pages") or {}).items()}
        self.title = guide_title(meta.get("title") or meta.get("source_id", ""))
        self.slug = meta.get("slug") or guide_slug(self.title)
        self.images = doc.get("images", [])
        # Drawings can have hidden copies placed off the page (sleeping accommodation, page 83).
        self.graphics = [g for g in doc.get("graphics", []) if g["bottom"] > 0
                         and g["top"] < self.size_of(g["page"])[1]]
        self.page_count = doc.get("page_count") or max((l["page"] for l in doc["lines"]), default=0)
        self.sections: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self.issues: list[str] = []
        self.checks: list[dict] = []
        self.printed: dict[int, str] = {}
        self.markers: list = []  # parse_pdf's margin labels (L143); none here
        self.claimed: set[int] = set()       # ids of lines that belong to a figure, table or box
        self.anchors: dict[int, list[dict]] = {}  # line id -> blocks to place there in the reading order
        self._fills: dict[int, list[dict]] = {}
        self._objects: dict[int, list[dict]] = {}
        self._body_fonts: dict[int, str] = {}
        self.lines = self._clean(doc["lines"])
        self._metrics()
        self._boxes()
        self._captions()
        self._loose_tables()
        self._diagrams()
        self._order()

    # -------------------------------------------------- page geometry

    def size_of(self, page: int) -> tuple[float, float]:
        p = self.pages.get(page) or {}
        return p.get("width", self.page_width), p.get("height", self.page_height)

    def tab_x(self, page: int) -> float:
        """Where the side tab starts: a tall shaded strip at the right edge of the page, or near the edge."""
        w, h = self.size_of(page)
        xs = [g["x0"] for g in self.graphics if g["page"] == page and g["fill"] and g["x0"] > 0.85 * w
              and g["bottom"] - g["top"] > 0.7 * h]
        return min(xs, default=w - 40)

    # -------------------------------------------------- set-up passes

    def _clean(self, lines: list[dict]) -> list[dict]:
        """Drop the side tab and page numbers (remember the printed page number); cut lines at wide gaps."""
        out = []
        tabs = {p: self.tab_x(p) for p in {l["page"] for l in lines}}
        for l in lines:
            w, h = self.size_of(l["page"])
            t = l["text"].strip()
            if abs(w - self.page_width) > 0.2 * self.page_width or l["top"] < 0 or l["top"] > h:
                continue  # a cover printed as a two-page spread; text placed off the page
            if l["x0"] >= tabs[l["page"]] - 2 or l["x0"] > w or not t:
                if re.fullmatch(r"\d{1,3}", t):
                    self.printed[l["page"]] = t
                continue
            if l["top"] > h - 70 and re.fullmatch(r"\d{1,3}", t) and l["size"] <= 10:
                self.printed[l["page"]] = t
                continue
            if re.search(r"\.indd\s+\d+\s+\d{2}/\d{2}/\d{4}", t):  # printer's slug on the cover pages
                continue
            out.extend(split_wide(l))
        return out

    def _metrics(self) -> None:
        """Body size per page (Part 1 is set in 11pt, Part 2 in 10pt), the body colour, and the body typeface."""
        per: dict[int, Counter] = {}
        sizes, colours, fonts = Counter(), Counter(), Counter()
        for l in self.lines:
            if len(l["text"].split()) >= 5:
                per.setdefault(l["page"], Counter())[l["size"]] += len(l["text"])
                sizes[l["size"]] += len(l["text"])
        self.body_size = sizes.most_common(1)[0][0] if sizes else 10.0
        self.page_body = {p: c.most_common(1)[0][0] for p, c in per.items()}
        for l in self.lines:
            if l["size"] == self.pb(l):
                for w in l.get("words") or []:
                    colours[tuple(w.get("c") or ())] += len(w["text"])
                fonts[family(l["font"])] += len(l["text"])
        self.body_colour = colours.most_common(1)[0][0] if colours else ()
        self.body_left = 0
        self.page_left = {}

    def pb(self, l: dict) -> float:
        """Body size on this line's page."""
        return self.page_body.get(l["page"], self.body_size)

    def coloured(self, l: dict) -> bool:
        ws = l.get("words") or []
        c = tuple(ws[0].get("c") or ()) if ws else ()
        return c != self.body_colour and c not in WHITE and c != ()

    def heavy_line(self, l: dict) -> bool:
        ws = l.get("words") or []
        return bool(ws) and all(is_heavy(w.get("f") or l["font"]) for w in ws if not _is_bullet_word(w))

    def is_caption(self, l: dict) -> bool:
        return bool(CAPTION_RE.match(l["text"].strip())) and (is_italic(l["font"]) or l["size"] < self.pb(l) - 0.4)

    def fills(self, page: int) -> list[dict]:
        """Shaded rectangles on a page (not white, not the side tab)."""
        if page not in self._fills:
            w, _ = self.size_of(page)
            self._fills[page] = [g for g in self.graphics if g["page"] == page and g["fill"] and g["kind"] != "line"
                                 and g["colour"] not in (None, *WHITE) and g["x1"] - g["x0"] < 0.9 * w
                                 and g["x0"] < self.tab_x(page) - 2]
        return self._fills[page]

    def running(self, l: dict) -> bool:
        """Running text: body size and typeface, a full line of words, dark on white (not text printed in a
        diagram's coloured boxes)."""
        ws = l.get("words") or []
        if abs(l["size"] - self.pb(l)) > 1 or family(l["font"]) != family(self.body_font_on(l["page"])) \
                or len(ws) < 6 or tuple(ws[0].get("c") or ()) in WHITE or is_italic(l["font"]):
            return False
        return not any(_inside(l, g, -1) for g in self.fills(l["page"]))

    def objects(self, page: int) -> list[dict]:
        """What is drawn on a page (images, rectangles, lines, curves), without the side tab, page-size
        backgrounds, specks and the rectangles of boxes."""
        if page in self._objects:
            return self._objects[page]
        w, h = self.size_of(page)
        tab = self.tab_x(page)
        out = []
        for g in [*({**im, "kind": "image", "fill": True, "stroke": False, "colour": None} for im in self.images), *self.graphics]:
            if g["page"] != page or (g["x1"] - g["x0"] < 2 and g["bottom"] - g["top"] < 2):
                continue
            if g["x0"] >= tab - 2 or g["bottom"] - g["top"] > 0.85 * h:  # the side tab, page-high strips
                continue
            if g["top"] < -1 or g["bottom"] > h + 1 or g["x0"] < -1 or g["x1"] > w + 1:  # runs off the page
                continue
            if any(_touches(g, b, -1) and b["x0"] - 2 <= g["x0"] and g["x1"] <= b["x1"] + 2 and b["top"] - 2 <= g["top"]
                   and g["bottom"] <= b["bottom"] + 2 for b in self.box_rects if b["page"] == page):
                continue
            out.append(g)
        self._objects[page] = out
        return out

    def _boxes(self) -> None:
        """Case study and Example boxes: a shaded rectangle whose first line is the box title. A box drawn some
        other way is found from its title line and the run of lines in the same small typeface below it."""
        self.box_rects: list[dict] = []
        self.boxes: list[dict] = []
        seen: set[int] = set()
        for g in self.graphics:
            if not g["fill"] or g["colour"] in (None, *WHITE) or g["x1"] - g["x0"] < 100 or g["bottom"] - g["top"] < 30:
                continue
            inside = sorted((l for l in self.lines if _inside(l, g, 1) and id(l) not in seen),
                            key=lambda l: (l["top"], l["x0"]))
            if not inside or inside[0]["text"].strip().lower().rstrip(":") not in BOX_TITLES:
                continue
            self.box_rects.append(g)
            self._add_box(inside, g)
            seen.update(id(l) for l in inside)
        for k, l in enumerate(self.lines):
            if id(l) in seen or l["text"].strip().lower() not in BOX_TITLES or l["size"] >= self.pb(l) \
                    and family(l["font"]) == family(self.body_font_on(l["page"])):
                continue
            run, prev = [l], l
            for x in self.lines[k + 1:]:
                if x["page"] != l["page"] or id(x) in seen:
                    continue
                if x["font"] == l["font"] and x["size"] == l["size"] and abs(x["x0"] - l["x0"]) <= 25 \
                        and 0 < x["top"] - prev["top"] <= 3 * l["size"]:
                    run.append(x)
                    prev = x
            if len(run) > 1:
                self._add_box(run, _union([{"page": x["page"], "top": x["top"], "bottom": x["top"] + x["size"],
                                            "x0": x["x0"], "x1": _x1(x)} for x in run]))
                seen.update(id(x) for x in run)

    def body_font_on(self, page: int) -> str:
        if page not in self._body_fonts:
            c = Counter()
            for l in self.lines:
                if l["page"] == page and len(l["text"].split()) >= 5:
                    c[l["font"]] += len(l["text"])
            self._body_fonts[page] = c.most_common(1)[0][0] if c else ""
        return self._body_fonts[page]

    def _add_box(self, lines: list[dict], rect: dict) -> None:
        title, body = lines[0], lines[1:]
        text, prev = "", None
        for x in body:
            if prev and x["top"] - prev["top"] > 1.6 * x["size"] and text and not BULLET_RE.match(x["text"]):
                text += "\n"
                text += x["text"]
            else:
                text = _join(text, x["text"]) if not text.endswith("\n") else text + x["text"]
            prev = x
        block = {"kind": "box", "title": title["text"].strip().rstrip(":"), "text": text, "page": title["page"],
                 "box": {k: rect[k] for k in ("page", "top", "bottom", "x0", "x1")}}
        self.boxes.append(block)
        self.claimed.update(id(x) for x in lines)
        self.anchors.setdefault(id(title), []).append(block)

    # -------------------------------------------------- figures and tables from their captions

    def _captions(self) -> None:
        self.figures: list[dict] = []
        k = 0
        while k < len(self.lines):
            l = self.lines[k]
            k += 1
            if id(l) in self.claimed or not self.is_caption(l):
                continue
            m = CAPTION_RE.match(l["text"].strip())
            cap_lines, prev = [l], l
            for x in self.lines[k:k + 6]:  # a caption may wrap onto a second or third line
                overlap = min(_x1(x), _x1(prev)) - max(x["x0"], prev["x0"])
                if x["page"] == l["page"] and x["font"] == l["font"] and abs(x["size"] - l["size"]) < 0.3 \
                        and overlap >= 0.5 * min(_x1(x) - x["x0"], _x1(prev) - prev["x0"]) \
                        and 0 < x["top"] - prev["top"] < 1.6 * l["size"] and id(x) not in self.claimed \
                        and not CAPTION_RE.match(x["text"].strip()):
                    cap_lines.append(x)
                    prev = x
            title = _join_all([m.group(3), *(x["text"].strip() for x in cap_lines[1:])]).strip()
            cap = {"page": l["page"], "top": l["top"], "bottom": prev["top"] + prev["size"] + 1,
                   "x0": min(x["x0"] for x in cap_lines), "x1": max(_x1(x) for x in cap_lines)}
            block = {"kind": m.group(1).lower(), "number": m.group(2), "title": title, "caption_box": cap,
                     "page": l["page"], "_line": id(l)}
            self.claimed.update(id(x) for x in cap_lines)
            if block["kind"] == "figure":
                self._figure_area(block)
            else:
                self._table_area(block)
            self.anchors.setdefault(id(l), []).append(block)
            self.figures.append(block)

    def _side(self, cap: dict, objs: list[dict], reach: float = 28.0) -> tuple[str | None, list[dict]]:
        """Is the picture below or above the caption? The side with something drawn closest to it, starting in
        the caption's column."""
        def column(o):
            return o["x0"] <= cap["x0"] + 40 and o["x1"] >= cap["x0"] + 10

        below = [o for o in objs if column(o) and cap["bottom"] - 3 <= o["top"] <= cap["bottom"] + reach]
        above = [o for o in objs if column(o) and cap["top"] - reach <= o["bottom"] <= cap["top"] + 3]
        db = min((o["top"] - cap["bottom"] for o in below), default=None)
        da = min((cap["top"] - o["bottom"] for o in above), default=None)
        if db is None and da is None:
            return None, []
        if da is None or (db is not None and db <= da):
            return "below", below
        return "above", above

    def _grow(self, seeds: list[dict], objs: list[dict], side: str, cap: dict, min_words: int = 6) -> dict:
        """Everything drawn that touches the seeds, on the caption's side, without crossing running text (lines
        of at least min_words words: table cells can run into each other)."""
        box = _union(seeds)
        on_side = [o for o in objs if (o["top"] >= cap["bottom"] - 3 if side == "below" else o["bottom"] <= cap["top"] + 3)]
        text = [l for l in self.lines if l["page"] == cap["page"] and (
            (id(l) not in self.claimed and self.running(l) and len(l["text"].split()) >= min_words)
            or (self.is_caption(l) and not _inside(l, cap, 1)))]  # nor another figure's caption
        changed = True
        while changed:
            changed = False
            for o in on_side:
                if o["x0"] >= box["x0"] - 0.5 and o["x1"] <= box["x1"] + 0.5 and o["top"] >= box["top"] - 0.5 \
                        and o["bottom"] <= box["bottom"] + 0.5:
                    continue
                if not _touches(o, box, 8.0):
                    continue
                grown = _union([box, o])
                if any(_inside(t, grown, -1) and not _inside(t, box, -1) for t in text):
                    continue  # would swallow running text: not part of this picture
                box = grown
                changed = True
        return box

    def _figure_area(self, f: dict) -> None:
        cap = f["caption_box"]
        objs = self.objects(cap["page"])
        side, seeds = self._side(cap, objs)
        if side is None:
            self.issues.append(f"figure {f['number']} (file page {cap['page']}): nothing drawn next to its caption")
            f["area"] = None
            return
        box = self._grow(seeds, objs, side, cap)
        f["caption_above"] = side == "below"
        frames = [o for o in objs if o["kind"] == "rect" and o["stroke"] and _touches(o, box, -1)
                  and o["x0"] <= box["x0"] + 1 and o["x1"] >= box["x1"] - 1 and o["top"] <= box["top"] + 1
                  and o["bottom"] >= box["bottom"] - 1]
        images = [o for o in objs if o["kind"] == "image" and _touches(o, box, 0)]
        if images and not frames:
            # A photo alone (nothing else drawn, no words): cut to its own pixels when rendered (photo_box), as
            # its image box can be padded. A drawing with a photo in it keeps the box of all its parts.
            img = _union(images)
            others = [o for o in objs if o["kind"] != "image" and _touches(o, box, -0.5)
                      and not (img["x0"] - 2 <= o["x0"] and o["x1"] <= img["x1"] + 2 and img["top"] - 2 <= o["top"]
                               and o["bottom"] <= img["bottom"] + 2)]
            words = [l for l in self.lines if id(l) not in self.claimed and _inside(l, box, 1)]
            if not others and not words:
                f["image_bbox"] = img
        pad = 1.5
        top, bottom = box["top"] - pad, box["bottom"] + pad
        if side == "below":  # never into the caption's letters
            top = max(top, cap["bottom"] + 0.5)
        else:
            bottom = min(bottom, cap["top"] - 0.5)
        f["area"] = {"page": box["page"], "top": round(top, 1), "bottom": round(bottom, 1),
                     "x0": round(box["x0"] - pad, 1), "x1": round(box["x1"] + pad, 1)}
        labels = [l for l in self.lines if id(l) not in self.claimed and _inside(l, box, 1)]
        f["labels"] = [l["text"] for l in sorted(labels, key=lambda l: (l["top"], l["x0"]))]
        self.claimed.update(id(l) for l in labels)

    def _table_area(self, t: dict) -> None:
        cap = t["caption_box"]
        ruled = [r for r in self.doc_tables if r["page"] == cap["page"]]
        side, near = self._side(cap, ruled, reach=40.0)
        t["caption_above"] = side != "above"
        if near:
            r = min(near, key=lambda r: abs(r["top"] - cap["bottom"]) if side == "below" else abs(cap["top"] - r["bottom"]))
            box = dict(r)
            inside = [l for l in self.lines if id(l) not in self.claimed and _inside(l, box, 2)]
            # Notes printed in small type just below the table belong to it ("Note 1: ...").
            last = box["bottom"]
            for l in sorted((l for l in self.lines if l["page"] == cap["page"] and id(l) not in self.claimed
                             and l["top"] > box["bottom"] - 2), key=lambda l: l["top"]):
                if l["top"] - last > 22 or l["size"] > self.pb(l) - 1.5 or not (box["x0"] - 5 <= l["x0"] <= box["x1"]):
                    break
                inside.append(l)
                last = l["top"] + l["size"]
            t["area"] = {"page": box["page"], "top": box["top"], "bottom": max(box["bottom"], last), "x0": box["x0"],
                         "x1": box["x1"]}
        else:
            # No ruled grid (rules across only, or shaded rows): what is drawn next to the caption and the short
            # lines among it, as for a figure.
            page_lines = [l for l in self.lines if l["page"] == cap["page"] and id(l) not in self.claimed]
            items = self.objects(cap["page"]) + [
                {"page": l["page"], "kind": "text", "top": l["top"], "bottom": l["top"] + l["size"], "x0": l["x0"],
                 "x1": _x1(l)} for l in page_lines if not self.heavy_line(l)
                or sum(abs(x["top"] - l["top"]) <= 1 for x in page_lines) > 1]  # header cells, not a heading
            side, seeds = self._side(cap, items)
            inside = []
            if side:
                t["caption_above"] = side == "below"
                box = self._grow(seeds, items, side, cap, min_words=8)
                inside = [l for l in page_lines if _inside(l, box, 2)]
                if inside:
                    t["area"] = box
        if t.get("area") is None and not near:
            # Nothing drawn: the lines below the caption in another style than the running text, up to the next
            # heading or running text.
            inside = []
            start = next(k for k, l in enumerate(self.lines) if id(l) == t["_line"])
            for l in self.lines[start + 1:]:
                if l["page"] != cap["page"] or id(l) in self.claimed:
                    continue
                if l["top"] < cap["bottom"] - 1 or not (cap["x0"] - 10 <= l["x0"]):
                    continue
                if (l["size"] == self.pb(l) and family(l["font"]) == family(self.body_font_on(l["page"]))) \
                        or self.heavy_line(l) and l["size"] >= self.pb(l):
                    break
                inside.append(l)
            if inside:
                t["area"] = _union([{"page": l["page"], "top": l["top"], "bottom": l["top"] + l["size"] + 2,
                                     "x0": l["x0"], "x1": _x1(l)} for l in inside])
            else:
                t["area"] = None
                self.issues.append(f"table {t['number']} (file page {cap['page']}): no rows found under its caption")
        inside.sort(key=lambda l: (l["top"], l["x0"]))
        t["text"] = "\n".join(l["text"] for l in inside)
        self.claimed.update(id(l) for l in inside)

    def _loose_tables(self) -> None:
        """Ruled tables with no caption (maintenance checklists, the glossary, record forms): a table section
        named after the heading above it. Grids inside figures or boxes, one-row grids and short one-column grids
        (a framed note) are not tables."""
        taken = [b.get("area") for b in self.figures if b.get("area")] + [b["box"] for b in self.boxes]
        for r in self.doc_tables:
            if len(r["rows"]) < 2 or (max(len(x) for x in r["rows"]) < 2 and len(r["rows"]) < 4):
                continue
            if any(a["page"] == r["page"] and _touches(a, r, -3) for a in taken):
                continue
            inside = sorted((l for l in self.lines if id(l) not in self.claimed and _inside(l, r, 2)),
                            key=lambda l: (l["top"], l["x0"]))
            if not inside:
                continue
            block = {"kind": "table", "number": None, "title": None, "page": r["page"],
                     "area": {k: r[k] for k in ("page", "top", "bottom", "x0", "x1")},
                     "text": "\n".join(l["text"] for l in inside), "loose": True}
            self.claimed.update(id(l) for l in inside)
            self.anchors.setdefault(id(inside[0]), []).append(block)
            self.figures.append(block)

    def _diagrams(self) -> None:
        """Drawings with no caption (a flow chart of rounded boxes: "Horizontal evacuation", "Refuge"): short bold
        lines set inside drawn shapes, at least three shapes close together (bold, since the PDFs also hold hidden
        drawings with plain labels). They become a figure with no number, so
        their labels are not read as headings or running text."""
        taken = [b["area"] for b in self.figures if b.get("area")] + [b["box"] for b in self.boxes]
        for page in sorted({l["page"] for l in self.lines}):
            w, h = self.size_of(page)
            shapes = [o for o in self.objects(page) if o["kind"] in ("rect", "curve")
                      and (o["x1"] - o["x0"]) * (o["bottom"] - o["top"]) < 0.25 * w * h
                      and o["x1"] - o["x0"] > 20 and o["bottom"] - o["top"] > 12
                      and not any(a["page"] == page and _touches(a, o, -1) for a in taken)]
            labelled = []
            for o in shapes:
                inside = [l for l in self.lines if l["page"] == page and id(l) not in self.claimed
                          and _inside(l, o, 1) and not self.running(l) and len(l["text"].split()) <= 8
                          and self.heavy_line(l) and not STEP_RE.match(l["text"].strip()) and l["size"] < TITLE_SIZE]
                if inside:
                    labelled.append((o, inside))
            groups: list[list[tuple[dict, list]]] = []
            for item in labelled:  # shapes within 45pt of each other are one drawing
                near = [g for g in groups if any(_touches(item[0], o, 45) for o, _ in g)]
                for g in near:
                    groups.remove(g)
                groups.append([item, *(x for g in near for x in g)])
            for grp in groups:
                if len(grp) < 3:
                    continue
                lines = sorted({id(l): l for _, ls in grp for l in ls}.values(), key=lambda l: (l["top"], l["x0"]))
                box = _union([o for o, _ in grp] + [
                    {"page": page, "top": l["top"], "bottom": l["top"] + l["size"], "x0": l["x0"], "x1": _x1(l)}
                    for l in lines])
                box = self._grow([box], [o for o in self.objects(page) if not any(
                    a["page"] == page and _touches(a, o, -1) for a in taken)], "below",
                    {"page": page, "top": box["top"] - 2, "bottom": box["top"] - 1, "x0": box["x0"], "x1": box["x1"]})
                lines = [l for l in self.lines if l["page"] == page and id(l) not in self.claimed and _inside(l, box, 1)
                         and not self.running(l)]
                pad = 1.5
                block = {"kind": "figure", "number": None, "title": None, "page": page,
                         "area": {"page": page, "top": round(box["top"] - pad, 1), "bottom": round(box["bottom"] + pad, 1),
                                  "x0": round(box["x0"] - pad, 1), "x1": round(box["x1"] + pad, 1)},
                         "labels": [l["text"] for l in lines]}
                block["caption_box"] = {"page": page, "top": block["area"]["top"], "bottom": block["area"]["top"],
                                        "x0": block["area"]["x0"], "x1": block["area"]["x1"]}
                self.claimed.update(id(l) for l in lines)
                self.anchors.setdefault(id(lines[0]), []).append(block)
                self.figures.append(block)
                taken.append(block["area"])

    def _order(self) -> None:
        """Reading order. Pages in two columns: the gutter is where at least three lines of running text start
        right of the middle; a line that crosses it is full width and starts a new band. Lines of figures, tables
        and boxes do not make bands."""
        pages: dict[int, list[dict]] = {}
        for l in self.lines:
            pages.setdefault(l["page"], []).append(l)
        out = []
        for page, ls in sorted(pages.items()):
            w, _ = self.size_of(page)
            free = [l for l in ls if id(l) not in self.claimed]
            starts = Counter(round(l["x0"] / 6) for l in free if 0.4 * w <= l["x0"] <= 0.7 * w
                             and l["size"] >= self.pb(l) - 1.5 and not BULLET_RE.match(l["text"]))
            gutter = None
            if starts:
                key, n = starts.most_common(1)[0]
                if n >= 3:
                    gutter = min(l["x0"] for l in free if round(l["x0"] / 6) in (key - 1, key, key + 1)
                                 or (BULLET_RE.match(l["text"]) and key * 6 - 30 <= l["x0"] <= key * 6))
            band = 0
            # Figures, tables and boxes set across both columns are a band of their own: the text above them is
            # read first, in both columns, then the block, then the text below.
            wide = [a for a in [*(b.get("area") for b in self.figures), *(b["box"] for b in self.boxes)]
                    if a and a["page"] == page and gutter is not None and a["x0"] < gutter - 8 < gutter + 8 < a["x1"]]
            current = None
            for l in sorted(ls, key=lambda l: (l["top"], l["x0"])):
                if gutter is None:
                    l["band"], l["col"] = 0, 0
                    continue
                area = next((a for a in wide if id(l) in self.claimed and _inside(l, a, 2)), None)
                if area is not None:
                    if area is not current:
                        band += 1
                        current = area
                    l["band"], l["col"] = band, 0
                    continue
                if current is not None:
                    band += 1
                    current = None
                crosses = l["x0"] < gutter - 8 and _x1(l) > gutter + 8
                if crosses and id(l) not in self.claimed:
                    band += 1
                    l["band"], l["col"] = band, 0
                    band += 1
                    continue
                l["band"], l["col"] = band, int(l["x0"] >= gutter - 8)
            out.extend(ls)
        self.lines = sorted(out, key=lambda l: (l["page"], l["band"], l["col"], l["top"], l["x0"]))

    # -------------------------------------------------- sections

    def sec(self, local: str, kind: str, parent: dict | None, number, title, path, page, text="") -> dict:
        sid = f"{self.slug}:{local}"
        base, n = sid, 1
        while sid in self.by_id:
            n += 1
            sid = f"{base}-{n}"
        return self.new(sid, kind, parent, number, title, path, page, text)

    def local(self, sec: dict | None) -> str:
        return sec["id"].split(":", 1)[1] if sec else "document"

    # -------------------------------------------------- the main pass

    def build(self) -> dict:
        mode = "skip"   # skip (cover, contents, index), content, back (references, further reading)
        part = chapter = None
        stack: list[tuple[int, dict]] = []   # open headings below the chapter: (level, section)
        para = None                          # the paragraph being filled
        last = None                          # its last line
        in_note = False                      # inside a footnote (small print at the foot of the page)
        counts: Counter = Counter()          # paragraphs per parent
        self.footnotes: list[tuple[int, str, str]] = []
        last_num: dict[str, list[int]] = {}

        def parent():
            return stack[-1][1] if stack else (chapter or part)

        def open_heading(level: int, sec: dict) -> None:
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, sec))

        i = 0
        while i < len(self.lines):
            l = self.lines[i]
            i += 1
            t = l["text"].strip()
            # ---- titles (Part, Section, Appendix, front and back matter), wrapped lines merged
            if l["size"] >= TITLE_SIZE and id(l) not in self.claimed and re.search(r"[A-Za-z]", t):
                parts, prev = [t], l
                while i < len(self.lines) and self.lines[i]["page"] == l["page"] \
                        and abs(self.lines[i]["size"] - l["size"]) < 0.5 and id(self.lines[i]) not in self.claimed \
                        and 0 < self.lines[i]["top"] - prev["top"] < 1.6 * l["size"]:
                    prev = self.lines[i]
                    parts.append(prev["text"].strip())
                    i += 1
                title = " ".join(parts)
                low = title.lower()
                para = None
                if low in SKIP_TITLES:
                    mode = "end" if low == "index" else "skip"  # nothing but the back cover after the index
                    continue
                if mode == "end":
                    continue
                if mode == "skip" and l["page"] <= 2:
                    continue  # the cover
                m_app_head = APP_HEAD_RE.match(title)
                if chapter and chapter["type"] == "appendix" and (m_app_head or not chapter["title"]) \
                        and not APPENDIX_RE.match(title):
                    if m_app_head and m_app_head.group(1) == chapter["number"]:
                        n = f"{m_app_head.group(1)}{m_app_head.group(2)}"
                        h = self.sec(f"appendix-{n.lower()}-{short_slug(m_app_head.group(3))}", "heading", chapter, n,
                                     m_app_head.group(3), [*chapter["heading_path"], f"{n} {m_app_head.group(3)}"],
                                     l["page"])
                        stack = [(3, h)]
                        continue
                    if not chapter["title"]:  # "Appendix B" on one line, its title below in another size
                        chapter["title"] = title
                        chapter["heading_path"][-1] = f"Appendix {chapter['number']} {title}"
                        continue
                stack = []
                mode = "content"
                if low in BACK_MATTER:
                    mode = "back"
                    part, chapter = None, self.sec(slugify(low), BACK_MATTER[low], None, None, title,
                                                   [self.title, title], l["page"])
                    continue
                m = PART_RE.match(title)
                if m:
                    part = self.sec(f"part-{m.group(1)}", "part", None, m.group(1), m.group(2) or title,
                                    [self.title, title], l["page"])
                    chapter = None
                    continue
                m = SECTION_RE.match(title)
                if m:
                    chapter = self.sec(f"section-{m.group(1)}", "chapter", part, m.group(1), m.group(2),
                                       [*(part["heading_path"] if part else [self.title]), title], l["page"])
                    continue
                m = APPENDIX_RE.match(title)
                if m:
                    part = None
                    chapter = self.sec(f"appendix-{m.group(1).lower()}", "appendix", None, m.group(1), m.group(2),
                                       [self.title, title], l["page"])
                    continue
                m = CHAPTER_NUM_RE.match(title)
                part = None
                chapter = self.sec(f"chapter-{m.group(1)}" if m else short_slug(title), "chapter", None,
                                   m.group(1) if m else None, m.group(2) if m else title, [self.title, title], l["page"])
                continue
            if mode in ("skip", "end"):
                continue
            # ---- figures, tables and boxes, placed where their caption or title is
            for b in self.anchors.get(id(l), []):
                self.place(b, parent() or self._doc(l))
            if id(l) in self.claimed:
                continue
            if mode == "back":
                chapter["text"] = "\n".join(x for x in [chapter["text"], t] if x)
                continue
            if chapter is None and part is None:
                chapter = self._doc(l)
            pbs = self.pb(l)
            # ---- Step banners in Part 1 ("STEP 1 IDENTIFYING FIRE HAZARDS")
            m = STEP_RE.match(t)
            if m and part and part["number"] == "1" and self.heavy_line(l) and l["size"] >= pbs + 0.5:
                rest = m.group(2).strip()
                title = f"Step {m.group(1)} {rest[:1].upper()}{rest[1:].lower()}".strip()
                chapter = self.sec(f"step-{m.group(1)}", "chapter", part, m.group(1), title,
                                   [*(part["heading_path"] if part else [self.title]), title], l["page"])
                stack, para = [], None
                continue
            # ---- headings: numbered, then un-numbered sub-headings (wrapped lines merged)
            if self.heavy_line(l) and l["size"] >= pbs - 0.6 and not BULLET_RE.match(t) and len(t.split()) <= 18:
                group, prev = [l], l
                j = i
                while j < len(self.lines) and self.lines[j]["page"] == l["page"] and id(self.lines[j]) not in self.claimed \
                        and self.lines[j]["font"] == l["font"] and abs(self.lines[j]["size"] - l["size"]) < 0.3 \
                        and 0 < self.lines[j]["top"] - prev["top"] < 1.6 * l["size"] \
                        and not NUM_HEAD_RE.match(self.lines[j]["text"].strip()) and self.heavy_line(self.lines[j]):
                    prev = self.lines[j]
                    group.append(prev)
                    j += 1
                title = _join_all(x["text"].strip() for x in group)
                m_num = NUM_HEAD_RE.match(title)
                m_app = APP_HEAD_RE.match(title) if chapter and chapter["type"] == "appendix" else None
                if m_app and m_app.group(1) != chapter["number"]:
                    m_app = None
                words = len(title.split())
                looks = not title.endswith((".", ",", ";", ":")) and not title[:1].islower()
                if looks and (m_num or m_app) and words <= 30:
                    i = j
                    if m_num:
                        n, rest = m_num.group(1), m_num.group(2)
                        level = 1 + n.count(".") + 1
                        lid = ("step-" if chapter and chapter["id"].split(":")[1].startswith("step-") else "") \
                            + f"{n.replace('.', '-')}-{short_slug(rest, 4)}"
                    else:
                        n, rest = f"{m_app.group(1)}{m_app.group(2)}", m_app.group(3)
                        level = 2 + m_app.group(2).count(".") + 1
                        lid = f"appendix-{n.lower().replace('.', '-')}-{short_slug(rest, 4)}"
                    self._check_number(n, last_num.setdefault(self.local(chapter or part), {}), l["page"])
                    par = None
                    for lev, s in reversed(stack):
                        if lev < level:
                            par = s
                            break
                    par = par or chapter or part
                    h = self.sec(lid, "heading", par, n, rest, [*par["heading_path"], f"{n} {rest}"], l["page"])
                    open_heading(level, h)
                    para = None
                    continue
                looks = looks and words <= 18
                if looks and BOX_HEAD_RE.match(title):
                    # "Example" set as a heading, its text below (the disabled people guide): a box
                    i = j
                    par = parent() or self._doc(l)
                    k = 1 + sum(1 for s in self.sections if s["parent_id"] == par["id"] and s["type"] == "box")
                    para = self.sec(f"{self.local(par)}-{slugify(title)}-{k}", "box", par, None, title,
                                    [*par["heading_path"], title], l["page"])
                    para["_box"], para["_bullet_x"], last = True, None, l
                    continue
                if looks and words <= 14 and not CAPTION_RE.match(title):
                    i = j
                    if l["size"] >= pbs + 2:
                        level = 3
                    else:
                        base = max((lev for lev, s in stack if s.get("number")), default=2)
                        rank = 0 if self.coloured(l) else (1 if family(l["font"]) != family(self.body_font_on(l["page"])) else 2)
                        level = base + 1 + rank
                    while stack and stack[-1][0] >= level:
                        stack.pop()
                    par = parent() or self._doc(l)
                    anchor = next((s for lev, s in reversed(stack) if s.get("number")), None) or chapter or part or par
                    h = self.sec(f"{self.local(anchor)}-{short_slug(title)}", "heading", par, None, title,
                                 [*par["heading_path"], title], l["page"])
                    open_heading(level, h)
                    para = None
                    continue
            # ---- footnotes: small print starting with a raised number, * or †
            if l["size"] <= min(7.5, pbs - 2) and re.match(r"^[⁰¹²³⁴⁵⁶⁷⁸⁹*†‡]", t):
                mark = re.match(r"^([⁰¹²³⁴⁵⁶⁷⁸⁹]+|[*†‡]+)", t).group(1)
                self.footnotes.append((l["page"], mark, t))
                in_note = True
                continue
            if in_note and l["size"] <= min(7.5, pbs - 2) and self.footnotes[-1][0] == l["page"]:
                p, mark, ft = self.footnotes[-1]  # a footnote wrapped onto the next line
                self.footnotes[-1] = (p, mark, f"{ft} {t}")
                continue
            in_note = False
            # ---- running text: one section per paragraph
            par = parent() or self._doc(l)
            bullet = bool(BULLET_RE.match(t))
            if para is not None and para.get("_box"):  # the text of a box set as a heading: all of it
                if not para["text"] or self._continues(para, last, l, bullet):
                    para["text"] = _join(para["text"], t)
                else:
                    para["text"] += "\n" + t
                para["_bullet_x"] = l["x0"] if bullet else para["_bullet_x"]
            elif para is not None and para["parent_id"] == par["id"] and self._continues(para, last, l, bullet):
                para["text"] = _join(para["text"], t)
                if bullet:
                    para["_bullet_x"] = l["x0"]
            else:
                counts[par["id"]] += 1
                para = self.sec(f"{self.local(par)}-para-{counts[par['id']]}", "paragraph", par, None, None,
                                list(par["heading_path"]), l["page"], _join("", t))
                para["_bullet_x"] = l["x0"] if bullet else None
                if l["size"] <= pbs - 1.5:
                    para["small_print"] = True
            last = l
        self._attach_footnotes()
        for s in self.sections:
            s.pop("_bullet_x", None)
            s.pop("_box", None)
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

    def _doc(self, l: dict) -> dict:
        """Text before any title (should not happen after the contents): one chapter named after the guide."""
        sid = f"{self.slug}:document"
        return self.by_id.get(sid) or self.sec("document", "chapter", None, None, self.title, [self.title], l["page"])

    def _check_number(self, n: str, last: dict, page: int) -> None:
        """Numbered headings go up by one within their parent number: "1.2" then "1.3". A jump is an issue
        (a heading the parser missed, or merged topics)."""
        head, _, tail = n.rpartition(".")
        if not head:
            m = re.match(r"^([A-H])(\d+)$", n)
            if not m:
                return
            head, tail = m.group(1), m.group(2)
        got = int(tail)
        prev = last.get(head, [0])[-1]
        if got not in (prev + 1, prev) and not (got == 1 and prev == 0):
            sep = "" if head.isalpha() else "."
            self.issues.append(f"heading numbers jump from {head}{sep}{prev} to {n} on file page {page}")
        last.setdefault(head, []).append(got)

    def _continues(self, para: dict, last: dict | None, l: dict, bullet: bool) -> bool:
        """Does this line go on with the paragraph being filled?"""
        if last is None:
            return False
        text = para["text"].rstrip()
        same_flow = last["page"] == l["page"] and last.get("band") == l.get("band") and last.get("col") == l.get("col")
        gap = l["top"] - last["top"] if same_flow else None
        spaced = gap is None or gap > 1.55 * max(l["size"], last["size"]) or gap < 0
        restyled = not bullet and not BULLET_RE.match(last["text"].strip()) and (
            abs(l["size"] - last["size"]) >= 1.5 or family(l["font"]) != family(last["font"]))
        if restyled and SENTENCE_END.search(text):
            return False
        if bullet:
            return text.endswith(":") or para.get("_bullet_x") is not None
        if para.get("_bullet_x") is not None:  # in a list: an indented line goes on with the item
            if not spaced and l["x0"] > para["_bullet_x"] + 3:
                return True
            if not SENTENCE_END.search(text) and not text.endswith(";"):
                return True
            para["_bullet_x"] = None
            return False
        if not SENTENCE_END.search(text):
            return True   # a sentence broken by a column, page or figure goes on
        return not spaced

    def place(self, b: dict, parent: dict) -> None:
        """A figure, table or box as a section under the current heading."""
        path = parent["heading_path"]
        if b["kind"] == "box":
            k = 1 + sum(1 for s in self.sections if s["parent_id"] == parent["id"] and s["type"] == "box")
            s = self.sec(f"{self.local(parent)}-{slugify(b['title'])}-{k}", "box", parent, None, b["title"],
                         [*path, b["title"]], b["page"], b["text"])
            s["box"] = b["box"]
            return
        kind, n = b["kind"], b["number"]
        if n is None and kind == "figure":  # a drawing without a caption
            k = 1 + sum(1 for s in self.sections if s["parent_id"] == parent["id"] and s["type"] == "figure"
                        and s["number"] is None)
            label = parent["title"] or self.title
            s = self.sec(f"{self.local(parent)}-figure-{k}", "figure", parent, None, label,
                         [*path, f"Figure ({label})"], b["page"])
            s["caption_box"] = b["caption_box"]
            s["drawn"] = True
        elif n is None:  # a ruled table without a caption
            k = 1 + sum(1 for s in self.sections if s["parent_id"] == parent["id"] and s["type"] == "table")
            label = parent["title"] or self.title
            s = self.sec(f"{self.local(parent)}-table-{k}", "table", parent, None, label, [*path, f"Table ({label})"],
                         b["page"], b["text"])
        else:
            s = self.sec(f"{kind}-{n.lower()}", kind, parent, n, b["title"], [*path, f"{kind.capitalize()} {n} {b['title']}"],
                         b["page"], b.get("text", ""))
            if s["id"] != f"{self.slug}:{kind}-{n.lower()}":
                self.issues.append(f"{kind} {n} appears twice (file page {b['page']}): second one is {s['id']}")
            s["caption_box"] = b["caption_box"]
            s["caption_above"] = b.get("caption_above", False)
        if kind == "figure":
            s["labels"] = b.get("labels", [])
            if b.get("image_bbox"):
                s["image_bbox"] = {k: b["image_bbox"][k] for k in ("page", "top", "bottom", "x0", "x1")}
                # photo_box looks right of the photo up to here: the photo's own column, not the text beside it
                s["right_limit"] = round(max(b["image_bbox"]["x1"], b["area"]["x1"]) + 6, 1)
        if b.get("area"):
            s["area"] = b["area"]
            self.span(s, b["area"]["page"], b["area"]["top"], b["area"]["bottom"])

    def _attach_footnotes(self) -> None:
        """Each footnote goes to the paragraph on its page (or the page before) whose text has its mark; failing
        that, to the last paragraph that starts on or before its page."""
        paras = [s for s in self.sections if s["type"] in ("paragraph", "box")]
        for page, mark, text in self.footnotes:
            body = text[len(mark):].strip()
            owner = next((s for s in paras if s["file_page"] in (page, page - 1) and mark in s["text"]), None) \
                or next((s for s in reversed(paras) if s["file_page"] <= page), None)
            if owner is None:
                self.issues.append(f"footnote on file page {page} has no paragraph: {text[:40]}")
                continue
            owner["footnotes"].append(f"{mark} {body}")


def build_tree(doc: dict, meta: dict, fixes: list[dict] | None = None) -> dict:
    return GuideBuilder(doc, meta, fixes).build()


def read_guide(path) -> dict:
    return read_pdf(path, graphics=True, superscripts=True, common_size=True, split_backwards=True)


# ---------------------------------------------------------------- command line

def records(source_id: str, src: dict | None, module: str = MODULE) -> list[dict]:
    """Current PDF versions of the source that sources.yaml sends to this parser (or to another module)."""
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (CORPUS_DIR / "versions" / source_id).glob("*.json")]
    return sorted((r for r in recs if r["valid_to"] is None and r["media_type"] == "application/pdf"
                   and src and parser_for(src, r["version_id"]) == module), key=lambda r: r["version_id"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--only", help="parse only versions whose id contains this text")
    a = ap.parse_args(argv)
    import yaml

    doc = yaml.safe_load((CORPUS_DIR / "sources.yaml").read_text(encoding="utf-8"))
    src = next((s for s in doc["sources"] if s["id"] == a.source), None)
    root = CORPUS_DIR.parent
    fixes = load_fixes(a.source)
    todo = [r for r in records(a.source, src) if not a.only or a.only in r["version_id"]]
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
