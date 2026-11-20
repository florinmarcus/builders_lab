"""Parse a guidance PDF (HSE guides first) into a document tree.

    python -m system.rag.parse_pdf --source hse-hsg264

Design: architecture/design/regulations-corpus.md, ADR 0010. Two layers:

- read_pdf(path): the PDF as plain data: lines (page, top, x0, font, size, text, words with x0),
  filled rectangles (colour boxes) and images. pdfplumber (MIT licence); no PyMuPDF (AGPL).
- build_tree(doc, meta): the tree, from that data only, so it can be tested with hand-made lines.

What build_tree does (step A):
- drops headers and footers (lines repeating at the top or bottom of many pages), the cover and
  the contents pages; reads the printed page number from the footer ("Page 10 of 73");
- chapters (large titles, wrapped lines merged), headings (bold, larger than body text);
- numbered paragraphs: a body line at the left margin starting with the next number; appendices
  restart at 1, so a number that happens to start a wrapped line is not taken as a paragraph;
- bullets ("■■" from the dingbat font) become "• "; hyphenated line ends are joined;
- boxes (filled rectangle with a "Box N:" title) and highlighted notes (filled rectangle, no title);
- footnotes ("* ...") attached to the paragraph before them;
- figures and tables from their captions; small-print label lines go to the figure, table rows to
  the table (raw text for now); photos are matched to the caption below them;
- every table and figure is listed in "checks" for the model (grid check, description).

Step B (next): real table grids, figure images cut from the page, model descriptions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from system.rag.corpus import CORPUS_DIR, slugify
from system.rag.fixes import content_key, index, load_fixes

PARSER = "guidance-pdf/0.3"
SKIP_TITLES = {"contents"}
BACK_MATTER = {"references": "references", "further information": "further-information"}
CAPTION_RE = re.compile(r"^(Figure|Table)\s+(\d+)\b")
PAGE_NO_RE = re.compile(r"\bPage\s+(\S+)\s+of\s+\d+\b|^(\d+)\s+of\s+\d+\s+pages$")
BULLET_RE = re.compile(r"^[■●•▪]+\s*")
PART_RE = re.compile(r"^(PART|Part|SCHEDULE|Schedule)\s+(\d+[A-Z]?|[IVX]+)\b")
# A numbered paragraph: "12 Text" (HSE guides) or "12. Text" / "1.—(1) Text" (legislation printed as PDF).
PARA_RE = re.compile(r"^(\d{1,3})(?:\.—|\.\s|\s)\s*(\S.*)$")


# ---------------------------------------------------------------- reading the PDF

def _words(chars: list[dict]) -> list[dict]:
    """Words with x positions, plus bold (b) and colour (c) of their first character, when the PDF gives them."""
    words, cur, x0, x1, first = [], "", None, None, None
    prev = None

    def emit():
        w = {"x0": round(x0, 1), "x1": round(x1, 1), "text": cur}
        if "size" in first:
            w["s"] = round(first["size"], 1)
        if first.get("fontname"):
            w["f"] = first["fontname"].split("+")[-1]
        if "top" in first:
            w["t"] = round(first["top"], 1)
        if first.get("fontname") and any(k in first["fontname"] for k in ("Bold", "Heavy", "Black", "Semibold")):
            w["b"] = True
        col = _colour(first.get("non_stroking_color"))
        if col and col not in ((0.0,), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)):
            w["c"] = list(col)
        words.append(w)

    for c in chars:
        gap = prev is not None and c["x0"] - prev["x1"] > 1.5  # some PDFs have no space characters, only gaps
        if c["text"].isspace() or gap:
            if cur:
                emit()
            cur, x0 = "", None
            if c["text"].isspace():
                prev = c
                continue
        if not cur:
            x0, first = c["x0"], c
        cur += c["text"]
        x1 = c["x1"]
        prev = c
    if cur:
        emit()
    return words


def _until_gap(words: list[dict], gap: float = 25.0) -> list[dict]:
    """Words up to the first wide gap: text beside a caption on the same line is not part of it."""
    out = words[:1]
    for w in words[1:]:
        prev = out[-1]
        end = prev.get("x1", prev["x0"] + 5 * len(prev["text"]))
        if w["x0"] - end > gap:
            break
        out.append(w)
    return out


def _colour(c):
    if isinstance(c, (list, tuple)) and c:
        return tuple(round(float(x), 2) for x in c)
    return None


BULLET_FONTS = ("Dingbat", "Wingding", "Symbol")
GUTTER_MIN_LINES = 3


def normalise_bullet(l: dict) -> dict:
    """A bullet drawn with a symbol font ("n" in ZapfDingbats, a private-use glyph in Wingdings) becomes "•".
    When the bullet is smaller or in another font than the words after it, the line takes the size and font of
    its words, so a bullet does not make a body line look like small print."""
    ws = l.get("words") or []
    if len(ws) < 2:
        return l
    w0 = ws[0]
    f0 = w0.get("f") or l["font"]
    glyph = len(w0["text"]) <= 2 and any(k in f0 for k in BULLET_FONTS) and not BULLET_RE.match(w0["text"])
    if glyph:
        w0 = {**w0, "text": "•"}
        ws = [w0, *ws[1:]]
        l = {**l, "words": ws, "text": " ".join(w["text"] for w in ws)}
    if (glyph or (w0["text"] in ("•", "●", "▪") and not any(k in f0 for k in BULLET_FONTS))) and ws[1].get("s") \
            and (ws[1]["s"] != l["size"] or ws[1].get("f") != l["font"]):
        l = {**l, "size": ws[1]["s"], "font": ws[1].get("f", l["font"])}
    return l


def _is_bullet_word(w: dict, line_font: str = "") -> bool:
    f = w.get("f") or line_font
    return bool(BULLET_RE.fullmatch(w["text"])) or (len(w["text"]) <= 2 and any(k in f for k in BULLET_FONTS))


def _size_at(ws: list[dict], k: int, l: dict) -> float:
    """Size of the text starting at word k: a bullet takes the size of the word after it."""
    if _is_bullet_word(ws[k], l["font"]) and k + 1 < len(ws):
        k += 1
    return ws[k].get("s", l["size"])


def _segment(l: dict, ws: list[dict]) -> dict:
    """Part of a line (a run of its words) as a line of its own, with the size and font of its first word."""
    return {**l, "words": ws, "text": " ".join(w["text"] for w in ws), "x0": ws[0]["x0"],
            "top": min(w.get("t", l["top"]) for w in ws), "size": ws[0].get("s", l["size"]),
            "font": ws[0].get("f", l["font"])}


def split_columns(lines: list[dict], body_size: float, page_width: float,
                  tables: list[dict] | None = None) -> list[dict]:
    """Pages set in columns (a sidebar beside the main text, or two text columns): pdfplumber joins words that
    sit at the same height in different columns into one line. Find each page's gutters (a wide gap in at least
    GUTTER_MIN_LINES lines, all at the same place, with body-size text on its right), cut lines there, and give
    every line its reading order: "band" (full-width lines separate bands) and "col". A narrow first column
    (under 36% of the page) is a sidebar: its lines are marked "aside".
    Small print, and lines inside a ruled table, are never cut: table cells are not columns of text."""
    out: list[dict] = []
    pages: dict[int, list[dict]] = {}
    for l in lines:
        pages.setdefault(l["page"], []).append(l)
    for page in sorted(pages):
        ls = pages[page]
        boxes = [t for t in tables or [] if t["page"] == page]
        cands = []  # (line index, x where the right part starts)
        for i, l in enumerate(ls):
            if any(t["top"] - 2 <= l["top"] <= t["bottom"] and t["x0"] - 2 <= l["x0"] <= t["x1"] for t in boxes):
                continue
            ws = l.get("words") or []
            for k in range(1, len(ws)):
                a, b = ws[k - 1], ws[k]
                bs, as_ = _size_at(ws, k, l), a.get("s", l["size"])
                if (k == 1 and re.match(r"^(\(?[\divxlc]{1,4}[.)]?|\(?[a-z][.)]|[•■●▪–-])$", a["text"])) \
                        or _is_bullet_word(a, l["font"]):
                    continue  # a list number or bullet with a hanging indent, not a column
                if b["x0"] - a.get("x1", a["x0"]) >= max(8.0, 1.2 * bs) and bs >= body_size - 0.5 \
                        and as_ >= body_size - 1.5:
                    cands.append((i, b["x0"]))
        gutters: list[float] = []
        for _, x in sorted(cands, key=lambda c: c[1]):
            if any(g - 1 <= x <= g + 25 for g in gutters):  # a column's indented lines (bullets) are the same column
                continue
            hits = {i for i, x2 in cands if x - 1 <= x2 <= x + 25}
            if len(hits) < GUTTER_MIN_LINES:
                continue
            # Text columns: few body lines run across the gutter. In a table or a flow chart set in body-size
            # text, the paragraphs above and below cross it.
            lo, hi = min(ls[i]["top"] for i in hits), max(ls[i]["top"] for i in hits)
            crossing = 0
            for j, l in enumerate(ls):
                if j in hits or not (lo - 60 <= l["top"] <= hi + 60) or l["size"] < body_size - 0.5:
                    continue
                ws = l.get("words") or []
                if ws and ws[0]["x0"] < x - 2 and max(w.get("x1", w["x0"]) for w in ws) > x + 2:
                    crossing += 1
            if crossing * 2 <= len(hits):
                gutters.append(x)
        if not gutters:
            out.extend(ls)
            continue
        cut: list[dict] = []
        for l in ls:
            ws = l.get("words") or []
            if any(t["top"] - 2 <= l["top"] <= t["bottom"] and t["x0"] - 2 <= l["x0"] <= t["x1"] for t in boxes):
                ws = []
            parts, start = [], 0
            for k in range(1, len(ws)):
                a, b = ws[k - 1], ws[k]
                bs, as_ = _size_at(ws, k, l), a.get("s", l["size"])
                if any(a.get("x1", a["x0"]) < g - 2 and b["x0"] >= g - 1 for g in gutters) \
                        and b["x0"] - a.get("x1", a["x0"]) >= max(8.0, 1.2 * bs) and bs >= body_size - 0.5 \
                        and as_ >= body_size - 1.5:
                    parts.append(ws[start:k])
                    start = k
            if not parts:
                cut.append(l)
                continue
            parts.append(ws[start:])
            cut.extend(normalise_bullet(_segment(l, p)) for p in parts)
        band = 0
        first = gutters[0]
        left_min = min((l["x0"] for l in cut if l["x0"] < first - 1), default=first)
        aside = (first - left_min) < 0.36 * page_width
        for l in sorted(cut, key=lambda l: (l["top"], l["x0"])):
            ws = l.get("words") or []
            end = ws[-1].get("x1", l["x0"]) if ws else l["x0"]
            col = sum(1 for g in gutters if l["x0"] >= g - 1)
            nxt = gutters[col] if col < len(gutters) else None
            if nxt is not None and end > nxt + 2:  # crosses a gutter: a full-width line
                band += 1
                out.append({**l, "band": band, "col": 0})
                band += 1
                continue
            l = {**l, "band": band, "col": col}
            if aside and col == 0:
                l["aside"] = True
            out.append(l)
    return out


def read_pdf(path) -> dict:
    import pdfplumber

    lines, rects, images, tables = [], [], [], []
    with pdfplumber.open(str(path)) as pdf:
        for n, page in enumerate(pdf.pages, start=1):
            for l in page.extract_text_lines(return_chars=True):
                first = l["chars"][0]
                m = first.get("matrix") or (1, 0, 0, 1)
                if not first.get("upright", True) or m[0] < 0 or m[3] < 0:  # sideways or upside-down text
                    continue
                lines.append(normalise_bullet({
                    "page": n, "top": round(l["top"], 1), "x0": round(l["x0"], 1),
                    "size": round(first["size"], 1), "font": first["fontname"].split("+")[-1],
                    "text": l["text"], "words": _words(l["chars"]),
                }))
            for r in page.rects:
                col = _colour(r.get("non_stroking_color"))
                if r["width"] > 100 and r["height"] > 12 and col and col not in ((1.0,), (1.0, 1.0, 1.0)):
                    rects.append({"page": n, "top": round(r["top"], 1), "bottom": round(r["bottom"], 1),
                                  "x0": round(r["x0"], 1), "x1": round(r["x1"], 1), "colour": col})
            for im in page.images:
                images.append({"page": n, "top": round(im["top"], 1), "bottom": round(im["bottom"], 1),
                               "x0": round(im["x0"], 1), "x1": round(im["x1"], 1)})
            for t in page.find_tables():  # ruled tables; the model checks every grid later
                rows = [[" ".join((c or "").split()) for c in row] for row in t.extract()]
                rows = [r for r in rows if any(r)]
                if rows:
                    x0, top, x1, bottom = t.bbox
                    tables.append({"page": n, "top": round(top, 1), "bottom": round(bottom, 1),
                                   "x0": round(x0, 1), "x1": round(x1, 1), "rows": rows})
        count = len(pdf.pages)
        width = float(pdf.pages[0].width) if pdf.pages else 595.0
        height = float(pdf.pages[0].height) if pdf.pages else 842.0
    sizes = Counter(l["size"] for l in lines)
    body = sizes.most_common(1)[0][0] if sizes else 10.0
    lines = split_columns(lines, body, width, tables)
    return {"lines": lines, "rects": rects, "images": images, "tables": tables, "page_count": count,
            "page_width": width, "page_height": height}


# ---------------------------------------------------------------- building the tree

def _caption_under(cap_top: float, im: dict) -> bool:
    """A caption belongs under a photo if it starts below the photo's top and at most 40 points below its
    bottom: some images have white space at the bottom, with the caption printed over it (HSG227)."""
    return im["top"] < cap_top <= im["bottom"] + 40

def _is_bold(font: str) -> bool:
    return any(k in font for k in ("Bold", "Heavy", "Black"))


def _join(text: str, line: str) -> str:
    """Add a wrapped line to running text: bullets start a new line; hyphenated ends join."""
    if BULLET_RE.match(line):
        item = "• " + BULLET_RE.sub("", line)
        return f"{text}\n{item}" if text else item
    if not text:
        return line
    if text.endswith("-") and len(text) > 1 and text[-2].isalpha():
        return text + line
    return f"{text} {line}"


class Builder:
    def __init__(self, doc: dict, meta: dict, fixes: list[dict] | None = None):
        self.meta = meta
        self.fixes = index(fixes)
        self.doc_tables = doc.get("tables", [])
        self.page_width = doc.get("page_width") or 595.0
        self.title = meta.get("title") or meta.get("source_id", "")
        self.page_height = doc.get("page_height") or 842.0
        # Reading order: page, then band and column on pages set in columns (split_columns), then top to bottom.
        self.lines = sorted(doc["lines"], key=lambda l: (l["page"], l.get("band", 0), l.get("col", 0), l["top"], l["x0"]))
        self.rects = doc.get("rects", [])
        self.images = doc.get("images", [])
        self.page_count = doc.get("page_count") or max((l["page"] for l in self.lines), default=0)
        self.sections: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self.issues: list[str] = []
        self.checks: list[dict] = []
        self.printed: dict[int, str] = {}
        self.markers: list[tuple[int, float, str]] = []  # (page, top, status) from margin labels
        self._strip_furniture()
        self._margin_labels()
        self._metrics()

    # -------------------------------------------------- page furniture

    def _strip_furniture(self) -> None:
        def norm(l):
            return re.sub(r"\d+", "#", l["text"].strip())

        def band(l):
            return "top" if l["top"] < 75 else ("bottom" if l["top"] > self.page_height - 42 else None)

        seen: dict[tuple, set] = {}
        for l in self.lines:
            b = band(l)
            if b:
                seen.setdefault((b, norm(l)), set()).add(l["page"])
        need = max(2, int(0.3 * self.page_count))
        furniture = {k for k, pages in seen.items() if len(pages) >= need}
        kept = []
        for l in self.lines:
            b = band(l)
            if b and (b, norm(l)) in furniture:
                m = PAGE_NO_RE.search(l["text"])
                if m:
                    self.printed[l["page"]] = m.group(1) or m.group(2)
                continue
            kept.append(l)
        self.lines = kept

    def _margin_labels(self) -> None:
        """L143 prints "Regulation 2", "ACOP 2" or "Guidance 2" in the left margin: the text that follows is the
        law itself, the Approved Code of Practice, or guidance (each has a different legal weight). Split these
        labels off the lines they share and remember where each one starts."""
        label_re = re.compile(r"^(Regulation|ACOP|Guidance)\s+\d+[A-Z]?$")
        kept = []
        for l in self.lines:
            ws = l.get("words") or []
            if ws and ws[0]["x0"] < 120:
                k = 1
                while k < len(ws) and ws[k]["x0"] < 150:
                    k += 1
                label = " ".join(w["text"] for w in ws[:k])
                if label_re.match(label):
                    self.markers.append((l["page"], l["top"], label.split()[0].lower()))
                    rest = ws[k:]
                    if not rest:
                        continue
                    # The rest keeps its own size and font (the label is larger and bold).
                    l = {**l, "words": rest, "text": " ".join(w["text"] for w in rest), "x0": rest[0]["x0"],
                         "size": rest[0].get("s", l["size"]), "font": rest[0].get("f", l["font"])}
            kept.append(l)
        self.lines = kept

    def status_at(self, page: int, top: float) -> str | None:
        """regulation, acop or guidance: the last margin label at or before this point."""
        last = None
        for p, t, st in self.markers:
            if (p, t) <= (page, top + 1):
                last = st
            else:
                break
        return last

    def _metrics(self) -> None:
        sizes = Counter(l["size"] for l in self.lines)
        self.body_size = sizes.most_common(1)[0][0] if sizes else 10.0
        lefts = Counter(round(l["x0"]) for l in self.lines if l["size"] == self.body_size)
        self.body_left = lefts.most_common(1)[0][0] if lefts else 0
        self.part_size = max((l["size"] for l in self.lines if PART_RE.match(l["text"].strip())), default=0.0)

    def page_label(self, page: int) -> str:
        return self.printed.get(page, str(page))

    # -------------------------------------------------- sections

    def add(self, sec: dict) -> dict:
        if sec["id"] in self.by_id:
            self.issues.append(f"duplicate section id {sec['id']}")
        sec.setdefault("footnotes", [])
        self.sections.append(sec)
        self.by_id[sec["id"]] = sec
        return sec

    @staticmethod
    def span(sec: dict, page: int, top: float, bottom: float) -> None:
        """Remember the vertical extent of a table or figure on a page (to match PDF tables and cut images)."""
        sp = sec.setdefault("spans", {})
        a, b = sp.get(str(page), (top, bottom))
        sp[str(page)] = (min(a, top), max(b, bottom))

    def new(self, sid, kind, parent, number, title, path, page, text="", top: float | None = None) -> dict:
        sec = {
            "id": sid, "parent_id": parent["id"] if parent else None, "type": kind, "number": number,
            "title": title, "heading_path": path, "text": text, "printed_page": self.page_label(page),
            "file_page": page, "applies_to": None,
        }
        if self.markers and top is not None:
            st = self.status_at(page, top)
            if st:
                sec["status"] = st  # L143: regulation, acop or guidance
        return self.add(sec)

    # -------------------------------------------------- classification helpers

    def rect_of(self, l):
        for r in self.rects:
            if r["page"] == l["page"] and r["top"] - 3 <= l["top"] <= r["bottom"] and r["x0"] - 6 <= l["x0"] <= r["x1"]:
                return r
        return None

    def is_caption(self, l) -> bool:
        # Smaller than body text (HSG264), or bold at body size (HSG227, where captions sit above).
        return bool(CAPTION_RE.match(l["text"])) and (l["size"] < self.body_size or
                                                       (_is_bold(l["font"]) and l["size"] <= self.body_size))

    def is_callout(self, l) -> bool:
        """A key message in large bold italic (e.g. 'Take care, these dates are only a guideline'): a note."""
        return _is_bold(l["font"]) and "Italic" in l["font"] and self.body_size + 0.5 <= l["size"] < 2 * self.body_size

    def is_small(self, l) -> bool:
        return l["size"] <= self.body_size - 1.5

    def is_heading(self, l) -> bool:
        return (_is_bold(l["font"]) and "Italic" not in l["font"] and self.body_size + 0.5 <= l["size"] < 2 * self.body_size
                and self.body_left - 6 <= l["x0"] <= self.body_left + 25)

    def is_body_line(self, l) -> bool:
        """Ordinary running text at the left margin (not in a box, not a caption)."""
        return (l["size"] == self.body_size and not _is_bold(l["font"]) and abs(l["x0"] - self.body_left) <= 3
                and not self.rect_of(l))

    def caption_areas(self) -> dict[int, list[int]]:
        """For each caption line, the lines above it up to the first body line, heading or caption:
        the figure's labels or the table's rows (captions here sit below their figure or table)."""
        areas: dict[int, list[int]] = {}
        self.area_tops: dict[int, float] = {}
        self.area_below: set[int] = set()  # captions whose table or figure is below them
        # Second lines of captions: just below a caption line, same size (the font may differ: Light),
        # starting under one of the captions on that line (not text beside them, like a note box).
        cont: set[int] = set()
        for k, l in enumerate(self.lines):
            if not self.is_caption(l):
                continue
            words = l.get("words") or []
            starts = [w["x0"] for w in words if w["text"] in ("Figure", "Table")] or [l["x0"]]
            j, prev = k + 1, l
            while j < len(self.lines) and self.lines[j]["page"] == l["page"] and \
                    0 < self.lines[j]["top"] - prev["top"] < 15 and self.lines[j]["size"] == l["size"] and \
                    self.lines[j]["x0"] <= max(starts) + 5 and not CAPTION_RE.match(self.lines[j]["text"]):
                cont.add(j)
                prev = self.lines[j]
                j += 1
        self.caption_continuations = cont
        for k, l in enumerate(self.lines):
            if not self.is_caption(l):
                continue
            got = []
            j = k - 1
            stop_bottom = 72.0  # below the page header if nothing stops the walk
            while j >= 0 and self.lines[j]["page"] == l["page"]:
                x = self.lines[j]
                if self.is_body_line(x) or self.is_caption(x) or self.is_chapter(x) or self.is_heading(x) \
                        or j in cont or (self.rect_of(x) and not self.is_small(x)):
                    stop_bottom = x["top"] + x["size"] + 2
                    break
                got.append(j)
                j -= 1
            photo_above = any(im["page"] == l["page"] and _caption_under(l["top"], im) for im in self.images)
            if not got and not photo_above:  # nothing above: the caption may sit above its table or figure (HSG227)
                j = k + 1
                while j < len(self.lines) and self.lines[j]["page"] == l["page"]:
                    x = self.lines[j]
                    if j in cont:
                        j += 1
                        continue
                    if self.is_body_line(x) or self.is_caption(x) or self.is_chapter(x) or self.is_heading(x) \
                            or (self.rect_of(x) and not self.is_small(x)):
                        break
                    got.append(j)
                    j += 1
                if got:
                    self.area_below.add(k)
            areas[k] = sorted(got)
            self.area_tops[k] = stop_bottom
        return areas

    def is_chapter(self, l) -> bool:
        # HSG264/HSG227 chapters are at least twice the body size; L143 uses 16pt condensed on 10pt body.
        if l["size"] >= 2 * self.body_size or (l["size"] >= 1.5 * self.body_size and "Cond" in l["font"]):
            return True
        # Statutory instruments and similar: "PART 1", "SCHEDULE 2" and "CONTENTS" set larger than body text.
        # Contents pages list the Parts in a smaller size than the Parts themselves: only the largest count.
        if l["size"] > self.body_size + 0.4:
            t = l["text"].strip()
            if t.lower() in SKIP_TITLES:
                return True
            if PART_RE.match(t):
                return l["size"] >= self.part_size - 0.5
        return False

    def _part_title(self, i: int, title: str) -> tuple[str, int]:
        """A bare "PART 1" takes the line below it (larger than body text, not bold body text) as its title."""
        if not PART_RE.fullmatch(title.strip()) or i >= len(self.lines):
            return title, i
        nxt, cur = self.lines[i], self.lines[i - 1]
        if nxt["page"] == cur["page"] and 0 < nxt["top"] - cur["top"] < 40 and nxt["size"] > self.body_size + 0.4 \
                and not self.is_chapter(nxt):
            return f"{title} {nxt['text']}", i + 1
        return title, i

    def is_runin_heading(self, k: int, expected: int) -> bool:
        """A bold line at body size, at the left margin, just above the next numbered paragraph ("Interpretation"
        above "2. In these Regulations"): a heading. Legislation printed as PDF sets headings like this."""
        l = self.lines[k]
        ws = l.get("words") or []
        if not ws or not all(w.get("b") for w in ws) or l["size"] != self.body_size or l["text"].rstrip().endswith(".") \
                or abs(l["x0"] - self.body_left) > 20 or k + 1 >= len(self.lines):
            return False
        m = PARA_RE.match(self.lines[k + 1]["text"])
        return bool(m) and int(m.group(1)) == expected and self.lines[k + 1]["page"] - l["page"] <= 1

    def add_aside(self, block: list[dict], parent: dict) -> dict | None:
        """Sidebar lines (split_columns marks them "aside"): one note per sidebar heading ("Safety checklist",
        "Caution:"), or one note for the block if it has none."""
        groups: list[tuple[str | None, list[str]]] = []
        for x in block:
            ws = x.get("words") or []
            head = bool(ws) and all(w.get("b") for w in ws) and not BULLET_RE.match(x["text"]) and len(ws) <= 8
            if head and (not groups or groups[-1][1] or groups[-1][0] is None):
                groups.append((x["text"].strip(), []))
            elif head and groups and not groups[-1][1]:
                groups[-1] = (f"{groups[-1][0]} {x['text'].strip()}", [])
            else:
                if not groups:
                    groups.append((None, []))
                groups[-1][1].append(x["text"])
        last = None
        for title, texts in groups:
            text = ""
            for t in texts:
                text = _join(text, t)
            if not text and not title:
                continue
            k = 1 + sum(1 for s in self.sections if s["type"] == "note")
            last = self.new(f"note-{k}", "note", parent, None, title,
                            [*parent["heading_path"], title.rstrip(":") if title else "Note"], block[0]["page"], text)
            last["aside"] = True
        return last

    # -------------------------------------------------- main pass

    def build(self) -> dict:
        self.lines_seen_contents = False
        # Short documents (task sheets, leaflets) have a title on page 1 and no chapter titles after it: the whole
        # document is one chapter and page 1 is content, not a cover.
        self.has_chapters = any(self.is_chapter(l) for l in self.lines if l["page"] > 1)
        mode = "skip" if self.has_chapters else "content"  # skip (cover, contents), content, back
        chapter = heading = None  # current chapter and heading sections
        para = None              # current numbered paragraph or text section
        last_body = None         # last section that can take a footnote
        counters: dict[str, int] = {}
        counter_key = "main"
        captions_on_page: list[dict] = []
        small_lines: list[dict] = []
        rect_done: set[int] = set()
        prev_caption_line = None
        prev_caption_top = 0.0
        last_footnote = None
        areas = self.caption_areas()
        consumed = {j for js in areas.values() for j in js}
        i = 0
        while i < len(self.lines):
            l = self.lines[i]
            # ---- chapter titles (merge wrapped lines)
            if self.is_chapter(l):
                parts = [l["text"]]
                j = i + 1
                while j < len(self.lines) and self.is_chapter(self.lines[j]) and self.lines[j]["page"] == l["page"] \
                        and self.lines[j]["top"] - self.lines[j - 1]["top"] < 45:
                    parts.append(self.lines[j]["text"])
                    j += 1
                i = j
                title = " ".join(parts)
                title, i = self._part_title(i, title)
                low = title.lower().strip()
                if not self.has_chapters:
                    continue  # the document's own title (page 1)
                para = None
                heading = None
                if l["page"] == 1 or low in SKIP_TITLES:
                    mode = "skip"
                    self.lines_seen_contents = self.lines_seen_contents or low in SKIP_TITLES
                    continue
                if low in BACK_MATTER:
                    mode = "back"
                    chapter = self.new(BACK_MATTER[low], "references" if low == "references" else "back-matter",
                                       None, None, title, [self.title, title], l["page"])
                    continue
                mode = "content"
                m_num = re.match(r"^(\d+)\s+(.*)$", title)
                m_app = re.match(r"^Appendix\s+(\d+)\s*[:\-–—]?\s*(.*)$", title, flags=re.I)
                m_part = PART_RE.match(title)
                if m_part:
                    kind, n = m_part.group(1).lower(), m_part.group(2)
                    t = title[m_part.end():].strip(" :-–—")
                    cid = f"{kind}-{n.lower()}"
                    while cid in self.by_id:
                        cid += "-2"
                    chapter = self.new(cid, "appendix" if kind == "schedule" else "chapter", None, n, t or title,
                                       [self.title, title], l["page"])
                    counter_key = cid if kind == "schedule" else "main"
                elif m_app:
                    n, t = m_app.group(1), m_app.group(2).lstrip(":-–— ")
                    chapter = self.new(f"appendix-{n}", "appendix", None, n, t, [self.title, f"Appendix {n} {t}"], l["page"])
                    counter_key = chapter["id"]
                elif m_num:
                    n, t = m_num.group(1), m_num.group(2)
                    chapter = self.new(f"chapter-{n}", "chapter", None, n, t, [self.title, f"{n} {t}"], l["page"])
                    counter_key = "main"
                else:
                    chapter = self.new(slugify(title), "chapter", None, None, title, [self.title, title], l["page"])
                    counter_key = "main"
                continue
            k_line = i
            i += 1
            if mode == "skip":
                # A captioned figure or table between the contents and chapter 1 is content (HSG227's flow chart).
                if l["page"] > 1 and self.is_caption(l) and self.lines_seen_contents:
                    mode = "content"
                    chapter = self.new("front-matter", "chapter", None, None, "Front matter",
                                       [self.title, "Front matter"], l["page"])
                    heading = None
                else:
                    continue
            if k_line in consumed and mode == "content":
                continue
            if mode == "back":
                chapter["text"] = "\n".join(x for x in [chapter["text"], l["text"]] if x)
                continue
            if chapter is None:  # a document without chapter titles: one chapter, named after the document
                chapter = self.new("document", "chapter", None, None, self.title, [self.title], l["page"])
            parent = heading or chapter
            # ---- sidebar (split_columns): notes beside the main text
            if l.get("aside"):
                block = [l]
                while i < len(self.lines) and self.lines[i].get("aside") and self.lines[i]["page"] == l["page"] \
                        and not self.is_chapter(self.lines[i]):
                    if i not in consumed:
                        block.append(self.lines[i])
                    i += 1
                last_body = self.add_aside(block, parent) or last_body
                continue
            # ---- captions (figures and tables); two captions may share a line
            if self.is_caption(l):
                prev_caption_line = []
                for cap in self.split_captions(l):
                    kind = cap["kind"]
                    sid = f"{kind}-{cap['number']}"
                    sec = self.new(sid, kind, parent, cap["number"], cap["title"],
                                   [*parent["heading_path"], f"{kind.capitalize()} {cap['number']} {cap['title']}"], l["page"])
                    sec["labels"] = []
                    sec["caption_box"] = {"page": l["page"], "top": l["top"], "x0": cap["x0"], "x1": cap["x1"]}
                    captions_on_page.append(sec)
                    prev_caption_line.append(sec)
                area_lines = [self.lines[j] for j in areas.get(k_line, [])]
                area = [x["text"] for x in area_lines]
                for c in prev_caption_line:
                    if k_line in self.area_below:
                        self.span(c, l["page"], l["top"], area_lines[-1]["top"] + area_lines[-1]["size"] + 2)
                    else:
                        self.span(c, l["page"], area_lines[0]["top"] if area_lines else self.area_tops.get(k_line, l["top"]),
                                  l["top"] + l["size"] + 2)
                if area and prev_caption_line:
                    first = prev_caption_line[0]
                    if first["type"] == "figure":
                        first["labels"].extend(area)
                    else:
                        first["text"] = "\n".join(x for x in [first["text"], *area] if x)
                prev_caption_top = l["top"]
                continue
            if prev_caption_line and k_line in self.caption_continuations:
                self.continue_captions(prev_caption_line, l)
                prev_caption_top = l["top"]
                continue
            prev_caption_line = None
            # ---- small print: footnotes, figure labels, table rows
            if self.is_small(l) or (l["size"] < self.body_size - 0.5 and "Dingbat" not in l["font"] and not self.rect_of(l)):
                mark = l["text"].lstrip()[:1]
                if mark in ("*", "†", "‡") and last_body:  # footnotes may start left of the body margin
                    owner = next((s for s in reversed(self.sections)
                                  if s["type"] in ("paragraph", "text", "box", "note") and mark in s["text"]), last_body)
                    owner["footnotes"].append(l["text"].strip())
                    last_footnote = (owner, l)
                    continue
                if last_footnote and last_footnote[1]["page"] == l["page"] and 0 < l["top"] - last_footnote[1]["top"] < 14 \
                        and abs(l["x0"] - last_footnote[1]["x0"]) < 6:
                    owner = last_footnote[0]
                    owner["footnotes"][-1] = f"{owner['footnotes'][-1]} {l['text'].strip()}"
                    last_footnote = (owner, l)
                    continue
                small_lines.append({**l, "parent": parent})
                continue
            # ---- boxes and highlighted notes
            r = self.rect_of(l)
            if r is not None:
                if id(r) in rect_done:
                    continue
                rect_done.add(id(r))
                inside = [x for x in self.lines if self.rect_of(x) is r and not self.is_small(x)]
                # The first line "Box N: title" is the title, bold or not; a wrapped title line joins it.
                m = re.match(r"^Box\s+(\d+)\s*:\s*(.*)$", inside[0]["text"]) if inside else None
                body = inside[1:] if m else inside
                t = m.group(2) if m else ""
                if m and body and body[0]["font"] == inside[0]["font"] and not BULLET_RE.match(body[0]["text"]) \
                        and body[0]["text"][:1].islower():
                    t = f"{t} {body[0]['text']}"
                    body = body[1:]
                text = ""
                for x in body:
                    text = _join(text, x["text"])
                if m:
                    n = m.group(1)
                    sec = self.new(f"box-{n}", "box", parent, n, t, [*parent["heading_path"], f"Box {n} {t}"], l["page"], text)
                else:
                    k = 1 + sum(1 for s in self.sections if s["type"] == "note")
                    sec = self.new(f"note-{k}", "note", parent, None, None, [*parent["heading_path"], "Note"], l["page"], text)
                sec["colour"] = list(r["colour"])
                last_body = sec
                continue
            # ---- callouts (key messages in large bold italic): notes
            if self.is_callout(l):
                text = l["text"]
                last_top = l["top"]
                while i < len(self.lines) and self.is_callout(self.lines[i]) and self.lines[i]["page"] == l["page"] \
                        and self.lines[i]["top"] - last_top < 22:
                    text = _join(text, self.lines[i]["text"])
                    last_top = self.lines[i]["top"]
                    i += 1
                k = 1 + sum(1 for s in self.sections if s["type"] == "note")
                last_body = self.new(f"note-{k}", "note", parent, None, None, [*parent["heading_path"], "Note"],
                                     l["page"], text)
                continue
            # ---- headings (merge wrapped heading lines)
            expected = counters.get(counter_key, 0) + 1
            if self.is_heading(l) or self.is_runin_heading(k_line, expected):
                title = l["text"]
                while i < len(self.lines) and self.is_heading(self.lines[i]) and self.lines[i]["page"] == l["page"] \
                        and self.lines[i]["top"] - l["top"] < 16 and not self.rect_of(self.lines[i]):
                    title += " " + self.lines[i]["text"]
                    i += 1
                hid = f"{chapter['id']}-{slugify(title)}"
                while hid in self.by_id:
                    hid += "-2"
                heading = self.new(hid, "heading", chapter, None, title, [*chapter["heading_path"], title], l["page"])
                para = None
                continue
            # ---- numbered paragraphs and running text
            m = PARA_RE.match(l["text"])
            dotted = bool(m) and l["text"][len(m.group(1))] == "."
            if m and int(m.group(1)) == expected and (abs(l["x0"] - self.body_left) <= 2 or
                                                       (dotted and abs(l["x0"] - self.body_left) <= 20)):
                counters[counter_key] = expected
                n = m.group(1)
                sid = f"para-{n}" if counter_key == "main" else f"{counter_key}-para-{n}"
                para = self.new(sid, "paragraph", parent, n, None, [*parent["heading_path"], f"Paragraph {n}"],
                                l["page"], _join("", m.group(2)), top=l["top"])
                last_body = para
                continue
            if para is None or para["parent_id"] != parent["id"] and para["type"] == "text":
                k = 1 + sum(1 for s in self.sections if s["parent_id"] == parent["id"] and s["type"] == "text")
                para = self.new(f"{parent['id']}-text-{k}", "text", parent, None, None,
                                [*parent["heading_path"], "Text"], l["page"], top=l["top"])
                last_body = para
            para["text"] = _join(para["text"], l["text"])
        self.place_small(small_lines, captions_on_page)
        self.place_images(captions_on_page)
        self.attach_grids()
        self.figure_areas()
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
            "title": self.title, "parser": PARSER,
            "sections": self.sections, "definitions": [], "issues": self.issues, "checks": self.checks,
        }

    # -------------------------------------------------- captions, labels, tables, images

    def split_captions(self, l) -> list[dict]:
        words = l.get("words") or [{"x0": l["x0"], "text": w} for w in l["text"].split()]
        starts = [k for k in range(len(words) - 1)
                  if words[k]["text"] in ("Figure", "Table") and re.match(r"^\d+[:.]?$", words[k + 1]["text"])]
        if not starts:  # words did not split as expected: fall back to the line's text
            m = CAPTION_RE.match(l["text"])
            self.issues.append(f"caption words not split on file page {l['page']}: {l['text'][:40]}")
            return [{"kind": m.group(1).lower(), "number": m.group(2), "title": l["text"][m.end():].strip(),
                     "x0": l["x0"], "x1": 10_000}]
        caps = []
        for a, k in enumerate(starts):
            end = starts[a + 1] if a + 1 < len(starts) else len(words)
            seg = _until_gap(words[k:end])
            caps.append({"kind": seg[0]["text"].lower(), "number": seg[1]["text"].rstrip(":."),
                         "title": " ".join(w["text"] for w in seg[2:]).strip().lstrip(":-–— "),
                         "x0": seg[0]["x0"], "x1": words[end]["x0"] if end < len(words) else 10_000})
        return caps

    def continue_captions(self, caps: list[dict], l) -> None:
        words = l.get("words") or [{"x0": l["x0"], "text": w} for w in l["text"].split()]
        for w in words:
            owner = max((c for c in caps if c["caption_box"]["x0"] <= w["x0"] + 5), key=lambda c: c["caption_box"]["x0"],
                        default=caps[0])
            owner["title"] = f"{owner['title']} {w['text']}".strip()
        for c in caps:
            c["heading_path"][-1] = f"{c['type'].capitalize()} {c['number']} {c['title']}"
            self.span(c, l["page"], l["top"], l["top"] + l["size"] + 2)

    def place_small(self, small: list[dict], captions: list[dict]) -> None:
        """Group small-print lines into blocks; a block just above (or below) a caption belongs to that
        figure or table; other blocks are tables without a caption (merged across pages per parent)."""
        blocks: list[list[dict]] = []
        for l in small:
            if blocks and blocks[-1][-1]["page"] == l["page"] and l["top"] - blocks[-1][-1]["top"] < 30:
                blocks[-1].append(l)
            else:
                blocks.append([l])
        unnamed: dict[str, dict] = {}
        for b in blocks:
            page, top, bottom = b[0]["page"], b[0]["top"], b[-1]["top"]
            near = [c for c in captions if c["caption_box"]["page"] == page and
                    (0 <= c["caption_box"]["top"] - bottom <= 100 or 0 <= top - c["caption_box"]["top"] <= 40)]
            near.sort(key=lambda c: abs(c["caption_box"]["top"] - bottom))
            texts = [x["text"] for x in b]
            if near:
                c = near[0]
                self.span(c, page, top, bottom + b[-1]["size"] + 2)
                if c["type"] == "figure":
                    c["labels"].extend(texts)
                else:
                    c["text"] = "\n".join(x for x in [c["text"], *texts] if x)
                continue
            parent = b[0]["parent"]
            key = parent["id"]
            t = unnamed.get(key)
            if t is None:
                k = 1 + sum(1 for s in self.sections if s["parent_id"] == key and s["type"] == "table")
                t = self.new(f"{key}-table-{k}", "table", parent, None, parent["title"],
                             [*parent["heading_path"], f"Table ({parent['title']})"], page)
                unnamed[key] = t
            t["text"] = "\n".join(x for x in [t["text"], *texts] if x)
            self.span(t, page, top, bottom + b[-1]["size"] + 2)

    def attach_grids(self) -> None:
        """Give each table section the PDF tables that overlap its lines; header rows repeated on later
        pages are dropped."""
        for s in self.sections:
            if s["type"] != "table":
                continue
            rows: list[list[str]] = []
            for page, (top, bottom) in sorted(s.get("spans", {}).items(), key=lambda kv: int(kv[0])):
                for t in self.doc_tables:
                    if t["page"] == int(page) and t["top"] <= bottom + 15 and t["bottom"] >= top - 15:
                        for r in t["rows"]:
                            if rows and r == rows[0]:
                                continue
                            rows.append(r)
            if rows:
                s["grid"], s["grid_source"] = rows, "pdf"
            else:
                self.issues.append(f"{s['id']}: no ruled table found on its pages; the model must build the grid")

    def figure_areas(self) -> None:
        """Where to cut each figure: the photo's box, or the caption area (labels down to the caption)."""
        for s in self.sections:
            if s["type"] != "figure":
                continue
            cap = s["caption_box"]
            if s.get("image_bbox"):
                im = s["image_bbox"]
                # The photo only: its caption is kept as text.
                s["area"] = {"page": im["page"], "top": im["top"], "bottom": im["bottom"], "x0": im["x0"], "x1": im["x1"]}
            else:
                top, bottom = s.get("spans", {}).get(str(cap["page"]), (cap["top"] - 200, cap["top"] + 12))
                s["area"] = {"page": cap["page"], "top": max(0.0, top - 6), "bottom": bottom,
                             "x0": 36.0, "x1": self.page_width - 36.0}

    def apply_fix(self, s: dict) -> bool:
        """Use a saved model fix for this table or figure if there is one. Returns True if used."""
        key = self.check_key(s)
        if s["type"] == "table":
            f = self.fixes.get((key, "table"))
            if f:
                v = f["value"]
                s["columns"], s["grid"], s["row_sentences"] = v.get("columns"), v.get("rows"), v.get("sentences", [])
                s["heading_rows"] = v.get("heading_rows", [])
                s["grid_source"] = "model"
                return True
        else:
            f = self.fixes.get((key, "figure_description"))
            if f:
                s["description"], s["description_source"] = f["value"], "model"
                return True
        return False

    @staticmethod
    def check_key(s: dict) -> str:
        return content_key(s["id"] + "\n" + s["text"] + "\n" + " ".join(s.get("labels", [])))

    def place_images(self, captions: list[dict]) -> None:
        for im in self.images:
            below = [c for c in captions if c["type"] == "figure" and c["caption_box"]["page"] == im["page"]
                     and _caption_under(c["caption_box"]["top"], im)
                     and c["caption_box"]["x0"] <= im["x1"] and c["caption_box"]["x0"] >= im["x0"] - 10]
            if not below:
                below = [c for c in captions if c["type"] == "figure" and c["caption_box"]["page"] == im["page"]
                         and _caption_under(c["caption_box"]["top"], im)]
            if below:
                c = min(below, key=lambda c: (abs(c["caption_box"]["top"] - im["bottom"]), abs(c["caption_box"]["x0"] - im["x0"])))
                if not c.get("image_bbox"):
                    c["image_bbox"] = {k: im[k] for k in ("page", "top", "bottom", "x0", "x1")}
            elif im["page"] != 1:
                self.issues.append(f"image on file page {im['page']} at {im['top']} has no caption below it")


def build_tree(doc: dict, meta: dict, fixes: list[dict] | None = None) -> dict:
    return Builder(doc, meta, fixes).build()


# ---------------------------------------------------------------- images (pypdfium2, permissive licence)

def _runs(flags: list[bool], min_gap: int) -> list[tuple[int, int]]:
    """Runs of True in flags, joining runs split by fewer than min_gap False values. Returns (start, end) pairs."""
    runs: list[list[int]] = []
    for i, f in enumerate(flags):
        if not f:
            continue
        if runs and i - runs[-1][1] <= min_gap:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    return [(a, b) for a, b in runs]


def photo_box(page_img, area: dict, caption: dict, scale: float, right_limit: float,
              ink: int = 235, gap_pt: float = 4.0) -> dict:
    """The photo's real box, from the rendered page. pdfplumber's image box can be wider or taller than the
    photo that is drawn (white padding, soft edges), so a neighbour photo can fall inside it, and words printed
    on the photo can fall outside it (HSG227 figures 3, 5, 6, 9). Find the block of non-white pixels that sits
    directly above the caption and starts in the caption's column. right_limit is where the next caption on the
    same line starts (or the page margin). Falls back to the image box if nothing is found."""
    if caption["page"] != area["page"]:
        return area
    left = max(0.0, min(area["x0"], caption["x0"]) - 6)
    right = max(area["x1"] + 6, right_limit - 4)
    top = max(0.0, area["top"] - 6)
    bottom = caption["top"] - 1
    if bottom - top < 20:
        return area
    win = page_img.crop((int(left * scale), int(top * scale), int(right * scale), int(bottom * scale)))
    mask = win.convert("L").point(lambda v: 255 if v < ink else 0)
    w, h = mask.size
    gap, tall = max(1, int(gap_pt * scale)), int(20 * scale)

    def runs_x(y0, y1):
        return [r for r in _runs([mask.crop((x, y0, x + 1, y1)).getbbox() is not None for x in range(w)], gap)
                if r[1] - r[0] > tall]

    def runs_y(x0, x1):
        return [r for r in _runs([mask.crop((x0, y, x1, y + 1)).getbbox() is not None for y in range(h)], gap)
                if r[1] - r[0] > tall]

    # 1. Rows, from a narrow strip at the caption's left edge: the lowest tall block above the caption.
    cap_x = int((max(caption["x0"], left) - left) * scale)
    rows = runs_y(cap_x, min(w, cap_x + int(30 * scale)))
    if not rows:
        return area
    y0, y1 = rows[-1]
    # 2. Columns, only within those rows (so text above the photo cannot join two photos together).
    cols = runs_x(y0, y1 + 1)
    if not cols:
        return area
    # Everything from the caption's column up to the next caption: the photo plus words printed beside it
    # ("BAD PRACTICE" in HSG227 figure 5). A neighbour photo to the left ends before the caption starts.
    cols = [c for c in cols if c[1] >= cap_x - gap]
    if not cols:
        return area
    x0, x1 = min(c[0] for c in cols), max(c[1] for c in cols)
    # 3. Rows again, within that column, then trim.
    rows = runs_y(x0, x1 + 1)
    if rows:
        y0, y1 = rows[-1]
    box = mask.crop((x0, y0, x1 + 1, y1 + 1)).getbbox() or (0, 0, x1 - x0 + 1, y1 - y0 + 1)
    return {"page": area["page"], "x0": round(left + (x0 + box[0]) / scale, 1),
            "x1": round(left + (x0 + box[2]) / scale, 1),
            "top": round(top + (y0 + box[1]) / scale, 1), "bottom": round(top + (y0 + box[3]) / scale, 1)}


def _next_caption_x(tree: dict, fig: dict) -> float:
    """Where the next figure caption on the same line starts, or the right page margin."""
    cap = fig["caption_box"]
    xs = [s["caption_box"]["x0"] for s in tree["sections"] if s["type"] == "figure" and s is not fig
          and s["caption_box"]["page"] == cap["page"] and abs(s["caption_box"]["top"] - cap["top"]) < 6
          and s["caption_box"]["x0"] > cap["x0"]]
    return min(xs, default=tree.get("page_width", 595.0) - 36.0)


def render_images(pdf_path, tree: dict, out_dir: Path, scale: float = 2.0) -> None:
    """Cut each figure out of its page, and render whole pages that hold tables (for the model check).
    Images go under corpus/parsed/ (not in git); their paths are written into the tree."""
    import pypdfium2 as pdfium

    root = CORPUS_DIR.parent
    pdf = pdfium.PdfDocument(str(pdf_path))
    cache: dict[int, object] = {}

    def page_image(n: int):
        if n not in cache:
            cache[n] = pdf[n - 1].render(scale=scale).to_pil()
        return cache[n]

    (out_dir / "figures").mkdir(parents=True, exist_ok=True)
    (out_dir / "pages").mkdir(parents=True, exist_ok=True)
    for s in tree["sections"]:
        if s["type"] == "figure" and s.get("area"):
            a = s["area"]
            if s.get("image_bbox"):
                a = s["area"] = photo_box(page_image(a["page"]), a, s["caption_box"], scale,
                                          _next_caption_x(tree, s))
            img = page_image(a["page"]).crop((int(a["x0"] * scale), int(a["top"] * scale),
                                              int(a["x1"] * scale), int(a["bottom"] * scale)))
            path = out_dir / "figures" / f"{s['id']}.png"
            img.save(path)
            s["image_path"] = path.relative_to(root).as_posix()
        elif s["type"] in ("table", "requirement"):  # requirement boxes (Approved Documents) are checked as tables
            paths = []
            for page in sorted({int(p) for p in s.get("spans", {})} or {s["file_page"]}):
                path = out_dir / "pages" / f"p{page}.png"
                if not path.exists():
                    page_image(page).save(path)
                paths.append(path.relative_to(root).as_posix())
            s["page_images"] = paths
    for c in tree["checks"]:
        sec = next((s for s in tree["sections"] if s["id"] == c["section_id"]), {})
        c["images"] = [sec["image_path"]] if sec.get("image_path") else sec.get("page_images", [])
    pdf.close()


# ---------------------------------------------------------------- command line

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    a = ap.parse_args(argv)
    import yaml

    doc = yaml.safe_load((CORPUS_DIR / "sources.yaml").read_text(encoding="utf-8"))
    src = next((s for s in doc["sources"] if s["id"] == a.source), None)
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (CORPUS_DIR / "versions" / a.source).glob("*.json")]
    root = CORPUS_DIR.parent
    for r in [r for r in recs if r["valid_to"] is None and r["media_type"] == "application/pdf"]:
        raw = root / r["raw_path"]
        if not raw.exists():
            print(f"missing raw file: {r['raw_path']}")
            continue
        tree = build_tree(read_pdf(raw), {**r, "title": src["title"] if src else a.source}, fixes=load_fixes(a.source))
        out = CORPUS_DIR / "parsed" / a.source / f"{r['version_id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        render_images(raw, tree, out.parent / r["version_id"])
        out.write_text(json.dumps(tree, ensure_ascii=False, indent=1), encoding="utf-8")
        types = Counter(s["type"] for s in tree["sections"])
        print(f"{r['version_id']}: {dict(types)}, {len(tree['issues'])} issues, {len(tree['checks'])} model checks "
              f"-> {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
