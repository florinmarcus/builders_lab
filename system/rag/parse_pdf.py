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

from system.rag.corpus import CORPUS_DIR, parser_for, slugify
from system.rag.fixes import content_key, index, load_fixes

PARSER = "guidance-pdf/0.3"
SKIP_TITLES = {"contents"}
BACK_MATTER = {"references": "references", "further information": "further-information"}
CAPTION_RE = re.compile(r"^(Figure|Table)\s+(A?\d+(?:\.\d+)?(?:[a-z]|\([a-z]\)(?:[–-]\([a-z]\))?)?)(?=[\s:.]|$)")  # "Figure 48d", "Table A1.2", "Figure 35(a)–(c)"
PAGE_NO_RE = re.compile(r"\bPage\s+(\S+)\s+of\s+\d+\b|^(\d+)\s+of\s+\d+\s+pages$")
BULLET_RE = re.compile(r"^[■●•▪]+\s*")
PART_RE = re.compile(r"^(PART|Part|SCHEDULE|Schedule|SECTION|Section)\s+(\d+[A-Z]?|[IVX]+|[A-H])\b")
# A numbered paragraph: "12 Text" (HSE guides) or "12. Text" / "1.—(1) Text" (legislation printed as PDF).
PARA_RE = re.compile(r"^(\d{1,3})(?:\.—|\.\s|\s)\s*(\S.*)$")
DEC_PARA_RE = re.compile(r"^(A?\d{1,2})\.(\d{1,3})\s+(\S.*)$")  # "2.14 Text": paragraph 14 of chapter 2 (HSG248)
SIGNED_RE = re.compile(r"^(Signed\b|Yours\s+(faithfully|sincerely))", re.I)  # just above or below a signature
ROLE_RE = re.compile(r"(Director|Secretary|Inspector|Minister|Chief Executive|Head of)")  # the signer's job title


# ---------------------------------------------------------------- reading the PDF

def _words(chars: list[dict], split_backwards: bool = False) -> list[dict]:
    """Words with x positions, plus bold (b) and colour (c) of their first character, when the PDF gives them.
    split_backwards: a character that starts left of the one before it begins a new word. pdfplumber can give
    the last word of one column and the first of the next in one run ("carry outFor")."""
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
        if first.get("fontname") and (_is_bold(first["fontname"]) or "Semibold" in first["fontname"]):
            w["b"] = True
        col = _colour(first.get("non_stroking_color"))
        if col and col not in ((0.0,), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)):
            w["c"] = list(col)
        words.append(w)

    for c in chars:
        if prev is not None and c["text"] == prev["text"] and abs(c["x0"] - prev["x0"]) < 1.0 and not c["text"].isspace():
            continue  # the same character printed twice on top of itself (bold faked by overprinting)
        gap = prev is not None and c["x0"] - prev["x1"] > 1.5  # some PDFs have no space characters, only gaps
        if split_backwards and prev is not None and c["x0"] < prev["x0"] - 1:
            gap = True
        if c["text"].isspace() or gap:
            if cur:
                emit()
            cur, x0 = "", None
            if c["text"].isspace():
                prev = c
                continue
        if not cur:
            x0, first = c["x0"], c
        elif first.get("sup") and not c.get("sup"):
            first = c  # a word that starts with a footnote number takes the size and font of its letters
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
    elif BULLET_RE.fullmatch(w0["text"]) and ws[1].get("s") and ws[1]["s"] >= l["size"] + 1.5:
        # "■" set much smaller than its words (L143: 8pt bullets on 10pt text)
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
                    left = [w for w in ws[:k] if not _is_bullet_word(w, l["font"])]
                    if len(left) <= 2 and re.fullmatch(r"\d+[A-Za-z]?[.:]?", left[-1]["text"] if left else "x"):
                        continue  # a numbered label ("Step 1") beside its text, as in a flow chart
                    cands.append((i, b["x0"], len(left)))
        gutters: list[float] = []
        for _, x, _n in sorted(cands, key=lambda c: c[1]):
            if any(g - 1 <= x <= g + 25 for g in gutters):  # a column's indented lines (bullets) are the same column
                continue
            hits = {i for i, x2, _n in cands if x - 1 <= x2 <= x + 25}
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
                        and b["x0"] - a.get("x1", a["x0"]) >= max(8.0, 1.2 * bs) and bs >= body_size - 1.5 \
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


def _size_weights(lines: list[dict]) -> Counter:
    """Text sizes weighted by characters: the body size is the one most text is set in (a sidebar of many short
    lines must not outvote the main column)."""
    c: Counter = Counter()
    for l in lines:
        c[l["size"]] += len(l["text"])
    return c


SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def mark_superscripts(chars: list[dict]) -> list[dict]:
    """Footnote numbers set small and raised ("the Order¹"): give them superscript digits, so they do not run
    into the word ("Order1", "Regulations20027"). A digit is raised when it is at most 80% of the line's main
    size and its bottom sits clearly above the line's baseline."""
    sizes = Counter(round(c["size"], 1) for c in chars if not c["text"].isspace())
    if not sizes:
        return chars
    main = sizes.most_common(1)[0][0]
    base = max((c["bottom"] for c in chars if round(c["size"], 1) == main), default=0)
    out = []
    for c in chars:
        if c["text"].isdigit() and c["size"] <= 0.8 * main and c["bottom"] < base - 0.2 * main:
            c = {**c, "text": c["text"].translate(SUPERSCRIPT), "sup": True}
        out.append(c)
    return out


def _graphic(n: int, o: dict, kind: str) -> dict:
    """A drawn rectangle, line or curve as plain data. Colours may be a list or a single grey or tint value."""
    def col(c):
        if isinstance(c, (int, float)):
            return (round(float(c), 2),)
        return _colour(c)
    return {"page": n, "kind": kind, "top": round(o["top"], 1), "bottom": round(o["bottom"], 1),
            "x0": round(o["x0"], 1), "x1": round(o["x1"], 1), "fill": bool(o.get("fill")),
            "stroke": bool(o.get("stroke")), "colour": col(o.get("non_stroking_color"))}


def read_pdf(path, *, graphics: bool = False, superscripts: bool = False, common_size: bool = False,
             split_backwards: bool = False) -> dict:
    """The PDF as plain data. The options are off by default (the HSE trees depend on the default output):
    graphics also returns every drawn rectangle, line and curve ("graphics") and each page's size ("pages");
    superscripts marks raised footnote numbers (mark_superscripts); common_size takes the page size most pages
    have, not page 1's (a cover printed as a two-page spread is twice as wide); split_backwards starts a new word
    where the text jumps back to the left (_words)."""
    import pdfplumber

    lines, rects, images, tables, drawn, boxes = [], [], [], [], [], {}
    with pdfplumber.open(str(path)) as pdf:
        for n, page in enumerate(pdf.pages, start=1):
            if graphics:
                boxes[n] = {"width": round(float(page.width), 1), "height": round(float(page.height), 1)}
                for kind in ("rects", "lines", "curves"):
                    drawn.extend(_graphic(n, o, kind[:-1]) for o in getattr(page, kind))
            for l in page.extract_text_lines(return_chars=True):
                first = l["chars"][0]
                m = first.get("matrix") or (1, 0, 0, 1)
                if not first.get("upright", True) or m[0] < 0 or m[3] < 0:  # sideways or upside-down text
                    continue
                if superscripts:
                    l = {**l, "chars": mark_superscripts(l["chars"])}
                    first = next((c for c in l["chars"] if not c.get("sup") and not c["text"].isspace()), first)
                ws = _words(l["chars"], split_backwards)
                text = l["text"]
                if superscripts or split_backwards or sum(len(w["text"]) for w in ws) < len(text.replace(" ", "")):
                    text = " ".join(w["text"] for w in ws)  # overprinted characters dropped, superscripts marked
                lines.append(normalise_bullet({
                    "page": n, "top": round(l["top"], 1), "x0": round(l["x0"], 1),
                    "size": round(first["size"], 1), "font": first["fontname"].split("+")[-1],
                    "text": text, "words": ws,
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
        if common_size and pdf.pages:
            width, height = Counter((float(p.width), float(p.height)) for p in pdf.pages).most_common(1)[0][0]
    sizes = _size_weights(lines)
    body = sizes.most_common(1)[0][0] if sizes else 10.0
    lines = split_columns(lines, body, width, tables)
    out = {"lines": lines, "rects": rects, "images": images, "tables": tables, "page_count": count,
           "page_width": width, "page_height": height}
    if graphics:
        out["graphics"], out["pages"] = drawn, boxes
    return out


# ---------------------------------------------------------------- building the tree

def _caption_under(cap_top: float, im: dict) -> bool:
    """A caption belongs under a photo if it starts below the photo's top and at most 40 points below its
    bottom: some images have white space at the bottom, with the caption printed over it (HSG227)."""
    return im["top"] < cap_top <= im["bottom"] + 40

BOLD_ABBR_RE = re.compile(r"-(Bd|Hv|Blk|Bk|Hvy)(Cn|It|CnO|O|Ex)?$")


def _is_bold(font: str) -> bool:
    """Bold, heavy or black weights, also when abbreviated in the font name (HelveticaNeueLTStd-Bd, -Hv, -BdCn)."""
    return any(k in font for k in ("Bold", "Heavy", "Black")) or bool(BOLD_ABBR_RE.search(font))


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


def _join_all(lines) -> str:
    text = ""
    for x in lines:
        text = _join(text, x)
    return text


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
        # Drawn shapes and page sizes (read_pdf(graphics=True)). None when the reader did not collect them: the
        # rules that need them are then skipped (hand-made test documents, older callers).
        self.graphics = doc.get("graphics")
        self.page_sizes = {int(k): v for k, v in (doc.get("pages") or {}).items()}
        self._shape_cache: dict[int, list[dict]] = {}
        self._stoppers: dict[int, bool] = {}
        self._ink_cache: dict[int, list[dict]] = {}
        self.page_count = doc.get("page_count") or max((l["page"] for l in self.lines), default=0)
        self.sections: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self.issues: list[str] = []
        self.checks: list[dict] = []
        self.printed: dict[int, str] = {}
        self.markers: list[tuple[int, float, str]] = []  # (page, top, status) from margin labels
        self._drop_overprint()
        self._strip_furniture()
        self._margin_labels()
        self._metrics()
        self._body_captions()
        self._diagram_pages()
        self._photo_captions()
        self._caption_sides()

    # -------------------------------------------------- drawn shapes

    def page_size(self, page: int) -> tuple[float, float]:
        p = self.page_sizes.get(page)
        return (p["width"], p["height"]) if p else (self.page_width, self.page_height)

    def shapes(self, page: int) -> list[dict]:
        """Drawn shapes on a page that can be part of a picture: not page backgrounds, not decoration running off
        the page edge, not the page-number tab in the footer."""
        if page not in self._shape_cache:
            pw, ph = self.page_size(page)
            gs = [g for g in self.graphics or [] if g["page"] == page and g["x0"] >= -1 and g["x1"] <= pw + 1
                  and g["top"] >= 30 and g["bottom"] <= ph - 20
                  and not (g["x1"] - g["x0"] > 0.9 * pw and g["bottom"] - g["top"] > 0.5 * ph)]
            for g in gs:
                w, h = g["x1"] - g["x0"], g["bottom"] - g["top"]
                if (h < 2 and w > 0.5 * pw) or (w < 2 and h > 300):
                    # A long thin line is a rule (under a heading, in the margin) unless other shapes touch it
                    # (a pipe in a gas installation diagram, a table border).
                    g["rule"] = not any(o is not g and o["x0"] <= g["x1"] + 2 and o["x1"] >= g["x0"] - 2
                                        and o["top"] <= g["bottom"] + 2 and o["bottom"] >= g["top"] - 2
                                        and (o["bottom"] - o["top"] >= 2 or o["x1"] - o["x0"] <= 0.5 * pw) for o in gs)
            self._shape_cache[page] = gs
        return self._shape_cache[page]

    @staticmethod
    def _is_rule(g: dict, pw: float) -> bool:
        """A long thin line that no other shape touches (set by shapes())."""
        return bool(g.get("rule"))

    def _pictures(self, page: int) -> list[dict]:
        """Images on a page, without a scan or background that fills most of it."""
        pw, ph = self.page_size(page)
        return [i for i in self.images if i["page"] == page and (i["x1"] - i["x0"]) * (i["bottom"] - i["top"]) < 0.6 * pw * ph]

    def drawn_page(self, page: int, ls: list[dict]) -> str | None:
        """What ink a page of short scattered lines has besides words: "picture" (text set in drawn boxes as in a
        flow chart, many drawn boxes as in a form, or images covering a tenth of the page), "table" (a ruled
        table holding most lines), or None (a letter's address block, a title page, short paragraphs)."""
        if self.graphics is None:
            return "picture"
        pw, ph = self.page_size(page)
        boxes = [g for g in self.shapes(page) if g["kind"] in ("rect", "curve")
                 and 12 < g["x1"] - g["x0"] < 0.7 * pw and 8 < g["bottom"] - g["top"] < 0.5 * ph]
        inbox = sum(1 for l in ls if any(g["x0"] - 2 <= l["x0"] <= g["x1"] and g["top"] - 2 <= l["top"] <= g["bottom"]
                                         for g in boxes))
        intab = sum(1 for l in ls if any(t["page"] == page and t["x0"] - 2 <= l["x0"] <= t["x1"]
                                         and t["top"] - 2 <= l["top"] <= t["bottom"] for t in self.doc_tables))
        ims = sum((i["x1"] - i["x0"]) * (i["bottom"] - i["top"]) for i in self._pictures(page))
        if (len(boxes) >= 3 and inbox >= 0.25 * len(ls) and intab < 0.5 * len(ls)) or ims >= 0.1 * pw * ph \
                or (len(boxes) >= 10 and intab < 0.5 * len(ls)):
            return "picture"
        return "table" if intab >= 0.5 * len(ls) else None

    def drawn_between(self, page: int, top: float, bottom: float) -> bool:
        """Shapes or an image among a block of short small-print lines: they label a drawing. Without them the
        lines are an address, a copyright notice or footnotes."""
        if self.graphics is None:
            return True
        pw, _ = self.page_size(page)
        n = sum(1 for g in self.shapes(page) if top - 5 <= (g["top"] + g["bottom"]) / 2 <= bottom + 5
                and not self._is_rule(g, pw))
        if n < 10 and any(t["page"] == page and t["top"] - 5 <= bottom and t["bottom"] + 5 >= top for t in self.doc_tables):
            return False  # the few rules of a ruled table: its cells, not a drawing's labels
        area = sum(max(0.0, min(i["bottom"], bottom) - max(i["top"], top)) * (i["x1"] - i["x0"])
                   for i in self._pictures(page))
        return n >= 6 or area >= 5000

    def ink_extent(self, page: int, box: dict) -> dict:
        """Grow a box (top, bottom, x0, x1) to take in the drawn shapes, ruled tables and images that touch it,
        so a flow chart's last box or arrow and a table's last row are not cut off."""
        pw, ph = self.page_size(page)
        items = [g for g in self.shapes(page) if not self._is_rule(g, pw)]
        items += [t for t in self.doc_tables if t["page"] == page]
        items += [i for i in self._pictures(page) if i["top"] >= 30 and i["bottom"] <= ph - 20]
        b = dict(box)
        grown = True
        while grown:
            grown = False
            for g in items:
                if g["bottom"] < b["top"] - 6 or g["top"] > b["bottom"] + 6 or g["x1"] < b["x0"] or g["x0"] > b["x1"]:
                    continue
                if g["top"] < b["top"] or g["bottom"] > b["bottom"] or g["x0"] < b["x0"] or g["x1"] > b["x1"]:
                    b = {"top": min(b["top"], g["top"]), "bottom": max(b["bottom"], g["bottom"]),
                         "x0": min(b["x0"], g["x0"]), "x1": max(b["x1"], g["x1"])}
                    grown = True
        return b

    # -------------------------------------------------- figure areas from ink

    def _boxed(self, l) -> bool:
        """The line is set inside a drawn box narrower than most of the page (a flow chart step, a label tag)."""
        pw, _ = self.page_size(l["page"])
        return any(g["kind"] in ("rect", "curve") and 12 < g["x1"] - g["x0"] < 0.6 * pw and g["bottom"] - g["top"] > 8
                   and g["x0"] - 2 <= l["x0"] <= g["x1"] and g["top"] - 2 <= l["top"] <= g["bottom"]
                   for g in self.shapes(l["page"]))

    def is_stopper(self, l) -> bool:
        """A line that is not part of any figure: running text (body size, six words or more, not set in a drawn
        box), a heading, a chapter title or another caption."""
        k = id(l)
        if k not in self._stoppers:
            def running(x):
                return x["size"] >= self.body_size - 0.5 and len(x["text"].split()) >= 6 and not self._boxed(x) \
                    and (not self.text_lefts or any(abs(x["x0"] - c) <= 2.5 for c in self.text_lefts)
                         or BULLET_RE.match(x["text"]) is not None)  # a bullet point is running text
            # The short last line of a paragraph ("Figure 2.") is running text too.
            tail = l["size"] >= self.body_size - 0.5 and any(
                x["page"] == l["page"] and 0 < l["top"] - x["top"] < 1.6 * l["size"] and abs(x["x0"] - l["x0"]) <= 3
                and x["size"] == l["size"] and running(x) for x in self.lines)
            self._stoppers[k] = self.is_caption(l) or self.is_chapter(l) or self.is_heading(l) or running(l) or tail \
                or self.caption_tail(l) is not None
        return self._stoppers[k]

    def caption_tail(self, l) -> dict | None:
        """The caption this line hangs under (a wrapped caption line or a source line such as "Western Power
        Distribution (WPD)": just below it, left-aligned with it, not larger). None if it is not one."""
        prev = l
        for _ in range(3):
            up = [x for x in self.lines if x["page"] == l["page"] and 0 < prev["top"] - x["top"] < 1.7 * max(x["size"], prev["size"])
                  and abs(x["x0"] - prev["x0"]) <= 3]
            if not up:
                return None
            x = max(up, key=lambda x: x["top"])
            if l["size"] > x["size"] + 0.5:
                return None
            if self.is_caption(x):
                return x
            prev = x
        return None

    @staticmethod
    def _seg_x1(l) -> float:
        """Right end of the line's first run of words: pdfplumber can join a text column's line with a drawing's
        label beside it (HSG33 Figure 2)."""
        ws = _until_gap(sorted(l.get("words") or [], key=lambda w: w["x0"]))
        return Builder._line_x1({**l, "words": ws}) if ws else Builder._line_x1(l)

    @staticmethod
    def _line_x1(l) -> float:
        ws = l.get("words") or []
        return max((w.get("x1", w["x0"] + 5 * len(w["text"])) for w in ws), default=l["x0"] + 5 * len(l["text"]))

    def ink_items(self, page: int) -> list[dict]:
        """Drawn shapes and images that can belong to a figure. A box holding running text is a note panel,
        not a drawing."""
        if page in self._ink_cache:
            return self._ink_cache[page]
        pw, ph = self.page_size(page)
        stoppers = [l for l in self.lines if l["page"] == page and l["size"] >= self.body_size - 0.5
                    and len(l["text"].split()) >= 6]
        items = []
        for g in self.shapes(page):
            if self._is_rule(g, pw):
                continue
            if g["kind"] == "rect" and g["x1"] - g["x0"] >= 0.6 * pw and any(
                    g["x0"] - 2 <= l["x0"] <= g["x1"] and g["top"] - 2 <= l["top"] <= g["bottom"] for l in stoppers):
                continue
            items.append(g)
        items += [i for i in self._pictures(page) if i["top"] >= 30 and i["bottom"] <= ph - 20]
        self._ink_cache[page] = items
        return items

    def ink_band(self, page: int, col: tuple[float, float], lo: float, hi: float) -> dict | None:
        """The drawn shapes, images and label lines between lo and hi that sit in the column col (x0, x1); the
        column widens to take in every item found. None when there is no drawn ink in the band."""
        x0, x1 = col
        # An image's box may reach a little past the band (white padding behind the caption, HSG247 Figure 8.2).
        items = [g for g in self.ink_items(page) if (g["top"] >= lo - 2 and g["bottom"] <= hi + 2) or (
            "kind" not in g and g["top"] >= lo - 40 and g["bottom"] <= hi + 40 and g["bottom"] - g["top"] > 100)]
        found: list[dict] = []
        rest = sorted(items, key=lambda g: g["x0"])
        grown = True
        while grown:
            grown = False
            keep = []
            for g in rest:
                if g["x1"] < x0 or g["x0"] > x1:
                    keep.append(g)
                    continue
                found.append(g)
                x0, x1 = min(x0, g["x0"]), max(x1, g["x1"])
                grown = True
            rest = keep
        if not found:
            return None
        box = {"top": min(g["top"] for g in found), "bottom": max(g["bottom"] for g in found), "x0": x0, "x1": x1,
               "lo": lo, "hi": hi}
        for l in self.lines:  # labels around the drawing
            if l["page"] != page or l["top"] < lo or l["top"] + l["size"] > hi + 2 or self.is_stopper(l):
                continue
            ws = _until_gap(sorted(l.get("words") or [], key=lambda w: w["x0"]))  # not words in the next column
            lx1 = self._line_x1({**l, "words": ws})
            if lx1 >= box["x0"] - 4 and l["x0"] <= box["x1"] + 4:
                box.update(top=min(box["top"], l["top"]), bottom=max(box["bottom"], l["top"] + l["size"] + 1),
                           x0=min(box["x0"], l["x0"]), x1=max(box["x1"], lx1))
        return box

    def _stop_above(self, page: int, y: float, col: tuple[float, float]) -> float:
        """Bottom of the lowest stopper line above y that overlaps the column (or below the page header)."""
        xs = [l["top"] + l["size"] + 1 for l in self.lines if l["page"] == page and l["top"] + l["size"] <= y
              and self._seg_x1(l) >= col[0] and l["x0"] <= col[1] and self.is_stopper(l)]
        return max(xs, default=45.0)

    def _stop_below(self, page: int, y: float, col: tuple[float, float]) -> float:
        """Top of the highest stopper line below y that overlaps the column (or above the page footer)."""
        _, ph = self.page_size(page)
        xs = [l["top"] - 1 for l in self.lines if l["page"] == page and l["top"] >= y
              and self._seg_x1(l) >= col[0] and l["x0"] <= col[1] and self.is_stopper(l)]
        return min(xs, default=ph - 40)

    def _band_above(self, page: int, y: float, col: tuple[float, float]) -> dict | None:
        band = self.ink_band(page, col, self._stop_above(page, y, col), y + 1)
        if band:  # the column widened: text beside the caption no longer counts, text over the drawing does
            wide = (band["x0"], band["x1"])
            band = self.ink_band(page, wide, self._stop_above(page, y, wide), y + 1)
        return band

    def _band_below(self, page: int, y: float, col: tuple[float, float]) -> dict | None:
        band = self.ink_band(page, col, y - 1, self._stop_below(page, y, col))
        if band:
            wide = (band["x0"], band["x1"])
            band = self.ink_band(page, wide, y - 1, self._stop_below(page, y, wide))
        return band

    def caption_column(self, cap: dict) -> tuple[float, float, float]:
        """The caption's column (x0, x1) and the right end of its words."""
        cap_lines = [l for l in self.lines if l["page"] == cap["page"] and abs(l["top"] - cap["top"]) < 2]
        ws = sorted((w for l in cap_lines for w in l.get("words") or [] if cap["x0"] - 1 <= w["x0"] < cap["x1"]),
                    key=lambda w: w["x0"])
        ws = _until_gap(ws) if ws else []  # text in the next column on the same line is not the caption
        right = max((w.get("x1", w["x0"] + 5 * len(w["text"])) for w in ws), default=cap["x0"] + 100)
        return cap["x0"] - 12, min(right, cap["x1"] - 4) + 12, right

    def caption_ink_area(self, s: dict, top: float, bottom: float) -> dict | None:
        """A captioned drawing cut from its ink: the shapes, images and labels between the caption and the
        running text on the side the figure is on, in the caption's column. Above the caption first, or below
        it first when the document sets its captions above figures (captions_above). None when no ink is found
        there, or when labels above the caption have no ink near them: the caller keeps the area from the labels."""
        cap = s["caption_box"]
        page = cap["page"]
        pw, ph = self.page_size(page)
        x0, x1, right = self.caption_column(cap)
        own = [l["top"] + l["size"] for l in self.lines if l["page"] == page and (abs(l["top"] - cap["top"]) < 2 or (
            cap["top"] < l["top"] < cap["top"] + 60 and (self.caption_tail(l) or {}).get("top") == cap["top"]))]
        cap_bottom = max([cap["top"] + 10, *own]) if self.captions_above else max(bottom, cap["top"] + 10)
        if self.captions_above:  # a caption in the margin column may head a figure in the text column
            band = self._band_below(page, cap_bottom, (x0, x1)) or self._band_below(page, cap_bottom, (36.0, pw - 36.0)) \
                or self._band_above(page, cap["top"] - 1, (x0, x1))
        else:
            band = self._band_above(page, cap["top"] - 1, (x0, x1))
            if band is None and top < cap["top"] - 30:
                return None
            band = band or self._band_below(page, cap_bottom, (x0, x1))
        if band is None:
            return None
        if band["bottom"] <= cap["top"] + 2:  # above its caption: the caption is taken too, and lines under it
            tails = [l["top"] + l["size"] + 1 for l in self.lines if l["page"] == page and cap["top"] < l["top"] < cap["top"] + 60
                     and self.caption_tail(l) is not None and abs(self.caption_tail(l)["top"] - cap["top"]) < 2]
            t, b = max(band["top"] - 3, band["lo"]), max([cap_bottom, *tails]) + 2
        else:  # below its caption
            t, b = cap["top"] - 2, min(band["bottom"] + 3, band["hi"])
        x0, x1 = min(band["x0"], cap["x0"]) - 3, max(band["x1"], right) + 3
        # A tinted panel behind the caption and the drawing (HSG85 flow charts) is part of the figure.
        panels = [g for g in self.shapes(page) if g["kind"] == "rect" and g["fill"] and g["x0"] <= x0 + 6
                  and g["x1"] >= x1 - 6 and g["top"] <= t + 6 and g["bottom"] >= b - 6
                  and (g["x1"] - g["x0"]) * (g["bottom"] - g["top"]) < 0.8 * pw * ph]
        if panels:
            g = min(panels, key=lambda g: (g["x1"] - g["x0"]) * (g["bottom"] - g["top"]))
            t, b, x0, x1 = min(t, g["top"] - 2), max(b, g["bottom"] + 2), min(x0, g["x0"] - 2), max(x1, g["x1"] + 2)
        if any(o is not s and o["type"] == "figure" and o.get("caption_box") and o["caption_box"]["page"] == page
               and abs(o["caption_box"]["top"] - cap["top"]) < 3 for o in self.sections):
            # figures side by side over one caption line: each keeps to its caption's column
            x0 = max(x0, cap["x0"] - 10)
            if cap["x1"] < 10_000:
                x1 = min(x1, cap["x1"] - 4)
        return {"page": page, "top": max(0.0, t), "bottom": min(ph, b), "x0": max(0.0, x0), "x1": min(pw, x1)}

    def drawn_ink_area(self, s: dict, top: float, bottom: float) -> dict | None:
        """A drawing found from its labels (no caption), cut from the ink around the labels, between the
        running text above and below them."""
        cap = s["caption_box"]
        page = cap["page"]
        pw, ph = self.page_size(page)
        ls = [l for l in self.lines if l["page"] == page and top - 1 <= l["top"] <= bottom and l["text"] in s["labels"]]
        if not ls:
            return None
        col = (min(l["x0"] for l in ls) - 6, max(self._line_x1(l) for l in ls) + 6)
        lo, hi = self._stop_above(page, top, col), self._stop_below(page, bottom, col)
        band = self.ink_band(page, col, lo, hi)
        if band is None:
            return None
        t, b = min(band["top"], top), max(band["bottom"], bottom)
        return {"page": page, "top": max(0.0, max(t - 3, lo)), "bottom": min(ph, min(b + 3, hi)),
                "x0": max(0.0, min(band["x0"], col[0]) - 3), "x1": min(pw, max(band["x1"], col[1]) + 3)}

    # -------------------------------------------------- pictures without "Figure N" captions

    def _diagram_pages(self) -> None:
        """A page that is one big picture: a flow chart drawn as boxes of text, an illustrated house with its
        numbered key (Asbestos essentials a0). Many short lines spread across the page at body size, almost no
        running text, no "Figure N" caption and no chapter title. The whole page becomes one figure."""
        self.diagram_pages: set[int] = set()
        self.table_pages: set[int] = set()
        pages: dict[int, list[dict]] = {}
        for l in self.lines:
            pages.setdefault(l["page"], []).append(l)
        for page, ls in pages.items():
            if len(ls) < 12 or any(CAPTION_RE.match(l["text"]) or self.is_chapter(l) for l in ls):
                continue
            running = [l for l in ls if l["size"] == self.body_size and abs(l["x0"] - self.left(l)) <= 3
                       and len(l["text"].split()) >= 7]
            near_body = [l for l in ls if l["size"] >= self.body_size - 1]
            if len(running) > 0.15 * len(ls) or len(near_body) < 0.7 * len(ls):
                continue
            short = sorted(len(l["text"].split()) for l in ls)[len(ls) // 2] <= 6  # boxes of a few words each
            if short and len({int(l["x0"] // 40) for l in ls}) >= 4:
                ink = self.drawn_page(page, ls)
                if ink == "picture":
                    self.diagram_pages.add(page)
                elif ink == "table":  # a page that is one ruled table with no caption: a table, not a figure
                    self.table_pages.add(page)

    def _caption_sides(self) -> None:
        """Does this document print figure captions above their figures (HSG247, HSG85 flow charts)? A vote over
        the figure captions: drawn ink or an image starting just below the caption and none ending just above
        it counts for "above", the reverse for "below". Needs the drawn shapes."""
        self.captions_above = False
        if self.graphics is None:
            return
        above = below = 0
        for l in self.lines:
            if not self.is_caption(l) or not l["text"].startswith("Figure"):
                continue
            cap = {"page": l["page"], "top": l["top"], "x0": l["x0"], "x1": 10_000}
            x0, x1, _ = self.caption_column(cap)
            items = [g for g in self.ink_items(l["page"]) if g["x1"] >= x0 and g["x0"] <= x1]
            a = any(l["top"] - 25 <= g["bottom"] <= l["top"] + 2 for g in items)
            b = any(l["top"] + l["size"] <= g["top"] <= l["top"] + 35 for g in items)
            above += b and not a
            below += a and not b
        self.captions_above = above >= 2 and above > 2 * below

    def _signature_or_logo(self, im: dict, on_page: list[dict]) -> bool:
        """An image that is not a picture of anything the text is about: a signature over the signer's name
        ("Yours faithfully" or "Signed:" above it, or a name and a job title below it), a letterhead logo at the
        top of page 1, or a publisher's logo or cover over a copyright line or web address."""
        tall, wide = im["bottom"] - im["top"], im["x1"] - im["x0"]
        small = tall <= 130 and wide <= 260
        above = sorted((l for l in on_page if im["top"] - 40 <= l["top"] and l["top"] + l["size"] <= im["top"] + 8),
                       key=lambda l: l["top"])
        below = sorted((l for l in on_page if im["bottom"] - 2 <= l["top"] <= im["bottom"] + 45
                        and l["x0"] < im["x1"] and self._line_x1(l) > im["x0"]), key=lambda l: l["top"])  # under it
        first = below[0]["text"].strip() if below else ""
        if small and above and SIGNED_RE.match(above[-1]["text"].strip()):
            return True
        if small and below and (re.fullmatch(r"Signed:?", first) or len(first.split()) <= 4
                                and any(ROLE_RE.search(l["text"]) for l in below[:3])):
            return True
        if first.startswith("©") or re.search(r"\bwww\.|\bISBN\b", first):
            return True
        if small and any(re.search(r"\bwww\.|\bISBN\b|^©", l["text"].strip()) for l in below[:3]):
            return True  # a barcode or publisher's logo on the back cover
        return im["page"] == 1 and im["top"] < 90 and small

    def _photo_captions(self) -> None:
        """Photos named by a short line printed just below them, with no "Figure N" (task sheets: "Asbestos
        lagging"). Photos in a row share caption lines, so only the words under each photo are its title. The
        lines become figure titles instead of loose small print."""
        self.photo_caps: dict[int, list[tuple[dict, str, dict]]] = {}
        self.skip_lines: set[int] = set()
        claimed: dict[int, int] = {}  # line index -> words claimed by photo captions
        handled: set[int] = set()  # images already named (one caption can name a grid of photos)
        self.not_pictures: set[int] = set()  # signatures and logos (id of the image)
        for im in self.images:
            if im["bottom"] - im["top"] < 40 or im["x1"] - im["x0"] < 60 or im["page"] in self.diagram_pages \
                    or im["page"] in self.table_pages or id(im) in handled:
                continue
            on_page = [(j, l) for j, l in enumerate(self.lines) if l["page"] == im["page"]]
            if self._signature_or_logo(im, [l for _, l in on_page]):
                self.not_pictures.add(id(im))
                continue
            if any(CAPTION_RE.match(l["text"]) and _caption_under(l["top"], im) for _, l in on_page):
                continue

            def under(l):
                return [w for w in l.get("words") or [] if im["x0"] - 4 <= w["x0"] <= im["x1"] + 2]

            first = next(((j, l) for j, l in on_page if im["bottom"] - 2 <= l["top"] <= im["bottom"] + 20
                          and under(l) and under(l)[0]["x0"] <= im["x0"] + 0.5 * (im["x1"] - im["x0"])
                          and l["size"] <= self.body_size and len(under(l)) <= 8), None)
            if not first:
                continue
            fw = first[1].get("words") or []
            gaps = [fw[k]["x0"] - fw[k - 1].get("x1", fw[k]["x0"]) for k in range(1, len(fw))]
            if fw and fw[-1].get("x1", 0) > im["x1"] + 20 and fw[0]["x0"] >= im["x0"] - 4 and max(gaps or [0]) < 12:
                # One caption for a grid of photos ("Top row: ... Bottom row: ..."): it runs past this photo.
                group, prev = [first], first[1]
                while True:
                    nxt = next(((j, l) for j, l in on_page if all(j != g[0] for g in group)
                                and 0 < l["top"] - prev["top"] < 14 and abs(l["x0"] - first[1]["x0"]) <= 4), None)
                    if not nxt:
                        break
                    group.append(nxt)
                    prev = nxt[1]
                right = max(w.get("x1", 0) for _, l in group for w in l.get("words") or [])
                grid = [g for g in self.images if g["page"] == im["page"] and g["bottom"] <= first[1]["top"] + 2
                        and g["bottom"] >= first[1]["top"] - 350 and g["x1"] > fw[0]["x0"] - 4 and g["x0"] < right + 4
                        and g["bottom"] - g["top"] >= 40]
                handled.update(id(g) for g in grid)
                union = {"page": im["page"], "top": min(g["top"] for g in grid), "bottom": max(g["bottom"] for g in grid),
                         "x0": min(g["x0"] for g in grid), "x1": max(g["x1"] for g in grid), "grid": len(grid) > 1}
                title = _join_all(l["text"].strip() for _, l in group)
                box = {"page": first[1]["page"], "top": first[1]["top"], "x0": fw[0]["x0"], "x1": union["x1"]}
                self.photo_caps.setdefault(min(j for j, _ in group), []).append((union, title, box))
                for j, l in group:
                    claimed[j] = len(l.get("words") or [])
                continue
            group, prev = [first], first[1]
            x0 = under(first[1])[0]["x0"]
            while True:
                nxt = next(((j, l) for j, l in on_page if all(j != g[0] for g in group)
                            and 0 < l["top"] - prev["top"] < 14 and under(l) and abs(under(l)[0]["x0"] - x0) <= 4
                            and len(under(l)) <= 8), None)
                if not nxt:
                    break
                group.append(nxt)
                prev = nxt[1]
            title = _join_all(" ".join(w["text"] for w in under(l)) for _, l in group)
            j0, l0 = group[0]
            box = {"page": l0["page"], "top": l0["top"], "x0": x0, "x1": im["x1"]}
            self.photo_caps.setdefault(min(j for j, _ in group), []).append((im, title, box))
            for j, l in group:
                claimed[j] = claimed.get(j, 0) + len(under(l))
        for j, n in claimed.items():
            if n >= 0.8 * len(self.lines[j].get("words") or [1]):
                self.skip_lines.add(j)
        # A caption group may start on a line that is not skipped: move it to the first skipped line, or drop it.
        for j in list(self.photo_caps):
            if j not in self.skip_lines:
                self.photo_caps.pop(j)

    # -------------------------------------------------- page furniture

    def _drop_overprint(self) -> None:
        """The same line printed twice a few points apart (a shadow or overprint, HSG150 figure 47): keep one."""
        kept, seen = [], []
        for l in self.lines:
            if any(o["page"] == l["page"] and o["text"] == l["text"] and abs(o["top"] - l["top"]) <= 8
                   and abs(o["x0"] - l["x0"]) <= 12 for o in seen[-6:]):
                continue
            seen.append(l)
            kept.append(l)
        # A small picture of the cover printed on page 1 (INDG453): its words repeat a title line at a fraction of
        # its size. Drop those words; text after a wide gap on the same line is kept.
        big = [l for l in kept if l["page"] == 1]
        out = []
        for l in kept:
            ws = l.get("words") or []
            if l["page"] == 1 and ws:
                src = next((b for b in big if b["size"] >= 2 * l["size"] and len(b["text"]) >= 12
                            and l["text"].startswith(b["text"][:12])), None)
                if src:
                    n = len(src["text"].split())
                    rest = ws[n:] if " ".join(w["text"] for w in ws[:n]) == src["text"] else []
                    if rest and rest[0].get("s", 0) > l["size"]:
                        out.append(_segment(l, rest))
                    continue
            out.append(l)
        self.lines = out

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
        sizes = _size_weights(self.lines)
        body = sizes.most_common(1)[0][0] if sizes else 10.0

        def is_furniture(l, b) -> bool:
            if (b, norm(l)) in furniture:
                return True
            t = l["text"].strip()
            # Part of a running head printed whole on other pages ("Health and Safety" alone on page 1).
            if len(t) >= 6 and any(fb == b and norm(l) in ft for fb, ft in furniture):
                return True
            # Logo text at the top right, in small print; a bare page number at the bottom.
            if b == "top" and l["x0"] > 0.6 * self.page_width and l["size"] < body:
                return True
            return b == "bottom" and bool(re.fullmatch(r"\d{1,3}", t))

        kept = []
        for l in self.lines:
            b = band(l)
            if b and is_furniture(l, b):
                m = PAGE_NO_RE.search(l["text"])
                if m:
                    self.printed[l["page"]] = m.group(1) or m.group(2)
                elif b == "bottom" and re.fullmatch(r"\d{1,3}", l["text"].strip()):
                    self.printed[l["page"]] = l["text"].strip()
                continue
            kept.append(l)
        self.lines = kept

    def _margin_labels(self) -> None:
        """L143 prints "Regulation 2", "ACOP 2" or "Guidance 2" in the left margin: the text that follows is the
        law itself, the Approved Code of Practice, or guidance (each has a different legal weight). Split these
        labels off the lines they share and remember where each one starts."""
        # "Regulation 2", "ACOP 3(1)–(2)" (L56 labels name the paragraphs they cover), "Summary"
        label_re = re.compile(r"^(Regulation|ACOP|Guidance|Schedule)\s+\d+[A-Z]?(\(\w+\)([–-]\(\w+\))?)?$|^(Summary|Guidance|ACOP)$")
        sizes = _size_weights(self.lines)
        body = sizes.most_common(1)[0][0] if sizes else 10.0
        lefts = Counter(round(l["x0"]) for l in self.lines if l["size"] == body)
        margin = max(150.0, (lefts.most_common(1)[0][0] if lefts else 0) - 4)  # where the text column starts
        # The label's word and its number may come as two lines ("ACOP" at the left, "2 Sporadic ..." at the
        # number's height): put them back together first.
        word_re = re.compile(r"^(Regulation|ACOP|Guidance)$")
        lone = [l for l in self.lines if word_re.match(l["text"].strip()) and l["x0"] < 120]
        merged: set[int] = set()
        joined: dict[int, dict] = {}
        for a in lone:
            for b in self.lines:
                bw = b.get("words") or []
                if b is not a and b["page"] == a["page"] and abs(b["top"] - a["top"]) <= 4 and bw \
                        and 120 <= bw[0]["x0"] < margin \
                        and re.fullmatch(r"\d+[A-Z]?(\(\w+\)([–-]\(\w+\))?)?", bw[0]["text"]):
                    rest = bw[1:]
                    joined[id(a)] = {**a, "words": [*a["words"], *bw], "text": f"{a['text'].strip()} {b['text']}",
                                     "aside": False}
                    if rest:  # the text after the number keeps its own place in the reading order
                        joined[id(a)]["top"] = b["top"]
                        joined[id(a)]["band"], joined[id(a)]["col"] = b.get("band", 0), b.get("col", 0)
                    merged.add(id(b))
                    break
        self.lines = [joined.get(id(l), l) for l in self.lines if id(l) not in merged]
        kept = []
        for l in self.lines:
            ws = l.get("words") or []
            if len(ws) > 1 and ws[0]["x0"] < margin - 10 and _is_bullet_word(ws[0], l["font"]) \
                    and abs(ws[1]["x0"] - margin - 4) <= 3 and PARA_RE.match(" ".join(w["text"] for w in ws[1:])):
                # A bullet in the margin before a numbered paragraph (HSG150 "• 224 Stepladders ..."): drop it.
                ws = ws[1:]
                l = {**l, "words": ws, "text": " ".join(w["text"] for w in ws), "x0": ws[0]["x0"],
                     "size": ws[0].get("s", l["size"]), "font": ws[0].get("f", l["font"])}
            if ws and ws[0]["x0"] < 120:
                k = 1
                while k < len(ws) and ws[k]["x0"] < margin:
                    k += 1
                label = " ".join(w["text"] for w in ws[:k])
                if label_re.match(label):
                    st = label.split()[0].lower()  # "summary": no legal status; a schedule is part of the law
                    self.markers.append((l["page"], l["top"], "regulation" if st == "schedule" else st))
                    rest = ws[k:]
                    if not rest:
                        continue
                    # The rest keeps its own size and font (the label is larger and bold).
                    l = {**l, "words": rest, "text": " ".join(w["text"] for w in rest), "x0": rest[0]["x0"],
                         "size": rest[0].get("s", l["size"]), "font": rest[0].get("f", l["font"])}
                    l = normalise_bullet(l)
            kept.append(l)
        self.lines = sorted(kept, key=lambda l: (l["page"], l.get("band", 0), l.get("col", 0), l["top"], l["x0"]))

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
        sizes = _size_weights(self.lines)
        self.body_size = sizes.most_common(1)[0][0] if sizes else 10.0
        lefts = Counter(round(l["x0"]) for l in self.lines if l["size"] == self.body_size)
        self.body_left = lefts.most_common(1)[0][0] if lefts else 0
        # Left margin page by page: books set mirrored margins on left and right pages (HSG248: 57 and 176).
        self.page_left: dict[int, int] = {}
        per: dict[int, Counter] = {}
        for l in self.lines:
            if l["size"] == self.body_size and len(l["text"]) > 40:
                per.setdefault(l["page"], Counter())[round(l["x0"])] += 1
        modes = {page: c.most_common(1)[0] for page, c in per.items()}
        common = Counter(x for x, n in modes.values() if n >= 5)
        for page, (x, n) in modes.items():
            # Only a margin many pages share (mirrored pages), not the left edge of one page's figure notes.
            if n >= 5 and common[x] >= max(3, 0.25 * len(modes)):
                self.page_left[page] = x
        fonts: Counter = Counter()
        for l in self.lines:
            if l["size"] == self.body_size:
                fonts[l["font"]] += len(l["text"])
        self.body_font = fonts.most_common(1)[0][0] if fonts else ""
        self.part_size = max((l["size"] for l in self.lines if PART_RE.match(l["text"].strip())), default=0.0)
        # Where running text starts: the left edges many long body-size lines share (columns, bullet indents).
        # A long label beside a drawing starts elsewhere.
        starts = Counter(round(l["x0"]) for l in self.lines if l["size"] >= self.body_size - 0.5 and len(l["text"].split()) >= 6)
        total = sum(starts.values())
        self.text_lefts = sorted({x for x, n in starts.items()
                                  if n + starts.get(x - 1, 0) + starts.get(x + 1, 0) >= max(5, 0.02 * total)})

    def left(self, l) -> float:
        """The left margin of running text on this line's page."""
        return self.page_left.get(l["page"], self.body_left) if hasattr(self, "page_left") else self.body_left

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
        # Smaller than body text (HSG264), or bold at body size (HSG227, where captions sit above), or a body-size
        # line set apart from what follows (L143: "Table 2 Examples of ..." then a gap, then the rows).
        return bool(CAPTION_RE.match(l["text"])) and (l["size"] < self.body_size or
                                                       (_is_bold(l["font"]) and l["size"] <= self.body_size)
                                                       or id(l) in self.body_captions)

    def _body_captions(self) -> None:
        self.body_captions: set[int] = set()
        for k, l in enumerate(self.lines):
            t = l["text"].strip()
            if not CAPTION_RE.match(t) or l["size"] != self.body_size or t.endswith(".") or len(t.split()) > 18:
                continue
            m = CAPTION_RE.match(t)
            after = t[m.end():].strip()
            nxt = self.lines[k + 1] if k + 1 < len(self.lines) else None
            nn = self.lines[k + 2] if k + 2 < len(self.lines) else None
            if after[:1].isupper() and (not nxt or nxt["page"] != l["page"]) and l["top"] > 0.75 * self.page_height:
                self.body_captions.add(id(l))  # the last line on its page: a caption under its figure (L56 figure 6)
                continue
            if not after[:1].isupper() or not nxt or nxt["page"] != l["page"]:
                continue
            if nxt["top"] - l["top"] >= 1.8 * l["size"]:
                self.body_captions.add(id(l))
            elif abs(nxt["x0"] - l["x0"]) <= 2 and not nxt["text"].rstrip().endswith(".") and nn \
                    and nn["page"] == l["page"] and nn["top"] - nxt["top"] >= 1.8 * l["size"]:
                self.body_captions.add(id(l))  # a caption wrapped onto a second line

    def is_callout(self, l) -> bool:
        """A key message in large bold italic (e.g. 'Take care, these dates are only a guideline'): a note."""
        return _is_bold(l["font"]) and "Italic" in l["font"] and self.body_size + 0.5 <= l["size"] < 2 * self.body_size

    def is_small(self, l) -> bool:
        return l["size"] <= self.body_size - 1.5

    def is_heading(self, l) -> bool:
        # Bold and larger than body text; or much larger, in another typeface (Decent Homes: 15pt sans headings over
        # 11pt Garamond text).
        bigger = (_is_bold(l["font"]) and self.body_size + 0.5 <= l["size"]) or \
            (l["size"] >= 1.3 * self.body_size and l["font"].split("-")[0] != self.body_font.split("-")[0])
        return (bigger and "Italic" not in l["font"] and l["size"] < 2 * self.body_size
                and self.left(l) - 6 <= l["x0"] <= self.left(l) + 25)

    def is_body_line(self, l) -> bool:
        """Ordinary running text at the left margin (not in a box, not a caption)."""
        return (l["size"] == self.body_size and not _is_bold(l["font"]) and abs(l["x0"] - self.left(l)) <= 3
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
                nxt_t = self.lines[j]["text"].strip()
                # A wrapped caption goes on mid-phrase; a table's first row ("General", "Handover form ...") starts
                # a new one with a capital after a caption that ended (HSG248 Table 2.1).
                if l["text"].startswith("Table") and nxt_t[:1].isupper() and not re.search(r"(\b(and|of|for|the|to|in|with|on|a|by|or)|[–\-,(])$",
                                                         prev["text"].strip()) and l.get("font") != self.lines[j].get("font") \
                        and len(prev["text"].strip()) < 60:
                    break
                cont.add(j)
                prev = self.lines[j]
                j += 1
        self.caption_continuations = cont
        for k, l in enumerate(self.lines):
            if not self.is_caption(l):
                continue
            got = []
            j = -1 if id(l) in self.body_captions and l["text"].startswith("Table") else k - 1  # body-size table captions sit above
            fig_above = self.captions_above and l["text"].startswith("Figure")
            if fig_above:
                j = -1  # the document prints figure captions above their figures: the labels are below
            stop_bottom = 72.0  # below the page header if nothing stops the walk
            while j >= 0 and self.lines[j]["page"] == l["page"]:
                x = self.lines[j]
                if self.is_body_line(x) or self.is_caption(x) or self.is_chapter(x) or self.is_heading(x) \
                        or j in cont or (self.rect_of(x) and not self.is_small(x)):
                    stop_bottom = x["top"] + x["size"] + 2
                    break
                got.append(j)
                j -= 1
            photo_above = not fig_above and any(im["page"] == l["page"] and _caption_under(l["top"], im) for im in self.images)
            if not got and not photo_above:  # nothing above: the caption may sit above its table or figure (HSG227)
                j = k + 1
                while j < len(self.lines) and self.lines[j]["page"] == l["page"]:
                    x = self.lines[j]
                    if j in cont:
                        j += 1
                        continue
                    # Under a body-size caption the rows are body-size too: only a numbered paragraph ends them.
                    body_stop = self.is_body_line(x) and (id(l) not in self.body_captions or
                                                          (PARA_RE.match(x["text"]) and abs(x["x0"] - self.left(x)) <= 3))
                    if body_stop or self.is_caption(x) or self.is_chapter(x) or self.is_heading(x) \
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
        if not re.search(r"[A-Za-z]", l["text"]):
            return False  # a large number or bullet on a section tab, not a title
        if l["size"] >= 2 * self.body_size or (l["size"] >= 1.5 * self.body_size
                                               and ("Cond" in l["font"] or re.search(r"(Hv|Bd|Blk|Md)Cn", l["font"]))):
            return True
        # Statutory instruments and similar: "PART 1", "SCHEDULE 2" and "CONTENTS" set larger than body text.
        # Contents pages list the Parts in a smaller size than the Parts themselves: only the largest count.
        if l["size"] > self.body_size + 0.4:
            t = l["text"].strip()
            if t.lower() in SKIP_TITLES:
                return l["size"] >= 1.3 * self.body_size  # not a "Contents" heading inside a chapter (L143)
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

    def _next_is(self, k: int, number: int) -> bool:
        """The next numbered line at the left margin (within 80 lines) carries this number: confirms a jump."""
        for x in self.lines[k + 1:k + 80]:
            m = PARA_RE.match(x["text"])
            if m and abs(x["x0"] - self.left(x)) <= 2:
                return int(m.group(1)) == number
        return False

    def _next_dec_is(self, k: int, prefix: str, number: int) -> bool:
        """The next "2.14"-style numbered line at the margin carries this number: confirms a longer jump (a
        paragraph the text layer lost, or one set inside a box)."""
        for x in self.lines[k + 1:k + 120]:
            m = DEC_PARA_RE.match(x["text"])
            if m and m.group(1) == prefix and abs(x["x0"] - self.left(x)) <= 2:
                return int(m.group(2)) == number
        return False

    def is_runin_heading(self, k: int, expected: int) -> bool:
        """A bold line at body size, at the left margin, just above the next numbered paragraph ("Interpretation"
        above "2. In these Regulations"): a heading. Legislation printed as PDF sets headings like this."""
        l = self.lines[k]
        ws = l.get("words") or []
        if not ws or not all(w.get("b") for w in ws) or l["size"] != self.body_size or l["text"].rstrip().endswith(".") \
                or abs(l["x0"] - self.left(l)) > 20 or k + 1 >= len(self.lines):
            return False
        prev = self.lines[k - 1] if k else None
        if prev and prev["page"] == l["page"] and 0 < l["top"] - prev["top"] < 1.8 * l["size"] \
                and all(w.get("b") for w in prev.get("words") or [{}]):
            return False  # the second line of a bold sentence, not a heading of its own
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
        diagram_done: set[int] = set()
        diagram_lines: set[int] = set()
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
                m_annex = re.match(r"^Appendix\s+(\d+)\s*:?\s*Annex\s+(\d+)\s*(.*)$", title, flags=re.I)
                if m_annex:
                    n, a, t = m_annex.groups()
                    chapter = self.new(f"appendix-{n}-annex-{a}", "appendix", None, f"{n}.{a}", t or f"Annex {a}",
                                       [self.title, title], l["page"])
                    counter_key = chapter["id"]
                elif m_part:
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
            # ---- a whole page that is one picture (flow chart, illustrated key)
            if l["page"] in self.diagram_pages and l["page"] not in diagram_done:
                diagram_done.add(l["page"])
                rest = [j for j in range(k_line, len(self.lines)) if self.lines[j]["page"] == l["page"]]
                ws = l.get("words") or []
                titled = bool(ws) and all(w.get("b") for w in ws) and len(ws) <= 14 and l["size"] >= self.body_size
                title = l["text"] if titled else (parent["title"] or self.title)
                sec = self.new(f"figure-p{l['page']}", "figure", parent, None, title,
                               [*parent["heading_path"], title], l["page"])
                labels = [self.lines[j] for j in (rest[1:] if titled else rest)]
                sec["labels"] = [x["text"] for x in labels]
                sec["caption_box"] = {"page": l["page"], "top": l["top"], "x0": l["x0"], "x1": self.page_width - 36}
                sec["diagram"] = True
                bottom = max(x["top"] + x["size"] + 2 for x in [l, *labels])
                self.span(sec, l["page"], l["top"], bottom)
                diagram_lines.update(rest)
                continue
            # ---- a whole page that is one ruled table with no caption
            if l["page"] in self.table_pages and l["page"] not in diagram_done:
                diagram_done.add(l["page"])
                rest = [j for j in range(k_line, len(self.lines)) if self.lines[j]["page"] == l["page"]]
                ws = l.get("words") or []
                titled = bool(ws) and all(w.get("b") for w in ws) and len(ws) <= 14 and l["size"] >= self.body_size \
                    and not any(t["page"] == l["page"] and t["top"] - 2 <= l["top"] <= t["bottom"] for t in self.doc_tables)
                title = l["text"] if titled else (parent["title"] or self.title)
                rows = [self.lines[j] for j in (rest[1:] if titled else rest)]
                sec = self.new(f"table-p{l['page']}", "table", parent, None, title, [*parent["heading_path"], title],
                               l["page"], "\n".join(x["text"] for x in rows))
                sec["caption_box"] = {"page": l["page"], "top": l["top"], "x0": l["x0"], "x1": self.page_width - 36}
                self.span(sec, l["page"], l["top"], max(x["top"] + x["size"] + 2 for x in [l, *rows]))
                diagram_lines.update(rest)
                continue
            if k_line in diagram_lines:
                continue
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
            # ---- photos named by the short line below them
            if k_line in self.skip_lines:
                for im, title, box in sorted(self.photo_caps.get(k_line, []), key=lambda c: c[2]["x0"]):
                    k = 1 + sum(1 for s in self.sections if s["id"].startswith("photo-"))
                    sec = self.new(f"photo-{k}", "figure", parent, None, title,
                                   [*parent["heading_path"], title], l["page"])
                    sec["labels"] = []
                    sec["caption_box"] = box
                    sec["image_bbox"] = {k2: im[k2] for k2 in ("page", "top", "bottom", "x0", "x1")}
                    if im.get("grid") and self.graphics is not None:  # a grid of photos: all of them, not trimmed
                        sec["images_bbox"] = dict(sec["image_bbox"])
                    self.span(sec, l["page"], im["top"], box["top"] + l["size"] + 2)
                continue
            # ---- captions (figures and tables); two captions may share a line
            if self.is_caption(l):
                prev_caption_line = []
                for cap in self.split_captions(l):
                    kind = cap["kind"]
                    sid = re.sub(r"[().–]", lambda m: "" if m.group(0) in "()" else "-", f"{kind}-{cap['number']}").lower()  # "Table 2.1" -> table-2-1
                    if sid in self.by_id and re.search(r"\(?continued\)?$", cap["title"], flags=re.I):
                        # "Table 5 ... (continued)" on the next page: more rows of the same table
                        captions_on_page.append(self.by_id[sid])
                        prev_caption_line.append(self.by_id[sid])
                        continue
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
                m_fn = re.match(r"^\(([a-z])\)\s", l["text"].lstrip())  # "(a) 1985 c. 70." (legislation footnotes)
                if m_fn and last_body and l["top"] > 0.75 * self.page_height:
                    mark = m_fn.group(0).strip()
                if (mark in ("*", "†", "‡") or len(mark) == 3) and last_body:  # footnotes may start left of the margin
                    owner = next((s for s in reversed(self.sections)
                                  if s["type"] in ("paragraph", "text", "box", "note") and mark in s["text"]), last_body)
                    owner["footnotes"].append(l["text"].strip())
                    last_footnote = (owner, l)
                    continue
                if last_footnote and last_footnote[1]["page"] == l["page"] and 0 < l["top"] - last_footnote[1]["top"] < 14 \
                        and -6 < l["x0"] - last_footnote[1]["x0"] < 20:  # wrapped lines may hang under the text
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
                    # A note led by a few bold words ("Summary This regulation ...") takes them as its title.
                    ws0 = inside[0].get("words") or [] if inside else []
                    lead = []
                    for w in ws0:
                        if not w.get("b"):
                            break
                        lead.append(w["text"])
                    title = None
                    if 0 < len(lead) <= 3 and len(lead) < len(ws0) and text.startswith(" ".join(lead)):
                        title = " ".join(lead).rstrip(":")
                        text = text[len(" ".join(lead)):].lstrip(" :")
                    elif lead and len(lead) == len(ws0) <= 6 and len(inside) > 1 and not BULLET_RE.match(inside[0]["text"]):
                        title = inside[0]["text"].strip().rstrip(":")  # a bold title line at the top of the box
                        text = ""
                        for x in inside[1:]:
                            text = _join(text, x["text"])
                    sec = self.new(f"note-{k}", "note", parent, None, title,
                                   [*parent["heading_path"], title or "Note"], l["page"], text)
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
            m_dec = DEC_PARA_RE.match(l["text"])
            prefix = (("A" if chapter.get("type") == "appendix" else "") + str(chapter.get("number"))) \
                if chapter.get("number") else None  # "A1.9" in appendix 1
            if m_dec and prefix and m_dec.group(1) == prefix \
                    and (abs(l["x0"] - self.left(l)) <= 2 or m_dec.group(3)[:1].isupper()):  # also beside a figure
                key = f"dec-{chapter['id']}"
                want = counters.get(key, 0) + 1
                got = int(m_dec.group(2))
                prev = self.lines[k_line - 1] if k_line else None
                spaced = prev is None or prev["page"] != l["page"] or l["top"] - prev["top"] >= 1.6 * l["size"]
                if got == want or (want < got <= want + 3 and spaced) or \
                        (got > want and spaced and self._next_dec_is(k_line, prefix, got + 1)):
                    if got != want:
                        self.issues.append(f"paragraph numbers jump to {m_dec.group(1)}.{got} on file page {l['page']}")
                    counters[key] = got
                    n = f"{m_dec.group(1)}.{got}"
                    para = self.new(f"para-{m_dec.group(1).lower()}-{got}", "paragraph", parent, n, None,
                                    [*parent["heading_path"], f"Paragraph {n}"], l["page"], _join("", m_dec.group(3)),
                                    top=l["top"])
                    last_body = para
                    continue
            m = PARA_RE.match(l["text"])
            dotted = bool(m) and l["text"][len(m.group(1))] == "."
            prev = self.lines[k_line - 1] if k_line else None
            # A paragraph starts after a gap; a number that wraps to the start of a line has none.
            spaced = prev is None or prev["page"] != l["page"] or l["top"] - prev["top"] >= 1.6 * l["size"]
            num = int(m.group(1)) if m else 0
            near = abs(l["x0"] - self.left(l))
            if m and ((num == expected and (near <= 2 or (dotted and near <= 20) or (spaced and near <= 8)))
                      or (expected < num <= expected + 3 and near <= 2 and spaced and self._next_is(k_line, num + 1))):
                if num != expected:
                    self.issues.append(f"paragraph numbers jump from {expected - 1} to {num} on file page {l['page']}")
                counters[counter_key] = num
                n = m.group(1)
                sid = f"para-{n}" if counter_key == "main" else f"{counter_key}-para-{n}"
                para = self.new(sid, "paragraph", parent, n, None, [*parent["heading_path"], f"Paragraph {n}"],
                                l["page"], _join("", m.group(2).lstrip("—– ")), top=l["top"])
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
            "title": self.title, "parser": PARSER, "page_width": self.page_width,
            "sections": self.sections, "definitions": [], "issues": self.issues, "checks": self.checks,
        }

    # -------------------------------------------------- captions, labels, tables, images

    def split_captions(self, l) -> list[dict]:
        words = l.get("words") or [{"x0": l["x0"], "text": w} for w in l["text"].split()]
        starts = [k for k in range(len(words) - 1)
                  if words[k]["text"] in ("Figure", "Table") and re.match(r"^A?\d+(\.\d+)?([a-z]|\([a-z]\)([–-]\([a-z]\))?)?[:.]?$", words[k + 1]["text"])]
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
        drawn: list[dict] = []  # drawings found from their labels (no caption)
        for b in blocks:
            page, top, bottom = b[0]["page"], b[0]["top"], b[-1]["top"]
            near = [c for c in captions if c["caption_box"]["page"] == page and
                    (0 <= c["caption_box"]["top"] - bottom <= 100 or 0 <= top - c["caption_box"]["top"] <= 40)]
            near.sort(key=lambda c: abs(c["caption_box"]["top"] - bottom))
            if self.captions_above:  # labels belong to the figure caption printed above them
                over = [c for c in captions if c["type"] == "figure" and c["caption_box"]["page"] == page
                        and 0 <= top - c["caption_box"]["top"] <= 400]
                near = sorted(over, key=lambda c: top - c["caption_box"]["top"])[:1] or near
            if not near and not any(c["type"] == "table" and c["caption_box"]["page"] == page for c in captions):
                # Labels high up in a tall drawing: the figure whose caption is further below, with no running
                # text in between (HSG150 figures 37, 41, 45).
                far = [c for c in captions if c["type"] == "figure" and not c.get("image_bbox")
                       and c["caption_box"]["page"] == page and 0 <= c["caption_box"]["top"] - bottom <= 450
                       and not any(x["page"] == page and bottom < x["top"] < c["caption_box"]["top"]
                                   and self.is_body_line(x) and len(x["text"].split()) >= 6 for x in self.lines)]
                near = sorted(far, key=lambda c: c["caption_box"]["top"] - bottom)[:1]
            if not near and top < 200:
                # A table running over from the bottom of the previous page, with no "continued" caption (L153 Table 1).
                prev = [c for c in captions if c["type"] == "table"
                        and str(page - 1) in c.get("spans", {}) and c["spans"][str(page - 1)][1] > self.page_height - 140]
                if prev:
                    c = prev[-1]
                    self.span(c, page, top, bottom + b[-1]["size"] + 2)
                    c["text"] = "\n".join(x for x in [c["text"], *[x["text"] for x in b]] if x)
                    continue
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
            if not any(re.search(r"[A-Za-z]", x["text"]) for x in b) or all(len(x["text"].strip()) <= 2 for x in b):
                continue  # a stray number (a section tab) or the subscripts of a formula, not content
            joins_table = key in unnamed and str(page) in unnamed[key].get("spans", {})
            words = [len(x["text"].split()) for x in b]
            near_fig = next((f for f in drawn if f["caption_box"]["page"] == page
                             and 0 <= top - f["spans"][str(page)][1] <= 120), None)
            if near_fig and sum(words) / len(b) <= 4:  # more labels of the same drawing
                near_fig["labels"].extend(texts)
                near_fig["caption_box"]["top"] = bottom
                self.span(near_fig, page, top, bottom + b[-1]["size"] + 2)
                continue
            if len(b) >= 4 and sum(words) / len(b) <= 3.5 and (not joins_table or not self.is_tabular(b)) \
                    and self.drawn_between(page, top, bottom + b[-1]["size"]):
                # Scattered short labels ("h", "20 mm", "White 'a' on a black background"): a drawing with no
                # caption, not a table (L143 Schedule 2, the asbestos label).
                k = 1 + sum(1 for s in self.sections if s["id"].startswith(f"{key}-figure-"))
                f = self.new(f"{key}-figure-{k}", "figure", parent, None, parent["title"],
                             [*parent["heading_path"], f"Figure ({parent['title']})"], page)
                f["labels"], f["drawn"] = texts, True
                f["caption_box"] = {"page": page, "top": bottom, "x0": min(x["x0"] for x in b), "x1": self.page_width - 36}
                self.span(f, page, top, bottom + b[-1]["size"] + 2)
                drawn.append(f)
                continue
            if not joins_table and not self.is_tabular(b):
                # Small print set as sentences (publishing notes, a key under a list): text, not a table.
                k = 1 + sum(1 for s in self.sections if s["parent_id"] == key and s["type"] == "text")
                text = ""
                for x in b:
                    text = _join(text, x["text"])
                s = self.new(f"{key}-text-{k}", "text", parent, None, None, [*parent["heading_path"], "Text"], page, text)
                s["small_print"] = True
                continue
            t = unnamed.get(key)
            if t is None:
                k = 1 + sum(1 for s in self.sections if s["parent_id"] == key and s["type"] == "table")
                t = self.new(f"{key}-table-{k}", "table", parent, None, parent["title"],
                             [*parent["heading_path"], f"Table ({parent['title']})"], page)
                unnamed[key] = t
            t["text"] = "\n".join(x for x in [t["text"], *texts] if x)
            self.span(t, page, top, bottom + b[-1]["size"] + 2)

    def is_tabular(self, block: list[dict]) -> bool:
        """Small-print lines look like a table when they are cut into cells: wide gaps inside lines, or a ruled
        table on the page around them. Lines of sentences with ordinary word spaces are prose."""
        page, top, bottom = block[0]["page"], block[0]["top"], block[-1]["top"]
        if len(block) == 1 and len(block[0]["text"].split()) >= 4 and not any(
                t["page"] == page and t["top"] - 2 <= top <= t["bottom"] + 2 for t in self.doc_tables):
            return False  # one line of words outside any ruled table: a sentence
        if any(t["page"] == page and t["top"] - 5 <= bottom and t["bottom"] + 5 >= top for t in self.doc_tables):
            return True
        gapped = 0
        for x in block:
            ws = x.get("words") or []
            if any(ws[k]["x0"] - ws[k - 1].get("x1", ws[k - 1]["x0"] + 5 * len(ws[k - 1]["text"])) > max(6.0, 1.5 * x["size"])
                   for k in range(1, len(ws))):
                gapped += 1
        return gapped >= max(1, 0.25 * len(block)) or len(block) == 1 and len(block[0]["text"].split()) <= 3

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
            if s.get("images_bbox"):  # a stack of photos under one caption: all of them, as placed
                im = s["images_bbox"]
                s["area"] = {"page": im["page"], "top": im["top"], "bottom": im["bottom"], "x0": im["x0"], "x1": im["x1"]}
                im = s.pop("image_bbox")  # no single photo to trim (render_images trims image_bbox photos)
                s["images_bbox"]["single"] = im
            elif s.get("image_bbox"):
                im = s["image_bbox"]
                # The photo only: its caption is kept as text.
                s["area"] = {"page": im["page"], "top": im["top"], "bottom": im["bottom"], "x0": im["x0"], "x1": im["x1"]}
            else:
                top, bottom = s.get("spans", {}).get(str(cap["page"]), (cap["top"] - 200, cap["top"] + 12))
                if self.graphics is not None and not s.get("diagram"):
                    # Cut from the drawing's ink (shapes, images, labels) between the running text and the caption.
                    ink = self.drawn_ink_area(s, top, bottom) if s.get("drawn") else self.caption_ink_area(s, top, bottom)
                    if ink:
                        s["area"] = ink
                        continue
                if not s.get("drawn") and not s.get("diagram") and bottom - top < 40 and not s.get("labels"):
                    # A drawing with no words of its own above its caption (a utility plan, a wired plug): the
                    # picture is the space between the text above and the caption.
                    on = [l for l in self.lines if l["page"] == cap["page"] and l["top"] + l["size"] < cap["top"] - 2]
                    above = [l["top"] + l["size"] + 2 for l in on if l["x0"] < cap["x1"]]
                    top = max(above) + 4 if above else 72.0
                    bottom = cap["top"] - 1
                elif s.get("drawn"):
                    # A drawing found from its labels: the picture reaches up to the text above it and down to the
                    # text below it, beyond its outermost labels.
                    on = [l for l in self.lines if l["page"] == cap["page"] and l["text"] not in s["labels"]]
                    above = [l["top"] + l["size"] + 2 for l in on if l["top"] + l["size"] < top]
                    below = [l["top"] - 2 for l in on if l["top"] > bottom]
                    top, bottom = (max(above) + 6 if above else 72.0), (min(below) if below else self.page_height - 45)
                x0, x1 = 36.0, self.page_width - 36.0
                shared = [o for o in self.sections if o is not s and o["type"] == "figure" and o.get("caption_box")
                          and o["caption_box"]["page"] == cap["page"] and abs(o["caption_box"]["top"] - cap["top"]) < 3]
                if shared:  # figures side by side above one caption line: each takes its caption's column
                    x0 = max(x0, cap["x0"] - 10)
                    if cap["x1"] < 10_000:
                        x1 = cap["x1"] - 4
                if s.get("diagram"):  # a whole page: from the leftmost to the rightmost text on it
                    pw, ph = self.page_size(cap["page"])
                    on = [l for l in self.lines if l["page"] == cap["page"]]
                    x0 = max(0.0, min([x0, *(l["x0"] - 8 for l in on)]))
                    x1 = min(pw, max([min(x1, pw - 36), *(w.get("x1", l["x0"]) + 8 for l in on for w in l.get("words") or [])]))
                    if self.graphics is not None:  # and every box, arrow, table rule and image the drawing has
                        g = self.ink_extent(cap["page"], {"top": top, "bottom": bottom, "x0": x0, "x1": x1})
                        top, bottom = g["top"], g["bottom"] + 3
                        x0, x1 = max(0.0, g["x0"] - 3), min(pw, g["x1"] + 3)
                s["area"] = {"page": cap["page"], "top": max(0.0, top - 6), "bottom": bottom, "x0": x0, "x1": x1}

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

    def _stacked_above(self, im: dict) -> list[dict]:
        """The image and the images stacked straight above it in the same column, each less than 20 points
        above the next, with no text line between them (HSG33 Figure 36(a)-(c), CIS69 Figure 2)."""
        stack = [im]
        while True:
            cur = stack[-1]
            up = [x for x in self.images if x["page"] == im["page"] and all(x is not y for y in stack)
                  and id(x) not in self.not_pictures and cur["top"] - 20 <= x["bottom"] <= cur["top"] + 2
                  and min(x["x1"], cur["x1"]) - max(x["x0"], cur["x0"]) >= 0.5 * min(x["x1"] - x["x0"], cur["x1"] - cur["x0"])
                  and x["bottom"] - x["top"] >= 30]
            up = [x for x in up if not any(l["page"] == im["page"] and x["bottom"] - 2 <= l["top"] <= cur["top"] - 2
                                           and l["x0"] < max(x["x1"], cur["x1"]) and self._line_x1(l) > min(x["x0"], cur["x0"])
                                           for l in self.lines)]
            if not up:
                return stack
            stack.append(max(up, key=lambda x: x["bottom"]))

    def _photo_cluster(self, im: dict) -> list[dict]:
        """The image and every image joined to it in a block of photos (less than 20 points apart, side by side
        or stacked, no text line between): the parts of a figure whose caption names them, "Figure 35(a)-(c)"."""
        group = [im]
        grown = True
        while grown:
            grown = False
            for x in self.images:
                if x["page"] != im["page"] or any(x is g for g in group) or id(x) in self.not_pictures \
                        or x["bottom"] - x["top"] < 30:
                    continue
                for g in group:
                    vgap = max(x["top"] - g["bottom"], g["top"] - x["bottom"])
                    hgap = max(x["x0"] - g["x1"], g["x0"] - x["x1"])
                    if vgap <= 20 and hgap <= 20 and not any(
                            l["page"] == im["page"] and min(x["bottom"], g["bottom"]) - 2 <= l["top"] <= max(x["top"], g["top"])
                            and l["x0"] < max(x["x1"], g["x1"]) and self._line_x1(l) > min(x["x0"], g["x0"]) for l in self.lines):
                        group.append(x)
                        grown = True
                        break
        return group

    def _labelled_image(self, im: dict) -> bool:
        """Short label lines beside an image, within its height and less than 100 points from its sides: the
        image is part of a labelled drawing (HSG247 Figure 8.2), cut from its ink with the labels, not trimmed
        to its pixels."""
        if self.graphics is None:
            return False
        return sum(1 for l in self.lines if l["page"] == im["page"] and im["top"] <= l["top"] <= im["bottom"] - 4
                   and not self.is_stopper(l) and l["size"] <= self.body_size + 1
                   and len(re.findall(r"[A-Za-z]", l["text"])) >= 3 and (im["x0"] - 100 <= self._line_x1(l) <= im["x0"] + 2
                                                   or im["x1"] - 2 <= l["x0"] <= im["x1"] + 100)) >= 2

    def _text_beside(self, c: dict, im: dict) -> None:
        """Running text printed beside a photo is not part of it: the photo's crop stops before it (right_limit,
        used by render_images)."""
        beside = [round(l["x0"]) for l in self.lines if l["page"] == im["page"] and l["x0"] >= im["x1"] - 5
                  and im["top"] - 2 <= l["top"] <= im["bottom"] and self.is_stopper(l)]
        xs = [x for x, n in Counter(beside).items() if n >= 2]  # a paragraph, not one long label
        # and another photo beside it (HSG33 Figures 31 and 32 side by side, captions at different heights)
        xs += [x["x0"] for x in self.images if x["page"] == im["page"] and x is not im and x["x0"] >= im["x1"] - 5
               and x["top"] < im["bottom"] and x["bottom"] > im["top"] and x["bottom"] - x["top"] >= 30]
        cap = c["caption_box"]
        nxt = [o["caption_box"]["x0"] for o in self.sections if o["type"] == "figure" and o is not c and o.get("caption_box")
               and o["caption_box"]["page"] == cap["page"] and abs(o["caption_box"]["top"] - cap["top"]) < 6
               and o["caption_box"]["x0"] > cap["x0"]]
        if xs and min(xs) > cap["x0"] + 30:
            c["right_limit"] = min([min(xs) - 2, *nxt])  # never past the next caption on the same line

    def place_images(self, captions: list[dict]) -> None:
        named = [s["image_bbox"] for s in self.sections if s["id"].startswith("photo-")]
        claimed: set[int] = set()  # images stacked over a lower one that took the caption
        for im in sorted(self.images, key=lambda i: -i["bottom"]) if self.graphics is not None else self.images:
            if id(im) in self.not_pictures or id(im) in claimed:
                continue  # a signature or a logo, or part of a stack of photos with one caption
            if self.graphics is not None and (im["bottom"] - im["top"] < 20 or im["x1"] - im["x0"] < 20):
                continue  # a tile of a picture cut into strips (HSG47 plans): figure_areas takes all of its ink
            if im["page"] in self.diagram_pages or im["page"] in self.table_pages or any(n["page"] == im["page"] and n["top"] <= im["top"] + 1
                                                        and im["bottom"] <= n["bottom"] + 1 and n["x0"] <= im["x0"] + 1
                                                        and im["x1"] <= n["x1"] + 1 for n in named):
                continue  # inside a whole-page picture, or a photo named by the line below it
            if self.captions_above:  # the caption just above the image, starting over it
                over = [c for c in captions if c["type"] == "figure" and c["caption_box"]["page"] == im["page"]
                        and not c.get("image_bbox") and im["top"] - 45 <= c["caption_box"]["top"] <= im["top"] + 2
                        and im["x0"] - 15 <= c["caption_box"]["x0"] <= im["x1"]]
                if over:
                    c = max(over, key=lambda c: c["caption_box"]["top"])
                    if self._labelled_image(im):
                        continue  # figure_areas cuts it from its ink with the labels
                    cap = c["caption_box"]
                    cap["bottom"] = max([cap["top"] + 10, *(l["top"] + l["size"] for l in self.lines if l["page"] == cap["page"]
                                                           and cap["top"] <= l["top"] < im["top"] - 2
                                                           and abs(l["x0"] - cap["x0"]) <= 3)])
                    c["image_bbox"] = {k: im[k] for k in ("page", "top", "bottom", "x0", "x1")}
                    c["caption_above"] = True
                    others = [o["caption_box"] for o in captions if o is not c and o["caption_box"]["page"] == im["page"]]
                    group = [x for x in self._photo_cluster(im) if x is im or not any(
                        x["top"] - 45 <= o["top"] <= x["top"] + 2 and x["x0"] - 15 <= o["x0"] <= x["x1"] for o in others)]
                    if len(group) > 1:  # a block of photos under one caption: one figure
                        claimed.update(id(x) for x in group)
                        c["images_bbox"] = {"page": im["page"], "top": min(x["top"] for x in group),
                                            "bottom": max(x["bottom"] for x in group),
                                            "x0": min(x["x0"] for x in group), "x1": max(x["x1"] for x in group)}
                    self._text_beside(c, im)
                    continue
            below = [c for c in captions if c["type"] == "figure" and c["caption_box"]["page"] == im["page"]
                     and _caption_under(c["caption_box"]["top"], im)
                     and c["caption_box"]["x0"] <= im["x1"] and c["caption_box"]["x0"] >= im["x0"] - 10]
            if not below:
                below = [c for c in captions if c["type"] == "figure" and c["caption_box"]["page"] == im["page"]
                         and _caption_under(c["caption_box"]["top"], im)]
            if below:
                c = min(below, key=lambda c: (abs(c["caption_box"]["top"] - im["bottom"]), abs(c["caption_box"]["x0"] - im["x0"])))
                if not c.get("image_bbox") and self._labelled_image(im):
                    pass  # figure_areas cuts it from its ink with the labels
                elif not c.get("image_bbox"):
                    c["image_bbox"] = {k: im[k] for k in ("page", "top", "bottom", "x0", "x1")}
                    if self.graphics is not None:
                        parts = re.search(r"\([a-z]\)\s*[–-]\s*\([a-z]\)|^\S*\d[a-z]\)?\s+(and|&)\s+\(?[a-z]\b",
                                          f"{c.get('number') or ''} {c.get('title') or ''}"[:40])  # "35(a)–(c)", "12a and b"
                        stack = self._photo_cluster(im) if parts else self._stacked_above(im)
                        if len(stack) > 1:  # photos stacked over one caption, nothing between them: one figure
                            claimed.update(id(x) for x in stack)
                            c["images_bbox"] = {"page": im["page"], "top": min(x["top"] for x in stack),
                                                "bottom": im["bottom"], "x0": min(x["x0"] for x in stack),
                                                "x1": max(x["x1"] for x in stack)}
                        self._text_beside(c, im)
            elif im["page"] != 1 and im["bottom"] - im["top"] >= 30 and im["x1"] - im["x0"] >= 30:  # not icons
                self.issues.append(f"image on file page {im['page']} at {im['top']} has no caption below it")


def build_tree(doc: dict, meta: dict, fixes: list[dict] | None = None) -> dict:
    return Builder(doc, meta, fixes).build()


def read_guidance(path) -> dict:
    """read_pdf as this parser uses it: with drawn shapes and page sizes, so pictures are told from pages of
    words (Builder.drawn_page, drawn_between) and cut to their ink (Builder.ink_extent)."""
    return read_pdf(path, graphics=True)


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
              ink: int = 235, gap_pt: float = 4.0, below: bool = False) -> dict:
    """The photo's real box, from the rendered page. pdfplumber's image box can be wider or taller than the
    photo that is drawn (white padding, soft edges), so a neighbour photo can fall inside it, and words printed
    on the photo can fall outside it (HSG227 figures 3, 5, 6, 9). Find the block of non-white pixels that sits
    directly above the caption and starts in the caption's column. right_limit is where the next caption on the
    same line starts (or the page margin). Falls back to the image box if nothing is found.
    below=True: the photo is below its caption (Home Office fire safety guides). The search starts under the
    caption's bottom ("bottom" in caption, else one line below its top) and takes the highest block."""
    if caption["page"] != area["page"]:
        return area
    left = max(0.0, min(area["x0"], caption["x0"]) - 6)
    right = max(area["x1"] + 6, right_limit - 4)
    if below:
        top = caption.get("bottom", caption["top"] + 12) + 1
        bottom = area["bottom"] + 6
    else:
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

    # 1. Rows, from a narrow strip at the caption's left edge: the lowest tall block above the caption (or the
    # highest below it).
    pick = 0 if below else -1
    cap_x = int((max(caption["x0"], left) - left) * scale)
    rows = runs_y(cap_x, min(w, cap_x + int(30 * scale)))
    if not rows:
        return area
    y0, y1 = rows[pick]
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
        y0, y1 = rows[pick]
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
            page = pdf[n - 1]
            media = page.get_mediabox()
            if tuple(page.get_cropbox()) != tuple(media):
                # pdfplumber measures from the media box; pypdfium2 renders the crop box. Render the media box
                # so the two agree (Home Office guides have a 29pt bleed around the crop box).
                page.set_cropbox(*media)
            cache[n] = page.render(scale=scale).to_pil()
        return cache[n]

    (out_dir / "figures").mkdir(parents=True, exist_ok=True)
    (out_dir / "pages").mkdir(parents=True, exist_ok=True)
    for s in tree["sections"]:
        if s["type"] == "figure" and s.get("area"):
            a = s["area"]
            if s.get("image_bbox"):
                limit = s.get("right_limit") or _next_caption_x(tree, s)  # a parser may know the photo's column
                a = s["area"] = photo_box(page_image(a["page"]), a, s["caption_box"], scale, limit,
                                          below=bool(s.get("caption_above")))
            if a["x1"] <= a["x0"] or a["bottom"] <= a["top"]:  # empty or upside-down box (fso-guidance-collection)
                tree.setdefault("issues", []).append(f"figure {s['id']}: empty image box {a}, image not cut")
                continue
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
        if src and parser_for(src, r["version_id"]) not in (None, "parse_pdf"):
            continue  # this file goes to another parser (sources.yaml parser.files)
        raw = root / r["raw_path"]
        if not raw.exists():
            print(f"missing raw file: {r['raw_path']}")
            continue
        tree = build_tree(read_guidance(raw), {**r, "title": src["title"] if src else a.source}, fixes=load_fixes(a.source))
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
