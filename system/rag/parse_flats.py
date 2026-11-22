"""Parse "Fire safety in purpose-built blocks of flats" (LGA 2011, Home Office 2024 reissue) into a document tree.

    python -m system.rag.parse_flats --source fso-guidance-collection

Design: architecture/design/regulations-corpus.md, ADR 0010. The guide has its own layout, unlike the 2006 fire
risk assessment guides (parse_guide) and the HSE guides (parse_pdf):

- One column of Arial 12pt. Front matter (a preface panel, Foreword, Contents, Acknowledgements), an Introduction,
  Parts A to G, Appendices 1 to 13, a Glossary, a Bibliography and an Index. Titles are set at 35pt ("Part E:
  Managing fire risk –" / "preventing fires" on two lines, "Appendix 1" with its title below in green 18pt).
- Numbered sections in green 18pt ("41. Introduction"), numbered paragraphs ("41.1", "A1.49") with the number
  hanging left of the text. One paragraph section per numbered paragraph, with all its text: bullets, the lines
  after them, and the text that runs on after a figure, a box or a page break. Sub-headings in bold 12pt.
- Each Part opens with "Key points" (18pt, black) and bullets, sometimes running onto the next page: one box.
- Boxes: a frame (drawn as an image or a rounded line) round a bold lead line and bullets.
- Figures: a bold caption ABOVE the picture ("Figure 7 – Multi-storey flat with ..."), the picture in the caption's
  column, with text running beside it. Photos, charts and a decision tree have no caption. Notes and keys in
  small print under a drawing belong to it.
- Footnotes in 8pt at the foot of the page ("2 Source: UK Fire Statistics 2008"), cited by raised numbers.
- The Glossary is a ruled two-column table: one definition section per term.

Ids are "flats:<local id>" ("flats:41-1", "flats:a1-49", "flats:part-e-key-points", "flats:figure-7"), unique
across the source. The tree format is parse_pdf's. Shared helpers come from parse_guide (GuideBuilder: drawn
objects, ruled tables, sections) and parse_pdf (reading the PDF, joining lines, rendering images).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter

from system.rag.corpus import CORPUS_DIR, slugify
from system.rag.fixes import index, load_fixes
from system.rag.parse_guide import GuideBuilder, _inside, _touches, _union, _x1, guide_title, is_heavy, records, \
    read_guide, short_slug, split_wide
from system.rag.parse_pdf import BULLET_RE, _join, _join_all, render_images

PARSER = "flats-guide-pdf/0.1"
MODULE = "parse_flats"
SLUG = "flats"
TITLE_SIZE = 30.0          # Part, Appendix and front-matter titles are 35pt
SECTION_SIZE = 17.0        # numbered sections and appendix titles are 18pt
CAPTION_RE = re.compile(r"^Figure\s+(\d{1,2})\s*[–-]\s*(.*)$")
SECTION_RE = re.compile(r"^(\d{1,2})\.\s+(\S.*)$")
PART_RE = re.compile(r"^Part\s+([A-H]):\s*(.*)$")
APPENDIX_RE = re.compile(r"^Appendix\s+(\d{1,2})$")
PARA_NUM_RE = re.compile(r"^(A?\d{1,2})\.(\d{1,3})$")
FOOTER_RE = re.compile(r"Fire safety in purpose-built blocks of flats")
SUPER = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
UNSUPER = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
SENTENCE_END = re.compile(r"[.!?:]['’”)]?$")
DASH_RE = re.compile(r"^[-–]\s")
FOOTER_TOP = 785.0         # footer rule and running footer below this


def straddles(l: dict, x: float, gap: float = 10.0) -> bool:
    """The line's words run across x: a word spans it, or two words close together sit either side of it (not
    two labels of neighbouring pictures read as one line)."""
    ws = l.get("words") or []
    for k, w in enumerate(ws):
        if w["x0"] < x < w.get("x1", w["x0"]):
            return True
        if k and ws[k - 1].get("x1", ws[k - 1]["x0"]) <= x <= w["x0"] and w["x0"] - ws[k - 1].get("x1", 0) < gap:
            return True
    return False


def join_line(text: str, line: str) -> str:
    """parse_pdf's _join, and a list item set with a dash ("- the fire resistance ...") starts a new line."""
    return f"{text}\n{line}" if text and DASH_RE.match(line) else _join(text, line)


class FlatsBuilder(GuideBuilder):
    """Builds the tree from read_pdf data. Reuses GuideBuilder's helpers (drawn objects, ruled tables, sections);
    the passes and the main loop are its own, so parse_guide's output does not change."""

    MIN_PICTURE = (50, 40)  # points: smaller drawn things are not pictures
    GROW_KEYS = False       # pictures without a caption take in the small print around them (the booklets)

    def __init__(self, doc: dict, meta: dict, fixes: list[dict] | None = None):  # noqa: D107 (own set-up)
        self.meta = meta
        self.fixes = index(fixes)
        self.doc_tables = doc.get("tables", [])
        self.page_width = doc.get("page_width") or 595.0
        self.page_height = doc.get("page_height") or 842.0
        self.pages = {int(k): v for k, v in (doc.get("pages") or {}).items()}
        self.title = guide_title(meta.get("title") or meta.get("source_id", ""))
        self.slug = meta.get("slug") or SLUG
        self.images = doc.get("images", [])
        self.graphics = [g for g in doc.get("graphics", []) if g["bottom"] > 0
                         and g["top"] < self.size_of(g["page"])[1]]
        self.page_count = doc.get("page_count") or max((l["page"] for l in doc["lines"]), default=0)
        self.sections: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self.issues: list[str] = []
        self.checks: list[dict] = []
        self.printed: dict[int, str] = {}
        self.markers: list = []
        self.claimed: set[int] = set()
        self.anchors: dict[int, list[dict]] = {}
        self._fills: dict[int, list[dict]] = {}
        self._objects: dict[int, list[dict]] = {}
        self._body_fonts: dict[int, str] = {}
        self.box_rects: list[dict] = []
        self.boxes: list[dict] = []
        self.figures: list[dict] = []
        self.lines = self._clean(doc["lines"])
        self._metrics()
        self._frames()
        self._captions()
        self._pictures()
        self._glossary_tables = [r for r in self.doc_tables if self._is_glossary(r)]
        self.doc_tables = [r for r in self.doc_tables if r not in self._glossary_tables]
        self._loose_tables()
        self.lines.sort(key=lambda l: (l["page"], l["top"], l["x0"]))

    # -------------------------------------------------- set-up passes

    def tab_x(self, page: int) -> float:
        return self.size_of(page)[0] - 30  # no side tab in this guide

    def _clean(self, lines: list[dict]) -> list[dict]:
        """Drop the running footer (keep its page number) and cut lines at wide gaps (text beside a figure, chart
        labels, two captions on one line)."""
        out = []
        for l in lines:
            t = l["text"].strip()
            if not t or t == ".":
                continue
            if l["top"] > FOOTER_TOP - 5 and FOOTER_RE.search(t):
                m = re.match(r"^(\d{1,3})\s", t) or re.search(r"\s(\d{1,3})$", t)
                self.printed[l["page"]] = m.group(1) if m else str(l["page"] - 2)
                continue
            out.extend(split_wide(self._drawn_bullet(l)))
        for p in range(1, self.page_count + 1):
            self.printed.setdefault(p, str(p - 2) if p > 2 else str(p))
        return out

    def _drawn_bullet(self, l: dict) -> dict:
        """Bullets in boxes are drawn as small dots, not printed as "•": put the "•" back in the text."""
        if BULLET_RE.match(l["text"]):
            return l
        mid = l["top"] + l["size"] / 2
        for g in self.graphics:
            if g["page"] == l["page"] and g["fill"] and g["kind"] in ("curve", "rect") and g["x1"] - g["x0"] <= 5 \
                    and g["bottom"] - g["top"] <= 5 and l["x0"] - 14 <= g["x0"] < l["x0"] and g["top"] <= mid <= g["bottom"] + 3:
                dot = {"x0": g["x0"], "x1": g["x1"], "text": "•", "s": l["size"], "f": l["font"]}
                return {**l, "x0": g["x0"], "text": "• " + l["text"], "words": [dot, *l.get("words", [])]}
        return l

    def body_line(self, l: dict, words: int = 5) -> bool:
        """Running text: 12pt (or the preface's 14pt), regular weight, a line of words."""
        return 11.5 <= l["size"] <= 14.5 and len(l["text"].split()) >= words and not self.heavy_line(l)

    def objects(self, page: int) -> list[dict]:
        """What is drawn on a page, without page backgrounds, the footer and specks (GuideBuilder.objects), and
        without frames that hold running text (box frames, a mask behind the redacted paragraphs)."""
        if page in self._objects:
            return self._objects[page]
        out = [o for o in super().objects(page) if o["top"] < FOOTER_TOP and not self._holds_text(o)
               and not self.redacted(o)]
        bars = [o for o in self.graphics if o["page"] == page and self.redacted(o)]
        if len(bars) >= 3:
            self.issues.append(f"file page {page}: {len(bars)} lines of text blacked out in the printed guide")
        self._objects[page] = out
        return out

    def _holds_text(self, o: dict) -> bool:
        """A frame or mask behind running text: two long lines, or a numbered paragraph, inside it."""
        if o["x1"] - o["x0"] < 150 or o["bottom"] - o["top"] < 25:
            return False
        inside = [l for l in self.lines if _inside(l, o, 1) and l["size"] >= 11.5]
        return sum(len(l["text"].split()) >= 7 for l in inside) >= 2 \
            or any(l.get("words") and PARA_NUM_RE.match(l["words"][0]["text"]) for l in inside)

    def redacted(self, o: dict) -> bool:
        """Black bars over removed text (paragraphs 79.9 to 79.11)."""
        return o["kind"] == "rect" and o["fill"] and tuple(o["colour"] or ()) in ((0.0,), (0.0, 0.0, 0.0)) \
            and 8 <= o["bottom"] - o["top"] <= 18 and o["x1"] - o["x0"] >= 40

    def _frames(self) -> None:
        """Boxes: a frame (an image or a drawn outline, wide and tall) round a bold lead line and running text."""
        frames = [o for o in [*({**im, "kind": "image"} for im in self.images), *self.graphics]
                  if o["kind"] in ("image", "curve", "rect") and o["x1"] - o["x0"] >= 150 and o["bottom"] - o["top"] >= 25
                  and o["bottom"] - o["top"] < 0.85 * self.size_of(o["page"])[1]]
        seen: set[tuple] = set()
        for o in sorted(frames, key=lambda o: (o["page"], o["top"])):
            key = (o["page"], round(o["top"]), round(o["bottom"]), round(o["x0"] / 4))
            if key in seen:
                continue  # the same frame drawn twice
            inside = sorted((l for l in self.lines if _inside(l, o, 1) and id(l) not in self.claimed),
                            key=lambda l: (l["top"], l["x0"]))
            if not inside or any(CAPTION_RE.match(l["text"].strip()) for l in inside):
                continue
            if not any(PARA_NUM_RE.match(l["words"][0]["text"]) for l in inside[:1]) \
                    and sum(1 for l in inside if self.body_line(l, 4)) >= 1 \
                    and ((self.heavy_line(inside[0]) and inside[0]["size"] < 12.5)
                                                                                  or self._continues_box(o, inside)):
                seen.add(key)
                self.box_rects.append(o)
                self._add_frame_box(inside, o)

    def _continues_box(self, o: dict, inside: list[dict]) -> bool:
        """A frame at the top of a page with no bold lead line goes on with the box at the foot of the page before."""
        prev = self.boxes[-1] if self.boxes else None
        return bool(prev) and prev["page"] == o["page"] - 1 and o["top"] < 120 and BULLET_RE.match(inside[0]["text"])

    def _add_frame_box(self, lines: list[dict], rect: dict) -> None:
        title_lines = []
        for l in lines:
            if self.heavy_line(l) and (not title_lines or l["top"] - title_lines[-1]["top"] < 1.6 * l["size"]):
                title_lines.append(l)
            else:
                break
        body = lines[len(title_lines):]
        text = ""
        for x in body:
            text = _join(text, x["text"].strip())
        self.claimed.update(id(x) for x in lines)
        if not title_lines and self.boxes and self.boxes[-1]["page"] == rect["page"] - 1:
            prev = self.boxes[-1]
            prev["text"] = "\n".join(t for t in [prev["text"], text] if t) if BULLET_RE.match(text) else \
                _join(prev["text"], text)
            return
        block = {"kind": "box", "title": _join_all(x["text"].strip() for x in title_lines), "text": text,
                 "page": rect["page"], "box": {k: rect[k] for k in ("page", "top", "bottom", "x0", "x1")}}
        self.boxes.append(block)
        self.anchors.setdefault(id(lines[0]), []).append(block)

    # -------------------------------------------------- figures

    def _captions(self) -> None:
        """Figures with a caption: the bold "Figure N – title" line(s), the picture below it in its column."""
        for k, l in enumerate(self.lines):
            m = CAPTION_RE.match(l["text"].strip())
            if not m or id(l) in self.claimed or not self.heavy_line(l):
                continue
            cap_lines, prev = [l], l
            for x in self.lines[k + 1:k + 8]:
                if x["page"] == l["page"] and self.heavy_line(x) and abs(x["x0"] - l["x0"]) < 6 \
                        and 0 < x["top"] - prev["top"] < 1.6 * l["size"] and not CAPTION_RE.match(x["text"].strip()):
                    cap_lines.append(x)
                    prev = x
            cap = {"page": l["page"], "top": l["top"], "bottom": prev["top"] + prev["size"] + 1,
                   "x0": min(x["x0"] for x in cap_lines), "x1": max(_x1(x) for x in cap_lines)}
            self.claimed.update(id(x) for x in cap_lines)
            block = {"kind": "figure", "number": m.group(1), "caption_box": cap, "page": l["page"],
                     "title": _join_all([m.group(2), *(x["text"].strip() for x in cap_lines[1:])]).strip(),
                     "caption_above": True}
            self.figures.append(block)
            self.anchors.setdefault(id(l), []).append(block)
        for block in self.figures:
            self._figure_below(block)

    def column(self, page: int, top: float, bottom: float, x0: float, x1: float) -> tuple[float, float]:
        """The horizontal room a picture has: between the running text to its left and to its right."""
        w, _ = self.size_of(page)
        left, right = 30.0, w - 30.0
        for l in self.lines:
            if l["page"] != page or id(l) in self.claimed or not self.body_line(l) or not (top <= l["top"] <= bottom):
                continue
            if l["x0"] >= x0 + 60:
                right = min(right, l["x0"] - 6)
            elif _x1(l) <= x0 + 5:
                left = max(left, _x1(l) + 6)
        return left, right

    def _figure_below(self, f: dict) -> None:
        cap = f["caption_box"]
        page = cap["page"]
        left, right = self.column(page, cap["top"], FOOTER_TOP, cap["x0"], cap["x1"])
        pair = False
        for o in self.figures:  # two captions on one line (Figures 11 and 12): each picture keeps to its own
            oc = o["caption_box"]
            if o is not f and oc["page"] == page and abs(oc["top"] - cap["top"]) < 6:
                pair = True
                if oc["x0"] > cap["x0"]:
                    right = min(right, oc["x0"] - 8)
                    boundary = right
                else:
                    left = max(left, cap["x0"] - 12)
                    boundary = left
        # A key printed across both pictures of a pair (small flats guide, Figures 3 to 6) belongs to both: it
        # is left out of both crops, so no crop shows half a line, and its words go to both figures' labels.
        shared: list[dict] = []
        if pair:
            cross = [l for l in self.lines if l["page"] == page and l["top"] > cap["bottom"] and l["size"] < 11.5
                     and straddles(l, boundary)]
            if cross:
                zone = min(l["top"] for l in cross) - 4
                shared = sorted((l for l in self.lines if l["page"] == page and l["top"] >= zone and l["size"] < 11.5
                                 and l["top"] < zone + 60), key=lambda l: (l["top"], l["x0"]))
        # The picture ends at the first running text below the caption in its column, or another caption.
        stop = FOOTER_TOP
        for l in self.lines:
            if l["page"] == page and id(l) not in self.claimed and l["top"] > cap["bottom"] \
                    and (self.body_line(l, 6) or l["size"] >= SECTION_SIZE) \
                    and l["x0"] < right and _x1(l) > left and not self._in_object(l):
                stop = min(stop, l["top"] - 2)
        for o in self.figures:
            if o is not f and o["caption_box"]["page"] == page and o["caption_box"]["top"] > cap["bottom"] \
                    and left - 5 <= o["caption_box"]["x0"] <= right:
                stop = min(stop, o["caption_box"]["top"] - 2)
        # A picture can start behind the caption's last line (Figure 11); a mask image just behind the caption
        # is not part of it.
        mask = {**cap, "top": cap["top"] - 5, "bottom": cap["bottom"] + 5, "x0": cap["x0"] - 5, "x1": cap["x1"] + 60}
        objs = [o for o in self.objects(page) if (o["top"] >= cap["bottom"] - 3 or (o["top"] >= cap["top"] - 2
                and o["bottom"] > cap["bottom"] + 20)) and o["bottom"] <= stop + 3
                and not (mask["top"] <= o["top"] and o["bottom"] <= mask["bottom"] and mask["x0"] <= o["x0"])
                and left - 2 <= (o["x0"] + o["x1"]) / 2 <= right + 2 and o["x1"] - o["x0"] < right - left + 20]
        labels = [l for l in self.lines if l["page"] == page and id(l) not in self.claimed
                  and cap["bottom"] - 1 <= l["top"] < stop and left - 2 <= l["x0"] and _x1(l) <= right + 6]
        # Only what hangs together below the caption: a photo further down the column is a picture of its own.
        pool = objs + [self._box_of(l) for l in labels]
        parts = [min(pool, key=lambda o: o["top"])] if pool else []  # what starts nearest below the caption
        grown = True
        while grown:
            grown = False
            for o in pool:
                reach = 25 if o.get("kind") == "image" else 45  # a key or note in small print sits further down
                if not any(o is q for q in parts) and any(_touches(o, q, reach) for q in parts):
                    parts.append(o)
                    grown = True
        labels = [l for l in labels if any(_touches(self._box_of(l), q, 0) for q in parts)]
        if shared:
            zone = shared[0]["top"] - 1
            parts = [q for q in parts if q["bottom"] < zone + 2]
            labels = [l for l in labels if l["top"] < zone - 2]
        if not parts:
            self.issues.append(f"figure {f['number']} (file page {page}): nothing drawn below its caption")
            f["area"] = None
            return
        box = _union(parts)
        pad = 3.0
        f["area"] = {"page": page, "top": round(max(box["top"] - pad, cap["bottom"] + 0.5), 1),
                     "bottom": round(box["bottom"] + pad, 1), "x0": round(max(box["x0"] - pad, left - 4), 1),
                     "x1": round(min(box["x1"] + pad, right + 8), 1)}
        f["labels"] = [self._label(l) for l in sorted(labels, key=lambda l: (l["top"], l["x0"]))] \
            + [self._label(l) for l in shared]
        self.claimed.update(id(l) for l in [*labels, *shared])

    def _in_object(self, l: dict) -> bool:
        """The line is printed on a picture (text set in the boxes of a drawing)."""
        return any(_inside(l, o, 0) for o in self.objects(l["page"]) if o["kind"] == "image")

    @staticmethod
    def _box_of(l: dict) -> dict:
        return {"page": l["page"], "top": l["top"], "bottom": l["top"] + l["size"], "x0": l["x0"], "x1": _x1(l),
                "kind": "text"}

    @staticmethod
    def _label(l: dict) -> str:
        return l["text"].translate(UNSUPER)  # chart values read as raised footnote numbers ("⁴⁰⁰")

    def _pictures(self) -> None:
        """Pictures without a caption (photos, charts, the decision tree): what is drawn close together, outside
        the captioned figures and the boxes, at least 50 by 40 points. Lines printed on it are its labels; a
        large bold line at its top (the decision tree's title) is its title."""
        taken = [f["area"] for f in self.figures if f.get("area")] + [b["box"] for b in self.boxes] \
            + [f["caption_box"] for f in self.figures]  # a mask image behind a caption is not a picture
        for page in sorted({o["page"] for o in [*self.images, *self.graphics]} - {1}):  # not the cover photo
            objs = [o for o in self.objects(page) if not any(a["page"] == page and _touches(a, o, -2) for a in taken)
                    and (o["x1"] - o["x0"] > 6 and o["bottom"] - o["top"] > 6)]
            groups: list[list[dict]] = []
            for o in objs:
                # photos set close together stay apart (2pt); the parts of a chart or a table touch (4pt)
                near = [g for g in groups if any(_touches(o, x, 2 if o["kind"] == x["kind"] == "image" else 4)
                                                 for x in g)]
                for g in near:
                    groups.remove(g)
                groups.append([o, *(x for g in near for x in g)])
            for g in groups:
                box = _union(g)
                if any(a["page"] == page and _touches(a, box, -2) for a in taken):
                    continue  # taken in by a picture grown from a neighbour (the second floor plan of a house)
                if box["x1"] - box["x0"] < self.MIN_PICTURE[0] or box["bottom"] - box["top"] < self.MIN_PICTURE[1]:
                    continue
                lines = sorted((l for l in self.lines if l["page"] == page and id(l) not in self.claimed
                                and _inside(l, box, 1)), key=lambda l: (l["top"], l["x0"]))
                title = [l for l in lines[:3] if self.heavy_line(l) and l["size"] >= 13]
                title = [l for l in title if l["size"] == title[0]["size"]]
                if not lines and all(o["kind"] == "rect" for o in g) and not any(o["kind"] == "image" for o in g):
                    continue  # a shaded panel with nothing in it
                if len(lines) >= 4 and all(o["kind"] in ("rect", "line") for o in g):
                    # shaded rows and rules with text: a table drawn without a grid (the risk matrix)
                    block = {"kind": "table", "number": None, "page": page, "area": box,
                             "text": "\n".join(l["text"] for l in lines)}
                    self.claimed.update(id(l) for l in lines)
                    self.figures.append(block)
                    taken.append(box)
                    self.anchors.setdefault(id(lines[0]), []).append(block)
                    continue
                if self.GROW_KEYS and not any(o["kind"] == "image" for o in g):  # drawings, not photos
                    box = self._grow_key(page, box, taken)
                    lines = sorted((l for l in self.lines if l["page"] == page and id(l) not in self.claimed
                                    and _inside(l, box, 1)), key=lambda l: (l["top"], l["x0"]))
                pad = 1.5
                area = {"page": page, "top": round(box["top"] - pad, 1), "bottom": round(box["bottom"] + pad, 1),
                        "x0": round(box["x0"] - pad, 1), "x1": round(box["x1"] + pad, 1)}
                block = {"kind": "figure", "number": None, "page": page, "area": area,
                         "title": _join_all(l["text"].strip() for l in title) or None,
                         "labels": [self._label(l) for l in lines if l not in title],
                         "caption_box": {"page": page, "top": area["top"], "bottom": area["top"], "x0": area["x0"],
                                         "x1": area["x1"]}}
                self.claimed.update(id(l) for l in lines)
                self.figures.append(block)
                taken.append(area)
                # placed in the reading order where the picture starts
                anchor = {"page": page, "top": box["top"], "x0": box["x0"], "size": 0, "text": "", "words": [],
                          "font": "", "_anchor": True}
                self.lines.append(anchor)
                self.claimed.add(id(anchor))
                self.anchors.setdefault(id(anchor), []).append(block)

    def _grow_key(self, page: int, box: dict, taken: list[dict], reach: float = 30.0) -> dict:
        """A drawing's labels and key in small print around it ("Fire-resisting, self-closing entrance door",
        a key of symbols, "Ground floor"), and the drawing's other parts they lead to, never running text."""
        small = [self._box_of(l) for l in self.lines if l["page"] == page and id(l) not in self.claimed
                 and l["size"] <= 10.5 and not _inside(l, box, 1) and not re.match(r"^\d{1,2}\s", l["text"])]
        body = [l for l in self.lines if l["page"] == page and id(l) not in self.claimed and l["size"] >= 11.5]
        pool = small + [o for o in self.objects(page) if o["kind"] != "image"
                        and not any(a["page"] == page and _touches(a, o, -2) for a in taken)]
        grown = True
        while grown:
            grown = False
            for o in pool:
                if o["x0"] >= box["x0"] and o["x1"] <= box["x1"] and o["top"] >= box["top"] and o["bottom"] <= box["bottom"]:
                    continue
                if not _touches(o, box, reach):
                    continue
                bigger = _union([box, o])
                if any(_inside(l, bigger, -1) for l in body):
                    continue
                box, grown = bigger, True
        return box

    def _is_glossary(self, r: dict) -> bool:
        heads = [l for l in self.lines if l["page"] <= r["page"] and l["size"] >= TITLE_SIZE]
        return bool(heads) and heads[-1]["text"].strip() == "Glossary" and max(len(x) for x in r["rows"]) == 2

    # -------------------------------------------------- the main pass

    def build(self) -> dict:
        mode = "skip"              # skip (cover, contents), content, back (bibliography), end (index)
        part = chapter = section = sub = None
        para = None                # the paragraph or key points box being filled
        last = None                # its last line
        counts: Counter = Counter()
        self.footnotes: list[tuple[int, str, str]] = []
        last_section = 0
        last_note = -1
        last_para: dict[str, int] = {}

        def parent():
            return sub or section or chapter or part

        i = 0
        while i < len(self.lines):
            l = self.lines[i]
            i += 1
            t = l["text"].strip()
            # ---- titles: Part, Appendix, front and back matter (wrapped lines merged)
            if l["size"] >= TITLE_SIZE and id(l) not in self.claimed:
                parts, prev = [t], l
                while i < len(self.lines) and self.lines[i]["page"] == l["page"] \
                        and self.lines[i]["size"] >= TITLE_SIZE and 0 < self.lines[i]["top"] - prev["top"] < 1.6 * l["size"]:
                    prev = self.lines[i]
                    parts.append(prev["text"].strip())
                    i += 1
                title = " ".join(parts)
                para = sub = section = None
                if l["page"] == 1:
                    mode = "content"  # the cover; the preface panel on page 2 has no title
                    continue
                if title == "Contents":
                    mode = "skip"
                    continue
                if title == "Index":
                    mode = "end"
                    continue
                if mode == "end":
                    continue
                mode = "content"
                m = PART_RE.match(title)
                if m:
                    part = self.sec(f"part-{m.group(1).lower()}", "part", None, m.group(1), m.group(2), [self.title, title],
                                    l["page"])
                    chapter = None
                    continue
                part = None
                m = APPENDIX_RE.match(title)
                if m:
                    chapter = self.sec(f"appendix-{m.group(1)}", "appendix", None, m.group(1), None, [self.title, title],
                                       l["page"])
                    continue
                if title == "Bibliography":
                    mode = "back"
                    chapter = self.sec("bibliography", "back-matter", None, None, title, [self.title, title], l["page"])
                    continue
                chapter = self.sec(slugify(title), "chapter", None, None, title, [self.title, title], l["page"])
                if title == "Glossary":
                    self._glossary(chapter)
                continue
            if mode in ("skip", "end"):
                continue
            # ---- figures, tables and boxes, placed where they start
            for b in self.anchors.get(id(l), []):
                self.place(b, parent() or self._doc(l))
            if id(l) in self.claimed:
                continue
            if mode == "back":
                chapter["text"] = _join(chapter["text"], t) if chapter["text"] and not l["top"] - last["top"] > 20 \
                    else "\n".join(x for x in [chapter["text"], t] if x)
                last = l
                continue
            # ---- green 18pt: numbered sections, an appendix's title, other headings
            if SECTION_SIZE <= l["size"] < TITLE_SIZE and self.coloured(l):
                group, prev = [l], l
                while i < len(self.lines) and self.lines[i]["page"] == l["page"] \
                        and abs(self.lines[i]["size"] - l["size"]) < 0.5 and self.coloured(self.lines[i]) \
                        and 0 < self.lines[i]["top"] - prev["top"] < 1.6 * l["size"]:
                    prev = self.lines[i]
                    group.append(prev)
                    i += 1
                title = _join_all(x["text"].strip() for x in group)
                para = sub = None
                m = SECTION_RE.match(title)
                if m:
                    n = int(m.group(1))
                    if n != last_section + 1:
                        self.issues.append(f"section numbers jump from {last_section} to {n} on file page {l['page']}")
                    last_section = n
                    host = part or chapter or self._doc(l)
                    section = self.sec(str(n), "chapter", host, str(n), m.group(2), [*host["heading_path"], title],
                                       l["page"])
                    continue
                if chapter and chapter["type"] == "appendix" and not chapter["title"]:
                    chapter["title"] = title
                    chapter["heading_path"][-1] = f"Appendix {chapter['number']} {title}"
                    continue
                host = section or chapter or part or self._doc(l)
                sub = self.sec(f"{self.local(host)}-{short_slug(title)}", "heading", host, None, title,
                               [*host["heading_path"], title], l["page"])
                continue
            # ---- Key points (18pt, black) at the start of a Part: one box, bullets up to the first section
            if l["size"] >= SECTION_SIZE and t == "Key points" and part is not None:
                para = self.sec(f"{self.local(part)}-key-points", "box", part, None, t, [*part["heading_path"], t],
                                l["page"])
                para["_key_points"], last = True, l
                continue
            # ---- sub-headings: a bold line (wrapped lines merged), not a sentence
            if self.heavy_line(l) and 11.5 <= l["size"] < SECTION_SIZE and not BULLET_RE.match(t) \
                    and not PARA_NUM_RE.match(l["words"][0]["text"]):
                group, prev = [l], l
                j = i
                while j < len(self.lines) and self.lines[j]["page"] == l["page"] and id(self.lines[j]) not in self.claimed \
                        and self.heavy_line(self.lines[j]) and abs(self.lines[j]["size"] - l["size"]) < 0.3 \
                        and 0 < self.lines[j]["top"] - prev["top"] < 1.6 * l["size"]:
                    prev = self.lines[j]
                    group.append(prev)
                    j += 1
                title = _join_all(x["text"].strip() for x in group)
                if len(title.split()) <= 25 and not title.endswith((".", ",", ";")):
                    i = j
                    host = section or chapter or part or self._doc(l)
                    sub = self.sec(f"{self.local(host)}-{short_slug(title)}", "heading", host, None,
                                   title.rstrip(":") if title.endswith(":") and len(title) < 60 else title,
                                   [*host["heading_path"], title.rstrip(":")], l["page"])
                    para = None
                    continue
            # ---- footnotes: small print at the foot of the page
            if l["size"] <= 8.5 and l["top"] > 600:
                m = re.match(r"^(\d{1,2})\s+(.*)$", t)
                if m:
                    self.footnotes.append((l["page"], m.group(1).translate(SUPER), m.group(2)))
                elif self.footnotes and self.footnotes[-1][0] == l["page"] and last_note == i - 1:
                    p, mark, text = self.footnotes[-1]
                    self.footnotes[-1] = (p, mark, f"{text} {t}")
                else:
                    self.footnotes.append((l["page"], "", t))
                last_note = i
                continue
            # ---- numbered paragraphs
            m = PARA_NUM_RE.match(l["words"][0]["text"]) if l["words"] else None
            if m and len(l["words"]) > 1 and (section or chapter):
                prefix, n = m.group(1), int(m.group(2))
                want = section["number"] if section else None
                if chapter and chapter["type"] == "appendix" and not section:
                    want = f"A{chapter['number']}"
                misprint = want and want.startswith("A") and prefix == want[1:]
                if want and (prefix == want or misprint) and n > last_para.get(want, 0):
                    if n != last_para.get(want, 0) + 1:
                        self.issues.append(f"paragraph numbers jump from {want}.{last_para.get(want, 0)} to "
                                           f"{want}.{n} on file page {l['page']}")
                    if misprint:
                        self.issues.append(f"paragraph {want}.{n} is printed as {prefix}.{n} (file page {l['page']})")
                    last_para[want] = n
                    num = f"{want}.{n}"
                    host = parent()
                    para = self.sec(num.lower().replace(".", "-"), "paragraph", host, num, None,
                                    list(host["heading_path"]), l["page"],
                                    " ".join(w["text"] for w in l["words"][1:]))
                    para["_numbered"], last = True, l
                    continue
            # ---- running text
            host = parent() or self._doc(l)
            if para is not None and (para.get("_numbered") or para.get("_key_points")):
                para["text"] = join_line(para["text"], t)
            elif para is not None and para["parent_id"] == host["id"] and self._goes_on(para, last, l):
                para["text"] = join_line(para["text"], t)
            else:
                counts[host["id"]] += 1
                para = self.sec(f"{self.local(host)}-para-{counts[host['id']]}", "paragraph", host, None, None,
                                list(host["heading_path"]), l["page"], _join("", t))
            last = l
        self._attach_notes()
        for s in self.sections:
            for k in ("_numbered", "_key_points"):
                s.pop(k, None)
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
            "sections": self.sections, "definitions": self.definitions, "issues": self.issues, "checks": self.checks,
        }

    definitions: list[dict] = []

    def _goes_on(self, para: dict, last: dict | None, l: dict) -> bool:
        """An unnumbered paragraph goes on: the next line on the same page close below, a list's lines (bullets,
        or dashes in Appendix 2), or a sentence broken by a page."""
        if last is None:
            return False
        text = para["text"].rstrip()
        item = bool(BULLET_RE.match(l["text"].strip()) or DASH_RE.match(l["text"].strip()))
        in_list = bool(re.search(r"(^|\n)(• |[-–] )", text))
        gap = l["top"] - last["top"]
        if last["page"] != l["page"] or gap < 0:  # a new page or column
            return not SENTENCE_END.search(text) or (item and (text.endswith(":") or in_list))
        if not item and text.endswith(":") and gap < 2.7 * l["size"]:
            return True  # a line set apart after a colon (a link: "... responsible person here:")
        if not item and not SENTENCE_END.search(text) and l["text"][:1].islower():
            return True  # a sentence broken by a picture
        if item:
            return text.endswith(":") or (in_list and gap < 1.9 * l["size"])
        if in_list and l["x0"] > last["x0"] - 1 and gap < 1.55 * l["size"]:
            return True  # a list item's wrapped line
        return 0 < gap < 1.55 * max(l["size"], last["size"])

    def _glossary(self, chapter: dict) -> None:
        """One definition section per term of the ruled glossary table (term, definition)."""
        self.definitions = []
        for r in self._glossary_tables:
            for row in r["rows"]:
                if len(row) != 2 or not row[0] or not row[1]:
                    continue
                term, text = row[0].strip(), row[1].strip()
                s = self.sec(f"glossary-{slugify(term)}", "definition", chapter, None, term,
                             [*chapter["heading_path"], term], r["page"], text)
                self.definitions.append({"term": term, "text": text, "section_id": s["id"]})
            self.claimed.update(id(l) for l in self.lines if _inside(l, r, 2))

    def place(self, b: dict, parent: dict) -> None:
        """A figure, table or box as a section under the current heading."""
        path = parent["heading_path"]
        if b["kind"] == "box":
            k = 1 + sum(1 for s in self.sections if s["parent_id"] == parent["id"] and s["type"] == "box")
            s = self.sec(f"{self.local(parent)}-box-{k}", "box", parent, None, b["title"] or None,
                         [*path, b["title"]] if b["title"] else list(path), b["page"], b["text"])
            s["box"] = b["box"]
            return
        if b["kind"] == "figure" and b["number"]:
            n = b["number"]
            s = self.sec(f"figure-{n}", "figure", parent, n, b["title"] or None,
                         [*path, f"Figure {n} – {b['title']}" if b["title"] else f"Figure {n}"], b["page"])
            s["caption_box"], s["caption_above"] = b["caption_box"], True
        elif b["kind"] == "figure":
            k = 1 + sum(1 for s in self.sections if s["parent_id"] == parent["id"] and s["type"] == "figure"
                        and s["number"] is None)
            label = b["title"] or f"Picture {k}"
            s = self.sec(f"{self.local(parent)}-figure-{k}", "figure", parent, None, b["title"],
                         [*path, label], b["page"])
            s["caption_box"], s["drawn"] = b["caption_box"], True
        else:  # a ruled table without a caption
            k = 1 + sum(1 for s in self.sections if s["parent_id"] == parent["id"] and s["type"] == "table")
            label = parent["title"] or self.title
            s = self.sec(f"{self.local(parent)}-table-{k}", "table", parent, None, label, [*path, f"Table ({label})"],
                         b["page"], b["text"])
        if b["kind"] == "figure":
            s["labels"] = b.get("labels", [])
        if b.get("area"):
            s["area"] = b["area"]
            self.span(s, b["area"]["page"], b["area"]["top"], b["area"]["bottom"])

    def _attach_notes(self) -> None:
        """A footnote goes to the paragraph on its page (or the page before) that cites its number; a note with no
        number (a correction notice) to the last paragraph on or before its page."""
        paras = [s for s in self.sections if s["type"] in ("paragraph", "box")]
        for page, mark, text in self.footnotes:
            owner = None
            if mark:
                owner = next((s for s in paras if s["file_page"] in (page, page - 1) and mark in s["text"]), None)
            owner = owner or next((s for s in reversed(paras) if s["file_page"] <= page), None)
            if owner is None:
                self.issues.append(f"footnote on file page {page} has no paragraph: {text[:40]}")
                continue
            owner["footnotes"].append(f"{mark} {text}".strip())


def build_tree(doc: dict, meta: dict, fixes: list[dict] | None = None) -> dict:
    return FlatsBuilder(doc, meta, fixes).build()


def drop_blank_pictures(pdf_path, tree: dict, scale: float = 0.5) -> list[str]:
    """Pictures without a caption whose area renders as one flat colour: an image placed in the PDF that shows
    nothing (pages 101 and 103 of the flats guide). They are dropped from the tree, with their checks, and
    listed as issues. Returns the dropped ids."""
    import pypdfium2 as pdfium
    from PIL import ImageStat

    pdf = pdfium.PdfDocument(str(pdf_path))
    blank = []
    for s in tree["sections"]:
        a = s.get("area")
        if s["type"] != "figure" or s.get("number") or not a or s.get("labels"):
            continue
        page = pdf[a["page"] - 1]
        media = page.get_mediabox()
        if tuple(page.get_cropbox()) != tuple(media):
            page.set_cropbox(*media)
        img = page.render(scale=scale).to_pil().convert("L").crop(
            (int(a["x0"] * scale) + 2, int(a["top"] * scale) + 2, int(a["x1"] * scale) - 2, int(a["bottom"] * scale) - 2))
        if max(ImageStat.Stat(img).stddev) < 2.0:
            blank.append(s["id"])
    pdf.close()
    if blank:
        tree["sections"] = [s for s in tree["sections"] if s["id"] not in blank]
        tree["checks"] = [c for c in tree["checks"] if c["section_id"] not in blank]
        tree.setdefault("dropped", []).extend(f"{b}: an image that shows nothing (flat colour)" for b in blank)
    return blank


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
