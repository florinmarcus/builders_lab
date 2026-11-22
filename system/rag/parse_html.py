"""Parse a GOV.UK or HSE web page into a document tree.

    python -m system.rag.parse_html --source hmrc-cis-340

Design: architecture/design/regulations-corpus.md, ADR 0010. The tree has the same shape as the one
from parse_pdf, so system/rag/chunk.py works on it unchanged.

Two kinds of page:
- GOV.UK pages saved by our harvester: clean HTML, an <h1> and a <div class="govspeak"> body.
- HSE pages saved whole: the full site with header, menus, breadcrumbs, sidebar and footer. We keep
  only the main content (the <main> element or the HSE content container) and drop the rest.

What build_tree does:
- h1 is the page title (else <title>, else the part title);
- h2 starts a chapter ("1. Introduction" gives chapter-1, "Appendix A" gives appendix-a);
- h3 and h4 start headings under the latest higher heading;
- a heading or paragraph that starts with a section number ("1.2", "2.10", "A.3") under the chapter
  with that number becomes a numbered paragraph (id "para-1.2"); its text runs until the next numbered
  paragraph or heading;
- other text (paragraphs, list items, loose text in divs) under the same heading is grouped into
  "text" sections of about 1,500 characters at most;
- list items keep "• " (or "1. ", "2. " in ordered lists) and their own line;
- every <table> becomes a "table" section with columns, a full grid (colspan and rowspan expanded)
  and grid_source "html"; no model check is needed;
- images are skipped; alt text longer than 20 characters is kept as a "figure" section.

Anything odd goes into "issues". There are no model checks ("checks" is empty).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter

import lxml.html

from system.rag.corpus import CORPUS_DIR, slugify

PARSER = "html/0.1"
TEXT_LIMIT = 1500  # a text section is closed before it would pass this many characters
MIN_ALT = 20       # shorter alt text is not worth a figure section

# Elements that are never content.
DROP_TAGS = {"script", "style", "noscript", "nav", "aside", "footer", "header", "form", "button", "iframe",
             "svg", "template", "input", "select", "textarea", "label", "dialog"}
# Classes and ids of page furniture (HSE and GOV.UK site parts).
DROP_MARKS = ("breadcrumb", "back-to-top", "sidebar", "feedback", "cookie", "visually-hidden", "related",
              "skip", "share", "print-link", "gem-c-contents", "contents-list", "lastupdated", "search",
              "report-a-problem", "hse-page-header__aside", "pagination", "next-page", "printable-version")
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "table", "div", "section", "article",
              "main", "figure", "figcaption", "blockquote", "pre", "dl", "dt", "dd", "hr", "details", "summary",
              "address", "fieldset", "img", "body"}
LINE_TAGS = {"p", "figcaption", "pre", "dt", "dd", "summary"}

CHAPTER_NUM_RE = re.compile(r"^(\d{1,2})\.?\s+(\S.*)$")
APPENDIX_RE = re.compile(r"^(?:Appendix|Annex)\s+([A-Z]|\d{1,2})\b", re.IGNORECASE)
PARA_NUM_RE = re.compile(r"^((?:\d{1,2}|[A-Z])(?:\.\d{1,3})+)\.?\s+(\S.*)$", re.DOTALL)
TITLE_SUFFIX_RE = re.compile(r"\s+[-–|]\s+(HSE|GOV\.UK)$")
INVISIBLE_RE = re.compile("[\\u00ad\\u200b\\u200c\\u200d\\u2060\\ufeff]")


# ---------------------------------------------------------------- text helpers

def clean(text: str) -> str:
    """Collapse spaces inside each line, drop empty lines. Non-breaking spaces become plain spaces."""
    text = INVISIBLE_RE.sub("", text)
    lines = (" ".join(ln.split()) for ln in text.split("\n"))
    return "\n".join(ln for ln in lines if ln)


def _name_parts(e) -> list[list[str]]:
    """Class names (and the id, except on headings, whose id is a slug of their text) split at - and _."""
    names = (e.get("class") or "").lower().split()
    if not (isinstance(e.tag, str) and e.tag.lower() in HEADING_TAGS):
        names.append((e.get("id") or "").lower())
    return [[p for p in re.split(r"[-_]+", n) if p] for n in names if n]


def has_mark(e, marks=DROP_MARKS) -> bool:
    """A mark matches whole parts of a class name: "hse-back-to-top__link" has "back-to-top", but the heading id
    "searching-for-opportunities" does not have "search" (S106: that heading and its chapter title were lost)."""
    parts = _name_parts(e)
    for m in marks:
        want = m.split("-")
        if any(name[k:k + len(want)] == want for name in parts for k in range(len(name) - len(want) + 1)):
            return True
    return False


def is_furniture(e) -> bool:
    if not isinstance(e.tag, str):
        return True  # comments and processing instructions
    tag = e.tag.lower()
    if tag in DROP_TAGS or e.get("hidden") is not None or e.get("aria-hidden") == "true":
        return True
    if (e.get("role") or "").lower() == "navigation":  # HSE "Next page" links of a multi-page guide
        return True
    return has_mark(e)


def inline_text(e, skip: set[str] | frozenset = frozenset()) -> str:
    """Text of an element. <br> gives a line break; raw newlines in the HTML are only spaces.
    Child elements whose tag is in skip are left out (their tail text is kept)."""
    out: list[str] = []

    def walk(el, top=False):
        if not top:
            if not isinstance(el.tag, str):
                out.append((el.tail or "").replace("\n", " "))
                return
            tag = el.tag.lower()
            if tag == "br":
                out.append("\n")
            elif tag in skip or is_furniture(el) or tag == "img":
                pass
            else:
                walk_inner(el)
                if tag in BLOCK_TAGS:
                    out.append("\n")
            out.append((el.tail or "").replace("\n", " "))
        else:
            walk_inner(el)

    def walk_inner(el):
        out.append((el.text or "").replace("\n", " "))
        for c in el:
            walk(c)

    walk(e, top=True)
    return clean("".join(out))


# ---------------------------------------------------------------- reading the page

def content_root(doc):
    """The element that holds the main content, and a note when we had to fall back."""
    for xp in ("//main", "//*[@role='main']", "//*[@id='contentContainer']", "//*[@id='content']"):
        found = doc.xpath(xp)
        if found:
            return found[0], None
    body = doc.find("body")
    if body is None:
        return doc, "no <body> found; used the whole document"
    return body, None


def read_html(data: bytes | str) -> dict:
    """The page as plain data: title, canonical URL and a flat list of blocks in reading order.

    Blocks: {"kind": "heading", "level", "text", "anchor"}, {"kind": "line", "text", "list": bool},
    {"kind": "table", "caption", "header", "rows"}, {"kind": "figure", "alt"}."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    issues: list[str] = []
    doc = lxml.html.document_fromstring(data)
    title_el = doc.find(".//title")
    head_title = clean(title_el.text_content()) if title_el is not None else ""
    canonical = None
    for link in doc.xpath("//link[@rel='canonical']"):
        canonical = link.get("href")
        break
    root, note = content_root(doc)
    if note:
        issues.append(note)
    if root.tag == "body" and doc.xpath("//header|//footer|//nav") and not doc.xpath("//*[contains(@class,'govspeak')]"):
        issues.append("no main content element found; used <body> without header, footer and navigation")
    blocks: list[dict] = []
    walk_block(root, blocks)
    return {"head_title": head_title, "canonical": canonical, "blocks": blocks, "issues": issues}


def walk_block(e, blocks: list[dict]) -> None:
    """Add the blocks of a container element. Loose inline text between blocks becomes a line."""
    buf: list[str] = []

    def flush():
        if buf:
            text = clean("".join(buf))
            if text:
                blocks.append({"kind": "line", "text": text, "list": False})
            buf.clear()

    buf.append((e.text or "").replace("\n", " "))
    for c in e:
        if not isinstance(c.tag, str):
            buf.append((c.tail or "").replace("\n", " "))
            continue
        tag = c.tag.lower()
        if is_furniture(c):
            pass
        elif tag in BLOCK_TAGS or tag == "dl":
            flush()
            block(c, blocks)
        elif tag == "br":
            buf.append("\n")
        else:  # inline element in a container (a, strong, span ...)
            for img in c.iter("img"):
                _figure(img, blocks)
            buf.append(inline_text(c) + " ")
        buf.append((c.tail or "").replace("\n", " "))
    flush()


def _figure(img, blocks: list[dict]) -> None:
    alt = clean(img.get("alt") or "")
    if len(alt) > MIN_ALT:
        blocks.append({"kind": "figure", "alt": alt})


def block(e, blocks: list[dict]) -> None:
    tag = e.tag.lower()
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        text = inline_text(e).replace("\n", " ")
        if text:
            blocks.append({"kind": "heading", "level": min(int(tag[1]), 4), "text": text, "anchor": e.get("id")})
    elif tag in LINE_TAGS:
        text = inline_text(e)
        if text:
            blocks.append({"kind": "line", "text": text, "list": False})
        for img in e.iter("img"):
            _figure(img, blocks)
    elif tag in ("ul", "ol"):
        list_items(e, blocks)
    elif tag == "li":  # a stray list item outside a list
        text = inline_text(e)
        if text:
            blocks.append({"kind": "line", "text": "• " + text, "list": True})
    elif tag == "table":
        blocks.append(read_table(e))
    elif tag == "img":
        _figure(e, blocks)
    elif tag == "hr":
        pass
    else:  # div, section, figure, blockquote ...
        walk_block(e, blocks)


def list_items(e, blocks: list[dict], depth: int = 0) -> None:
    """One line per list item: "• " or "1. ", indented by two spaces for each level of nesting.
    A <br> inside an item starts a new line without a mark."""
    ordered = e.tag.lower() == "ol"
    try:
        n = int(e.get("start") or 1)
    except ValueError:
        n = 1
    for li in e:
        stray = clean((li.tail or "").replace("\n", " "))  # text in the list but outside any item (broken HTML)
        if not isinstance(li.tag, str) or li.tag.lower() != "li" or is_furniture(li):
            if stray:
                _add_stray(blocks, stray, depth)
            continue
        text = inline_text(li, skip={"ul", "ol", "table"})
        mark = "  " * depth + (f"{n}. " if ordered else "• ")
        if text:
            blocks.append({"kind": "line", "text": mark + text, "list": True})
        n += 1
        for sub in li:
            if isinstance(sub.tag, str) and sub.tag.lower() in ("ul", "ol"):
                list_items(sub, blocks, depth + 1)
            elif isinstance(sub.tag, str) and sub.tag.lower() == "table":
                blocks.append(read_table(sub))
        for img in li.iter("img"):
            if next(img.iterancestors("li"), None) is li:  # images in nested lists are done there
                _figure(img, blocks)
        if stray:
            _add_stray(blocks, stray, depth)


def _add_stray(blocks: list[dict], text: str, depth: int) -> None:
    """Text inside a list but after an item's end tag (HSE wood dust: "<li>... time</li> period</ul>"): it ends
    that item, so it joins the last item's line; with no item before it, it is a line of its own."""
    if blocks and blocks[-1]["kind"] == "line" and blocks[-1]["list"]:
        blocks[-1]["text"] += " " + text
    else:
        blocks.append({"kind": "line", "text": "  " * depth + text, "list": True})


def read_table(t) -> dict:
    """Rows of cell text with colspan and rowspan expanded, and which rows are header rows."""
    caption_el = t.find("caption")
    caption = inline_text(caption_el).replace("\n", " ") if caption_el is not None else ""
    trs = []
    for child in t:
        if not isinstance(child.tag, str):
            continue
        tag = child.tag.lower()
        if tag == "tr":
            trs.append((child, False))
        elif tag in ("thead", "tbody", "tfoot"):
            for tr in child:
                if isinstance(tr.tag, str) and tr.tag.lower() == "tr":
                    trs.append((tr, tag == "thead"))
    grid: list[list[str]] = []
    header_flags: list[bool] = []
    pending: dict[int, tuple[str, int]] = {}  # column -> (text, rows still to fill) from rowspan
    for tr, in_head in trs:
        row: list[str] = []
        all_th = True
        cells = [c for c in tr if isinstance(c.tag, str) and c.tag.lower() in ("td", "th")]
        for c in cells:
            _fill_rowspans(row, pending)
            text = inline_text(c).replace("\n", " ")
            if c.tag.lower() != "th" and text:
                all_th = False
            down = _int(c.get("rowspan"))
            for _ in range(_int(c.get("colspan"))):
                if down > 1:
                    pending[len(row)] = (text, down - 1)
                row.append(text)
        _fill_rowspans(row, pending)
        # a cell from a row above that reaches past the cells of this row
        for k in sorted(k for k in pending if k > len(row)):
            row.extend([""] * (k - len(row)))
            _fill_rowspans(row, pending)
        grid.append(row)
        has_th = any(c.tag.lower() == "th" for c in cells)
        header_flags.append(in_head or (has_th and all_th))
    return {"kind": "table", "caption": caption, "rows": grid, "header": header_flags}


def _fill_rowspans(row: list[str], pending: dict[int, tuple[str, int]]) -> None:
    """Add the cells that rows above carry down (rowspan) at the end of this row."""
    while len(row) in pending:
        text, left = pending.pop(len(row))
        if left > 1:
            pending[len(row)] = (text, left - 1)
        row.append(text)


def _int(v) -> int:
    try:
        return max(1, min(int(v), 50))
    except (TypeError, ValueError):
        return 1


# ---------------------------------------------------------------- the tree

def group_headings(blocks: list[dict]) -> list[dict]:
    """A heading (h3 or lower) with nothing under it, followed straight away by a heading of the same level, is
    a group label ("Named standards" over FAQ 25 in the AD B FAQ, "Payment to third parties" over 6.4 in CIS 340).
    The page does not say where the group ends, so the label takes only the heading right after it (with that
    heading's own sub-headings), one level down, instead of the label being dropped as an empty heading (S106)."""
    out = [dict(b) for b in blocks]
    heads = [i for i, b in enumerate(out) if b["kind"] == "heading"]
    labels = {i for i in heads if out[i]["level"] >= 3 and i + 1 < len(out)
              and out[i + 1]["kind"] == "heading" and out[i + 1]["level"] == out[i]["level"]}
    active: int | None = None  # level of the open group
    first = False  # the heading right after the label
    for i in heads:
        lv = blocks[i]["level"]
        if active is not None and lv <= active and not first:
            active = None
        first = False
        if i in labels:
            active, first = lv, True
            continue
        if active is not None:
            out[i]["level"] = lv + 1
            if lv == active:
                out[i]["grouped"] = True  # keeps the id it had before (evals and fixes point to section ids)
    return out


class Builder:
    def __init__(self, page: dict, meta: dict):
        self.page = page
        self.meta = meta
        self.url = page.get("canonical") or meta.get("fetched_url") or meta.get("url") or ""
        self.sections: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self.issues: list[str] = list(page.get("issues", []))
        self.title = ""
        self.root = None           # pseudo-parent for text before the first heading
        self.stack: dict[int, dict] = {}  # level (2, 3, 4) -> latest heading or numbered paragraph
        self.chapter_number: str | None = None
        self.last_chapter_int = 0
        self.para: dict | None = None  # open numbered paragraph
        self.text: dict | None = None  # open text section
        self.counts: Counter = Counter()

    # -------------------------------------------------- helpers

    def add(self, sec: dict) -> dict:
        sid = sec["id"]
        if sid in self.by_id:
            k = 2
            while f"{sid}-{k}" in self.by_id:
                k += 1
            sec["id"] = f"{sid}-{k}"
        self.sections.append(sec)
        self.by_id[sec["id"]] = sec
        return sec

    def new(self, sid, kind, parent, number, title, path, text="", anchor=None, **extra) -> dict:
        return self.add({
            "id": sid, "parent_id": parent["id"] if parent else None, "type": kind, "number": number,
            "title": title, "heading_path": path, "text": text, "printed_page": None, "file_page": None,
            "applies_to": None, "footnotes": [], "url": self.url + (f"#{anchor}" if anchor else ""), **extra,
        })

    def parent_for(self, level: int) -> dict | None:
        """The latest heading above this level."""
        for lv in range(level - 1, 1, -1):
            if lv in self.stack:
                return self.stack[lv]
        return None

    def container(self) -> dict | None:
        """Where running text goes: the latest heading or numbered paragraph at any level."""
        for lv in sorted(self.stack, reverse=True):  # 2 to 4, or 5 under a group label
            return self.stack[lv]
        return None

    def path_of(self, parent: dict | None) -> list[str]:
        return list(parent["heading_path"]) if parent else [self.title]

    def close(self) -> None:
        self.para = None
        self.text = None

    def para_number(self, text: str, heading: bool) -> tuple[str, str] | None:
        """(number, rest) if the text starts with a section number that fits the current chapter.
        Outside a numbered chapter only headings count, so "2.5 metres ..." in a paragraph is not taken."""
        m = PARA_NUM_RE.match(text)
        if not m:
            return None
        num = m.group(1)
        major = num.split(".")[0]
        if self.chapter_number is not None and major != self.chapter_number:
            return None
        if self.chapter_number is None and not heading:
            return None
        if f"para-{num}" in self.by_id:
            return None
        return num, m.group(2)

    # -------------------------------------------------- blocks

    def build(self) -> dict:
        blocks = self.page["blocks"]
        h1 = next((b for b in blocks if b["kind"] == "heading" and b["level"] == 1), None)
        title = h1["text"] if h1 else TITLE_SUFFIX_RE.sub("", self.page.get("head_title") or "")
        if not h1:
            self.issues.append("no <h1>; page title taken from <title>" if title else "no <h1> and no <title>")
        self.title = title or self.meta.get("part_title") or self.meta.get("title") or self.meta.get("source_id", "")
        blocks = group_headings(blocks)
        seen_h1 = False
        for b in blocks:
            k = b["kind"]
            if k == "heading":
                if b["level"] == 1:
                    if not seen_h1:
                        seen_h1 = True
                        continue
                    self.issues.append(f"second <h1> \"{b['text'][:60]}\" treated as a chapter")
                    b = {**b, "level": 2}
                self.heading(b)
            elif k == "line":
                self.line(b)
            elif k == "table":
                self.table(b)
            elif k == "figure":
                self.figure(b)
        self.sections = [s for s in self.sections if self.keep(s)]
        prefix = self.meta.get("id_prefix")
        if prefix:  # one page of a multi-page source: ids like "top-text-1" must not clash across pages
            for s in self.sections:
                s["id"] = f"{prefix}-{s['id']}"
                if s["parent_id"]:
                    s["parent_id"] = f"{prefix}-{s['parent_id']}"
        if not any(s["type"] not in ("chapter", "heading") for s in self.sections):
            self.issues.append("empty page: no text found")
        return {
            "source_id": self.meta.get("source_id"), "version_id": self.meta.get("version_id"),
            "valid_from": self.meta.get("valid_from"), "valid_to": self.meta.get("valid_to"),
            "sha256": self.meta.get("sha256"), "title": self.title, "parser": PARSER,
            "sections": self.sections, "definitions": [], "issues": self.issues, "checks": [],
        }

    def keep(self, s: dict) -> bool:
        """Drop empty sections. Headings stay when they have something under them."""
        if s["type"] in ("chapter", "heading"):
            return bool(s["title"]) and any(x["parent_id"] == s["id"] for x in self.sections)
        if s["type"] == "table":
            return bool(s.get("grid"))
        if s["type"] == "paragraph":
            return bool(s["text"] or s["title"])
        return bool(s["text"])

    def heading(self, b: dict) -> None:
        self.close()
        level, text, anchor = b["level"], b["text"], b.get("anchor")
        if level == 2:
            number, sid = None, None
            m = CHAPTER_NUM_RE.match(text)
            a = APPENDIX_RE.match(text)
            if a:
                number = a.group(1).upper()
                sid = f"appendix-{number.lower()}"
            elif m and int(m.group(1)) == self.last_chapter_int + 1:
                number = m.group(1)
                self.last_chapter_int = int(number)
                sid = f"chapter-{number}"
            self.chapter_number = number
            sid = sid or slugify(text)
            sec = self.new(sid, "chapter", None, number, text, [self.title, text], anchor=anchor, level=2)
            self.stack = {2: sec}
            return
        parent = self.parent_for(level)
        pn = self.para_number(text, True)
        if pn:
            num, rest = pn
            sec = self.new(f"para-{num}", "paragraph", parent, num, rest, [*self.path_of(parent), text],
                           anchor=anchor)
            self.para = sec
        else:
            base = parent
            if b.get("grouped") and parent is not None:  # under a group label: the id it has without the label
                base = self.by_id.get(parent["parent_id"]) if parent["parent_id"] else None
            sid = f"{base['id']}-{slugify(text)}" if base else slugify(text)
            sec = self.new(sid, "heading", parent, None, text, [*self.path_of(parent), text], anchor=anchor,
                           level=level)
        self.stack = {lv: s for lv, s in self.stack.items() if lv < level}
        self.stack[level] = sec

    def line(self, b: dict) -> None:
        text = b["text"]
        cont = self.container()
        if not b["list"]:
            pn = self.para_number(text, False)
            if pn:
                num, rest = pn
                # A numbered paragraph sits beside other numbered paragraphs, under their heading.
                parent = cont
                while parent is not None and parent["type"] == "paragraph":
                    parent = self.by_id.get(parent["parent_id"]) if parent["parent_id"] else None
                self.text = None
                anchor = parent["url"].split("#", 1)[1] if parent and "#" in parent["url"] else None
                self.para = self.new(f"para-{num}", "paragraph", parent, num, None,
                                     [*self.path_of(parent), f"Paragraph {num}"], rest, anchor=anchor)
                return
        if self.para is not None:
            self.para["text"] = f"{self.para['text']}\n{text}" if self.para["text"] else text
            return
        if self.text is not None and len(self.text["text"]) + 1 + len(text) <= TEXT_LIMIT:
            self.text["text"] += "\n" + text
            return
        base = cont["id"] if cont else "top"
        self.counts[base] += 1
        anchor = cont["url"].split("#", 1)[1] if cont and "#" in cont["url"] else None
        self.text = self.new(f"{base}-text-{self.counts[base]}", "text", cont, None, None, self.path_of(cont),
                             text, anchor=anchor)

    def table(self, b: dict) -> None:
        self.text = None
        rows, header = b["rows"], b["header"]
        if not any(any(c for c in r) for r in rows):
            self.issues.append("empty table skipped")
            return
        if len({len(r) for r in rows}) > 1:
            self.issues.append("table rows of different lengths were padded")
        ncols = max(len(r) for r in rows)
        rows = [r + [""] * (ncols - len(r)) for r in rows]
        heads = [i for i, h in enumerate(header) if h]
        # Header rows at the top give the column names; header rows further down stay in the grid.
        top = []
        for i in range(len(rows)):
            if i in heads:
                top.append(i)
            else:
                break
        if top and len(top) < len(rows):
            columns = []
            for c in range(ncols):
                parts: list[str] = []
                for i in top:
                    if rows[i][c] and rows[i][c] not in parts:
                        parts.append(rows[i][c])
                columns.append(" - ".join(parts))
            grid = [r for i, r in enumerate(rows) if i not in top]
        else:
            columns, grid = [], rows
        cont = self.container()
        caption = b.get("caption") or ""
        m = re.match(r"^Table\s+([A-Z]?\d+(?:\.\d+)?)[.:]?\s*(.*)$", caption)
        if m:
            number, title = m.group(1), m.group(2) or caption
            sid = f"table-{number.lower()}"
        else:
            number, title = None, caption or (cont["title"] if cont and cont.get("title") else self.title)
            base = cont["id"] if cont else "top"
            self.counts[f"{base}#table"] += 1
            sid = f"{base}-table-{self.counts[base + '#table']}"
        body = [columns] + grid if columns else grid
        text = "\n".join(" | ".join(r) for r in body)
        anchor = cont["url"].split("#", 1)[1] if cont and "#" in cont["url"] else None
        label = f"Table {number}: {title}" if number else f"Table: {title}"
        self.new(sid, "table", cont, number, title, [*self.path_of(cont), label], text, anchor=anchor,
                 columns=columns, grid=grid, heading_rows=[], grid_source="html")

    def figure(self, b: dict) -> None:
        self.text = None
        cont = self.container()
        self.counts["#figure"] += 1
        n = self.counts["#figure"]
        base = cont["id"] if cont else "top"
        anchor = cont["url"].split("#", 1)[1] if cont and "#" in cont["url"] else None
        # Images on web pages have no printed number: we count them in page order, labelled "Image n".
        self.new(f"{base}-image-{n}", "figure", cont, str(n), b["alt"], [*self.path_of(cont), f"Image {n}"],
                 b["alt"], anchor=anchor, kind_label="image", labels=[])


def build_tree(page: dict, meta: dict) -> dict:
    """The document tree from read_html's data and the version record (plus source title)."""
    return Builder(page, meta).build()


def parse_html(data: bytes | str, meta: dict) -> dict:
    return build_tree(read_html(data), meta)


# ---------------------------------------------------------------- command line

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    a = ap.parse_args(argv)
    import yaml

    doc = yaml.safe_load((CORPUS_DIR / "sources.yaml").read_text(encoding="utf-8"))
    src = next((s for s in doc["sources"] if s["id"] == a.source), None)
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((CORPUS_DIR / "versions" / a.source).glob("*.json"))]
    root = CORPUS_DIR.parent
    todo = [r for r in recs if r.get("valid_to") is None and r.get("media_type", "").split(";")[0] in
            ("text/html", "application/xhtml+xml")]
    if not todo:
        print(f"{a.source}: no current HTML versions")
    for r in todo:
        raw = root / r["raw_path"]
        if not raw.exists():
            print(f"missing raw file: {r['raw_path']}")
            continue
        meta = {**r, "title": src["title"] if src else a.source, "url": src.get("url") if src else None}
        if len(todo) > 1:  # several pages: each page's ids carry the page, so keys stay unique in the source
            meta["id_prefix"] = slugify(r["version_id"].split("@")[0])
        tree = parse_html(raw.read_bytes(), meta)
        out = CORPUS_DIR / "parsed" / a.source / f"{r['version_id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(tree, ensure_ascii=False, indent=1), encoding="utf-8")
        types = Counter(s["type"] for s in tree["sections"])
        print(f"{r['version_id']}: {dict(types)}, {len(tree['issues'])} issues -> {out.relative_to(root)}")
        for i in tree["issues"]:
            print(f"  issue: {i}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
