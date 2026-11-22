"""Corpus coverage, two tools in one module.

1. The audit (corpus/OVERNIGHT-PLAN.md, S1): which sources are parsed, checked and chunked.

    python -m system.rag.coverage                 # writes corpus/coverage.md and prints the summary

   One row per source in scope (mode ingest, fetched). For each: current versions and their file types, raw file
   present, the parser assigned in sources.yaml (or the one that fits the file type), parsed trees, open model
   checks, chunk files.

2. The content check: does each parsed tree hold what its raw file holds? Plain code, no model (ADR 0006).

    python -m system.rag.coverage report [--source ID ...] [--verbose]
    python -m system.rag.coverage accept --source ID --item KEY --reason "..." --by "..."

   Three checks per version in scope (corpus.in_scope, ADR 0016) whose tree is in corpus/parsed. For a PDF:
   - text: the raw words (pdfplumber extract_words, read here, not through the parser's reader) against every
     text-bearing field of the tree, as a multiset of normalised words, per document and per page. Words the
     parsers drop by rule (running headers and footers, page numbers, cover, contents, index, sideways text,
     pages a tree issue names) are counted under that reason; the rest missing is "unexplained".
   - images: every embedded image of 1% of the page or more sits in a figure crop, or has a named reason (logo,
     signature, band, background, cover, a tree issue).
   - tables: every ruled table pdfplumber finds (2+ rows, 2+ columns) has a table or figure section on its page
     and most of its cell words in the tree.
   Flagged items not yet accepted make the report fail (exit 1) and the real-tree test fail. A person who looked
   at a flagged item and keeps it records why with `accept` (corpus/coverage/<source>.json, in git).
   Raw words, images and tables are cached per raw file under corpus/parsed/<source>/coverage-cache/ (not in git).

   Web pages (read_html_raw) and legislation XML (read_xml_raw) are read as blocks of visible text: a page's block
   elements, a law's provisions. Page chrome (header, footer, menus, breadcrumbs, cookie banner, feedback, back to
   top, screen-reader text, "last updated") and the law's editorial parts (annotations, metadata, title page,
   explanatory note, signature, footnotes) are counted under named reasons (HTML_REASONS, XML_REASONS). check_blocks
   then flags a block with 3 or more words in no 3-word run of the tree, a document with over 1% of its words
   missing, a table whose cells are not in a table section (web pages) or the tree (laws), and a picture in no
   figure section and with no named reason.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
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


def audit() -> int:
    print(write(build()))
    return 0


# =============================================================== content check: raw file against parsed tree

CACHE_VERSION = 2  # 2: ruled tables read from the deduplicated page too
PDF = "application/pdf"

# Thresholds, chosen from the first run over every PDF tree (22 Nov 2026; distribution in the report's --verbose
# output and in architecture/design/regulations-corpus.md).
MIN_IMAGE_SHARE = 0.01     # images under 1% of the page area are ignored (bullets, icons, specks)
PAGE_MIN_WORDS = 40        # a page is judged only with this many raw words left after the reasons
PAGE_EMPTY = 0.10          # ... and flagged when the tree holds under 10% of them: the page was lost
DOC_UNEXPLAINED = 0.05     # a document is flagged when over 5% of its raw words are missing for no named reason
TABLE_WORDS = 0.60         # a ruled table is found when 60% of its cell words are in the tree on that page
IMAGE_IN_CROP = 0.50       # an image is inside a figure crop when half of it lies in the crop
PAGE_FRAME = 0.85          # a "ruled table" this wide and this tall is a border round the page (Procurement guides)

REASONS = {  # raw words the parsers drop on purpose, and why (first match wins, in this order)
    "sideways": "sideways or upside-down text (the reader skips it)",
    "issue": "on a page a tree issue says was skipped (picture of text, blacked out), or the lines an issue quotes",
    "cover": "cover page (before the first section, and short or the imprint)",
    "contents": "contents page or contents line",
    "front": "front matter before the first section: a short page or the imprint (ISBN, ©, Published by)",
    "index": "index, or the list after it (parse_adoc, parse_guide and parse_flats stop there)",
    "back": "back cover (last page)",
    "page-number": "page number in the header or footer",
    "watermark": "watermark ('O N L I N E  V E R S I O N')",
    "furniture": "running header or footer (repeats on many pages, or the Approved Document top band)",
    "bullet": "a bullet glyph read as a letter ('n', 'l', 'q', 'u' from a dingbat font at a line start)",
    "margin-label": "a margin label ('ACOP 3', 'Guidance 11'): parse_pdf keeps it as the section's status",
    "form": "a form's answer boxes ('Yes', 'No', 'N/A'): parse_booklet drops them",
    "duplicate": "printed twice a few points apart (shadow or overprint), as a line or a word",
    "in-figure": "inside a figure crop: kept as the picture, not as text",
}
IMAGE_REASONS = {
    "cover": "on the cover or front matter",
    "back": "on the back cover or index pages",
    "background": "background behind a page of text (60% of the page or more)",
    "band": "a thin decorative band or rule",
    "repeated": "the same image on 3 or more pages (logo, band, tab)",
    "signature": "a signature, letterhead logo, publisher's logo or cover thumbnail (parse_pdf's rule)",
    "issue": "named in a tree issue (no caption below it)",
    "table": "inside a table's rows",
}
CID_RE = re.compile(r"\(cid:\d+\)")
APOS_RE = re.compile(r"['‘’`´]")
TOKEN_RE = re.compile(r"[^\W_]+")
LIGATURES = ("ffi", "ffl", "fi", "fl", "ff")
AD_PARSER = "approved-document-pdf"
STOPS_AT_INDEX = ("approved-document-pdf", "fire-risk-guide-pdf", "flats-guide-pdf")  # parse_pdf keeps an index
INSERTED = {"figure", "table", "note", "box", "aside", "requirement"}  # placed inside running text
TABLE_HOMES = ("table", "figure", "requirement")  # parse_adoc keeps the ruled Requirement boxes as requirement


def tokens(text: str | None) -> list[str]:
    """Normalised words: NFKC (ligatures, superscripts, m² -> m2), lower case, apostrophes removed, then runs of
    letters and digits. Punctuation, bullets, dot leaders and hyphens split words, the same on both sides, so a
    word hyphenated at a line end ("pre-" + "vention") matches the parser's joined "pre-vention"."""
    if not text:
        return []
    text = unicodedata.normalize("NFKC", CID_RE.sub(" ", text)).lower()
    return TOKEN_RE.findall(APOS_RE.sub("", text))


# ---------------------------------------------------------------- raw readers (one per file type)

def read_pdf_raw(path: Path) -> dict:
    """The raw PDF as plain data, read with pdfplumber directly (not parse_pdf.read_pdf, so a reader bug shows):
    words with positions and upright flag, images, ruled tables. Exact overprints are removed (dedupe_chars)."""
    import pdfplumber

    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for n, page in enumerate(pdf.pages, start=1):
            w, h = float(page.width), float(page.height)
            clean = page.dedupe_chars()
            words = [[x["text"], round(x["x0"], 1), round(x["top"], 1), round(x["x1"], 1), round(x["bottom"], 1),
                      1 if x.get("upright", True) and x.get("direction", "ltr") == "ltr" else 0]
                     for x in clean.extract_words()]
            images = [[round(i["x0"], 1), round(i["top"], 1), round(i["x1"], 1), round(i["bottom"], 1)]
                      for i in page.images]
            tables = []
            try:
                found = clean.find_tables()
            except Exception:  # a broken table structure must not stop the check
                found = []
            for t in found:
                rows = [[" ".join((c or "").split()) for c in r] for r in t.extract()]
                rows = [r for r in rows if any(r)]
                cols = {k for r in rows for k, c in enumerate(r) if c}
                if len(rows) >= 2 and len(cols) >= 2:
                    tables.append({"bbox": [round(v, 1) for v in t.bbox], "rows": rows})
            pages.append({"n": n, "width": round(w, 1), "height": round(h, 1), "words": words, "images": images,
                          "tables": tables})
    return {"pages": pages}


# ---------------------------------------------------------------- web pages and legislation XML (S106)
# Both are read as blocks of visible text in reading order: a web page's block elements (p, li, td, h2 ...), a
# legislation file's provisions (the nearest element with an id). Each piece of text carries the reason it is not
# content (site header, footer, menus, editorial notes ...) or None. The check is the same for both
# (check_blocks): every block of content must be in the tree as a run of words, every table's cells must be in
# the tree, and every picture must be a figure section or have a named reason.

HTML = "text/html"
XML = "application/xml"
HTML_INLINE = {"a", "abbr", "acronym", "b", "bdi", "bdo", "big", "br", "cite", "code", "data", "del", "dfn", "em",
               "font", "i", "img", "ins", "kbd", "mark", "q", "s", "samp", "small", "span", "strong", "sub", "sup",
               "time", "tt", "u", "var", "wbr"}
HTML_REASONS = {  # web page text the parser drops on purpose, and why (the nearest named element wins)
    "not-shown": "not shown on the page (script, style, template, a hidden element)",
    "screen-reader": "text for screen readers only ('visually-hidden')",
    "site-header": "the site header (logo, search, menu)",
    "site-footer": "the site footer",
    "navigation": "menus, breadcrumbs and 'next page' links",
    "skip-link": "'skip to main content' link",
    "cookie-banner": "cookie banner",
    "feedback": "page feedback ('Is this page useful?', report a problem)",
    "back-to-top": "'back to top' link",
    "sidebar": "sidebar (related links beside the content)",
    "related": "related content links",
    "form": "form controls and buttons",
    "contents-list": "the page's own contents list (links to its headings)",
    "last-updated": "'last updated' or 'published' line (page metadata)",
    "share-print": "share and print links",
    "search": "search box",
    "embedded": "embedded frame, video or drawing (iframe, svg)",
}
# (reason, tags, ARIA roles, class or id marks). A mark matches whole parts of a class name split at - and _
# ("hse-back-to-top__link" has back-to-top; "research" does not have search).
HTML_RULES = (
    ("screen-reader", set(), set(), ("visually-hidden", "sr-only")),
    ("not-shown", {"script", "style", "noscript", "template", "head", "title", "meta", "link"}, set(),
     ("hide", "hidden", "js-hidden")),
    ("site-header", {"header"}, {"banner"}, ()),
    ("site-footer", {"footer"}, {"contentinfo"}, ()),
    ("navigation", {"nav"}, {"navigation"}, ("breadcrumb", "multistep-navigation", "pagination", "next-page")),
    ("skip-link", set(), set(), ("skip", "skip-link")),
    ("cookie-banner", set(), set(), ("cookie", "cookie-banner")),
    ("feedback", set(), set(), ("feedback", "report-a-problem")),
    ("back-to-top", set(), set(), ("back-to-top",)),
    ("sidebar", {"aside"}, {"complementary"}, ("sidebar",)),
    ("related", set(), set(), ("related",)),
    ("form", {"form", "button", "input", "select", "option", "textarea", "label", "dialog"}, {"search"}, ()),
    ("contents-list", set(), set(), ("contents-list",)),
    ("last-updated", set(), set(), ("lastupdated", "last-updated", "metadata")),
    ("share-print", set(), set(), ("share", "print-link", "printable-version")),
    ("search", set(), set(), ("search",)),
    ("embedded", {"svg", "iframe", "object", "embed", "video", "audio", "canvas"}, set(), ()),
)
HIDDEN_STYLE_RE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)


def _mark_parts(e) -> list[list[str]]:
    names = (e.get("class") or "").lower().split() + [(e.get("id") or "").lower()]
    return [[p for p in re.split(r"[-_]+", n) if p] for n in names if n]


def _has_mark(parts: list[list[str]], mark: str) -> bool:
    want = mark.split("-")
    return any(name[k:k + len(want)] == want for name in parts for k in range(len(name) - len(want) + 1))


def html_reason(e) -> str | None:
    """Why this element (with everything inside it) is not page content, or None."""
    tag = e.tag.lower() if isinstance(e.tag, str) else ""
    if e.get("hidden") is not None or e.get("aria-hidden") == "true" or HIDDEN_STYLE_RE.search(e.get("style") or ""):
        return "not-shown"
    role = (e.get("role") or "").lower()
    parts = _mark_parts(e)
    for reason, tags, roles, marks in HTML_RULES:
        if tag in tags or role in roles or any(_has_mark(parts, m) for m in marks):
            return reason
    return None


def _cell_text(e) -> str:
    return " ".join(" ".join(t for t in e.itertext()).split())


def read_html_raw(path: Path) -> dict:
    """A web page as blocks of visible text in reading order, each part with its reason (None: content), plus
    its images and tables. Read with lxml directly, not through parse_html, so a parser rule that drops too much
    shows. Text after a block element inside another block goes into a new block (a list after a paragraph's
    opening words is not one run of words)."""
    import lxml.html

    doc = lxml.html.document_fromstring(path.read_bytes())
    body = doc.find("body")
    if body is None:
        body = doc
    blocks: list[dict] = []
    images: list[dict] = []
    tables: list[dict] = []

    def new(tag: str) -> int:
        blocks.append({"tag": tag, "parts": []})
        return len(blocks) - 1

    def add(b: int, text: str | None, reason: str | None) -> None:
        parts = blocks[b]["parts"]
        if not text or not text.strip():
            if text and parts:
                parts[-1][0] += " "  # a space between two inline elements ("<abbr>HMRC</abbr> <abbr>CIS</abbr>")
            return
        if parts and parts[-1][1] == reason:
            parts[-1][0] += text
        else:
            parts.append([text, reason])

    def walk(e, reason: str | None, b: int) -> int:
        tag = e.tag.lower()
        r = reason or html_reason(e)
        if tag == "img":
            images.append({"alt": " ".join((e.get("alt") or "").split()), "src": e.get("src") or "",
                           "width": e.get("width"), "height": e.get("height"), "reason": r, "block": b})
        elif tag == "table":
            rows = [[_cell_text(c) for c in tr if isinstance(c.tag, str) and c.tag.lower() in ("td", "th")]
                    for tr in e.iter("tr")]
            tables.append({"rows": [x for x in rows if any(x)], "reason": r})
        if tag == "br" and blocks[b]["parts"]:
            blocks[b]["parts"][-1][0] += "\n"  # a line break parts words ("England<br>HM Revenue")
        inline = tag in HTML_INLINE
        cur = b if inline else new(tag)
        add(cur, e.text, r)
        for c in e:
            if isinstance(c.tag, str):
                cur = walk(c, r, cur)
            add(cur, c.tail, r)
        return cur if inline else new(blocks[b]["tag"])

    walk(body, None, new("body"))
    keep = [i for i, bl in enumerate(blocks) if bl["parts"]]
    renum = {old: new_ for new_, old in enumerate(keep)}
    for im in images:
        im["block"] = renum.get(im["block"])
    return {"kind": "html", "blocks": [blocks[i] for i in keep], "images": images, "tables": tables}


LEG_NS = "http://www.legislation.gov.uk/namespaces/legislation"
XML_REASONS = {  # legislation XML text parse_legislation leaves out on purpose, and why
    "metadata": "legislation.gov.uk metadata (dates, effects, statistics), not printed text",
    "contents": "table of contents",
    "annotation": "editorial annotations (amendment and commencement notes): kept on sections as amendments",
    "prelims": "the title page and preamble (title, made, laid and in force dates, enacting words)",
    "explanatory-note": "the explanatory note ('This note is not part of the Regulations') and earlier orders",
    "signature": "the signature block (who signed and when)",
    "footnote": "the printed footnotes: citations of the enabling and amended laws",
    "resources": "attached files and images listed at the end of the file",
    "equation-image": "a picture of a formula whose text is in the provision (parse_legislation skips it)",
    "schedules-title": "the word 'SCHEDULES' over the Schedules (each Schedule has its own number and title)",
}
XML_RULES = {"Metadata": "metadata", "Contents": "contents", "Commentaries": "annotation", "Commentary": "annotation",
             "PrimaryPrelims": "prelims", "SecondaryPrelims": "prelims", "ExplanatoryNotes": "explanatory-note",
             "EarlierOrders": "explanatory-note", "SignedSection": "signature", "Footnotes": "footnote",
             "Footnote": "footnote", "Resources": "resources"}


XML_INLINE = {"Superior", "Inferior", "Emphasis", "Strong", "Underline", "SmallCaps", "Uppercase", "Addition",
              "Substitution", "Repeal", "Citation", "CitationSubRef", "InternalLink", "ExternalLink", "Term",
              "Definition", "Acronym", "Abbreviation", "Span", "Character", "InlineAmendment", "CommentaryRef",
              "FootnoteRef", "Proviso", "Strike"}
XML_LABELS = {"Number", "Title"}  # each its own block (and a P1's Pnumber): the tree keeps them in their own fields


def xml_reason(e) -> str | None:
    q = etree_qname(e)
    if q is None:
        return None
    ns, name = q
    if ns != LEG_NS:
        return "metadata" if "metadata" in ns or ns.startswith("http://purl.org/dc") or "Atom" in ns else None
    if name == "Version" and "equation" in (e.get("Description") or "").lower():
        return "equation-image"
    if name == "Title" and etree_qname(e.getparent()) == (LEG_NS, "Schedules"):
        return "schedules-title"
    return XML_RULES.get(name)


def etree_qname(e) -> tuple[str, str] | None:
    if not isinstance(e.tag, str) or not e.tag.startswith("{"):
        return None
    ns, name = e.tag[1:].split("}", 1)
    return ns, name


def read_xml_raw(path: Path) -> dict:
    """A legislation.gov.uk XML file as blocks of text, one per provision (the nearest element with an id, else
    the nearest Part, Schedule or the body), each part with its reason (None: content); plus its pictures
    (Figure, Image) and tables (Tabular). Read with lxml directly, not through parse_legislation."""
    from lxml import etree

    root = etree.parse(str(path), etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)).getroot()
    blocks: list[dict] = []
    images: list[dict] = []
    tables: list[dict] = []
    skip_marks = {f"{{{LEG_NS}}}CommentaryRef", f"{{{LEG_NS}}}FootnoteRef"}  # markers: no printed text

    def new(name: str) -> int:
        blocks.append({"tag": name, "parts": []})
        return len(blocks) - 1

    def add(b: int, text: str | None, reason: str | None) -> None:
        parts = blocks[b]["parts"]
        if not text or not text.strip():
            if text and parts:
                parts[-1][0] += " "  # spaces between two amendments ("care homes</Addition> <Addition>, which")
            return
        if parts and parts[-1][1] == reason:
            parts[-1][0] += text
        else:
            parts.append([text, reason])

    def gap(b: int) -> None:  # a word break between two block elements (two Text elements, a number and its text)
        if blocks[b]["parts"]:
            blocks[b]["parts"][-1][0] += " "

    def walk(e, reason: str | None, b: int) -> int:
        q = etree_qname(e)
        name = q[1] if q else ""
        r = reason or xml_reason(e)
        p1_number = name == "Pnumber" and etree_qname(e.getparent()) == (LEG_NS, "P1")
        if (name in XML_LABELS or p1_number) and q[0] == LEG_NS:  # the tree keeps it in its own field
            lb = new(f"{blocks[b]['tag']}:{name.lower()}")
            add(lb, "".join(e.itertext()), r)
            return b
        if name not in XML_INLINE:
            gap(b)
        if name == "Figure" and q[0] == LEG_NS:
            images.append({"alt": "", "src": " ".join(i.get("ResourceRef") or "" for i in e.iter(f"{{{LEG_NS}}}Image")),
                           "reason": r, "block": b, "unit": e.get("id") or blocks[b]["tag"]})
        elif name == "Tabular" and q[0] == LEG_NS:
            rows = [[" ".join(" ".join(c.itertext()).split()) for c in tr if isinstance(c.tag, str)
                     and c.tag.endswith(("}td", "}th"))] for tr in e.iter("{http://www.w3.org/1999/xhtml}tr")]
            tables.append({"rows": [x for x in rows if any(x)], "reason": r, "unit": e.get("id") or blocks[b]["tag"]})
        own = e.get("id") and q and q[0] == LEG_NS
        cur = new(e.get("id")) if own else b
        add(cur, e.text, r)
        for c in e:
            if isinstance(c.tag, str) and c.tag not in skip_marks:
                cur = walk(c, r, cur)
            add(cur, c.tail, r)
        if name not in XML_INLINE:
            gap(cur)
        return new(blocks[b]["tag"]) if own else cur

    walk(root, None, new("body"))
    keep = [i for i, bl in enumerate(blocks) if bl["parts"]]
    renum = {old: new_ for new_, old in enumerate(keep)}
    for im in images:
        im["block"] = renum.get(im["block"])
    return {"kind": "xml", "blocks": [blocks[i] for i in keep], "images": images, "tables": tables}


BLOCK_MISSING = 3          # a block is flagged when 3 or more of its words are in no run of words in the tree
HTML_DOC_UNEXPLAINED = 0.01  # ... and a document when over 1% of its content words are missing


def check_blocks(raw: dict, tree: dict, sha8: str) -> dict:
    """Web page or legislation file against its tree. Text: every content word as a multiset (coverage), and every
    block as runs of three words found in the tree's word sequence (a short block: all its words in a row), so a
    lost paragraph shows even when its words occur elsewhere. Tables: each table's cell words in one table section
    (web pages) or in the tree (legislation, whose tables are rows of the provision's text). Images: a figure
    section with the image's alt text, or a named reason."""
    whole, _, seq, pdf_t, model_t = tree_pools(tree)
    grams = {n: {tuple(seq[k:k + n]) for k in range(len(seq) - n + 1)} for n in (1, 2, 3)}
    explained, items, examples = Counter(), [], []
    content_toks: list[str] = []
    raw_set: set[str] = set()
    seen_keys: Counter = Counter()
    for bl in raw["blocks"]:
        toks: list[str] = []
        for text, reason in bl["parts"]:
            ts = tokens(text)
            raw_set.update(ts)
            if reason:
                explained[reason] += len(ts)
            else:
                toks.extend(ts)
        if not toks:
            continue
        content_toks.extend(toks)
        n = len(toks)
        if n < 3:
            ok = [tuple(toks) in grams[n]] * n
        else:
            ok = [False] * n
            for k in range(n - 2):
                if tuple(toks[k:k + 3]) in grams[3]:
                    ok[k] = ok[k + 1] = ok[k + 2] = True
        miss = [t for t, g in zip(toks, ok) if not g]
        if len(miss) >= BLOCK_MISSING or (n < BLOCK_MISSING and miss):
            base = f"{sha8}:{bl['tag'] if raw.get('kind') == 'xml' else 'text'}:{'-'.join(toks[:6])}"
            seen_keys[base] += 1
            key = base if seen_keys[base] == 1 else f"{base}#{seen_keys[base]}"
            items.append({"key": key, "kind": "block", "page": None,
                          "detail": f"{len(miss)} of {n} words in no run of words in the tree: \"{_snippet(miss, 14)}\""
                                    f" in \"{_snippet(toks, 14)}\""})
    pool = Counter(whole)
    got = match(content_toks, pool, seq)
    n_content = len(content_toks)
    matched = sum(got)
    share = (n_content - matched) / n_content if n_content else 0.0
    if share > HTML_DOC_UNEXPLAINED:
        lost = [t for t, g in zip(content_toks, got) if not g]
        examples.append(_snippet(lost, 14))
        items.append({"key": f"{sha8}:doc:text", "kind": "doc", "page": None,
                      "detail": f"{share:.0%} of {n_content} words missing: \"{_snippet(lost, 14)}\""})

    def novel(c: Counter) -> Counter:
        return Counter({t: k for t, k in c.items() if t not in raw_set})

    extra_pdf, extra_model = novel(pdf_t), novel(model_t)
    text = {"raw_words": n_content + sum(explained.values()), "content_words": n_content, "matched": matched,
            "unexplained": n_content - matched, "unexplained_share": share, "explained": dict(explained),
            "coverage": matched / n_content if n_content else 1.0, "pages": [], "items": items, "examples": examples,
            "facts": {}, "extra_pdf": sum(extra_pdf.values()), "extra_pdf_words": [t for t, _ in extra_pdf.most_common(8)],
            "extra_model": sum(extra_model.values()), "extra_model_words": [t for t, _ in extra_model.most_common(8)],
            "tree_words": sum(whole.values())}
    return {"text": text, "images": _check_block_images(raw, tree, sha8), "tables": _check_block_tables(raw, tree, sha8, whole, seq)}


def _check_block_images(raw: dict, tree: dict, sha8: str) -> dict:
    figs = [Counter(t for t, _ in section_words(s)) for s in tree.get("sections") or [] if s.get("type") == "figure"]
    issues = " ".join(str(i) for i in tree.get("issues") or [])
    total, in_tree, explained, items, seen = 0, 0, Counter(), [], Counter()
    for k, im in enumerate(raw["images"]):
        total += 1
        if im.get("reason"):
            explained[im["reason"]] += 1
            continue
        alt = tokens(im.get("alt"))
        if alt and any(not (Counter(alt) - f) for f in figs):
            in_tree += 1
            continue
        if raw.get("kind") == "xml" and im.get("unit") and f"Figure inside {im['unit']}" in issues:
            explained["named in a tree issue (picture not parsed)"] += 1
            continue
        name = (im.get("src") or "").rsplit("/", 1)[-1].split("?")[0][-80:] or f"{k}"
        seen[name] += 1
        key = f"{sha8}:image:{name}" + (f"#{seen[name]}" if seen[name] > 1 else "")
        items.append({"key": key, "kind": "image", "page": None,
                      "detail": f"image {name!r} alt \"{im.get('alt', '')[:80]}\" in no figure section"
                                + (f" (in {im['unit']})" if im.get("unit") else "")})
    return {"images": total, "in_crop": in_tree, "explained": dict(explained), "items": items}


def _check_block_tables(raw: dict, tree: dict, sha8: str, whole: Counter, seq: list[str]) -> dict:
    homes = [Counter(t for t, _ in section_words(s)) for s in tree.get("sections") or [] if s.get("type") == "table"]
    total, found, explained, items = 0, 0, Counter(), []
    for k, t in enumerate(raw["tables"]):
        total += 1
        if t.get("reason"):
            explained[t["reason"]] += 1
            continue
        cell = [w for r in t["rows"] for c in r for w in tokens(c)]
        if not cell:
            explained["empty table"] += 1
            continue
        pools = [whole] if raw.get("kind") == "xml" else homes
        share = max((sum(match(cell, Counter(p), seq)) / len(cell) for p in pools), default=0.0)
        if share >= 0.9:
            found += 1
            continue
        first = " | ".join(c for c in (t["rows"] or [[]])[0] if c)[:70]
        where = "in the tree" if raw.get("kind") == "xml" else "in any one table section"
        items.append({"key": f"{sha8}:table:{t.get('unit') or k}:{'-'.join(cell[:4])}", "kind": "table", "page": None,
                      "table": "missing", "detail": f"{len(t['rows'])}-row table: {share:.0%} of its cell words {where}; "
                                                    f"first row \"{first}\""})
    return {"tables": total, "found": found, "explained": dict(explained), "items": items}


READERS = {PDF: read_pdf_raw, HTML: read_html_raw, XML: read_xml_raw}
CACHE_VERSIONS = {PDF: CACHE_VERSION, HTML: 3, XML: 4}  # bump one when its reader changes


def cache_path(source_id: str, sha256: str, media_type: str = PDF) -> Path:
    v = CACHE_VERSIONS.get(media_type, CACHE_VERSION)
    kind = "" if media_type == PDF else {HTML: "html.", XML: "xml."}.get(media_type, "")
    return CORPUS_DIR / "parsed" / source_id / "coverage-cache" / f"{sha256[:16]}.{kind}v{v}.json"


def raw_doc(record: dict, use_cache: bool = True) -> dict:
    """The raw file's words, images and tables, from the cache when it holds this file (by SHA-256)."""
    cp = cache_path(record["source_id"], record["sha256"], record["media_type"])
    version = CACHE_VERSIONS.get(record["media_type"], CACHE_VERSION)
    if use_cache and cp.exists():
        try:
            d = json.loads(cp.read_text(encoding="utf-8"))
            if d.get("cache_version") == version and d.get("sha256") == record["sha256"]:
                return d
        except (json.JSONDecodeError, OSError):
            pass
    d = READERS[record["media_type"]](ROOT / record["raw_path"])
    d.update(cache_version=version, sha256=record["sha256"])
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return d


def _fill_cache(record: dict) -> str:
    raw_doc(record)
    return record["source_id"]


# ---------------------------------------------------------------- the tree's words and pages

def section_words(s: dict) -> list[tuple[str, str]]:
    """(token, origin) for every text-bearing field of a section. origin: "pdf" (text read from the file) or
    "model" (table grids and column names a model wrote). Not heading_path (it repeats the parents) and not model
    descriptions. A figure or table's own printed prefix ("Figure 1", "Appendix 2") is taken from the end of its
    heading path when the title follows it."""
    out = []

    def add(text, origin="pdf"):
        out.extend((t, origin) for t in tokens(text))

    title = s.get("title") or ""
    hp = s.get("heading_path") or []
    if hp and title and hp[-1].endswith(title) and hp[-1] != title:
        prefix = hp[-1][: -len(title)]
        if len(tokens(prefix)) <= 3:
            add(prefix)
    elif hp and not title and s.get("type") in ("figure", "table", "schedule", "part", "chapter") \
            and len(tokens(hp[-1])) <= 3:  # "Schedule 6" with no title (a repealed Schedule)
        add(hp[-1])
    add(title)
    if s.get("number") and not (hp and title and tokens(s["number"])[:1] and hp[-1].endswith(title)
                                and set(tokens(s["number"])) <= set(tokens(hp[-1][: -len(title)]))):
        add(str(s["number"]))
    add(s.get("text"))
    add(s.get("limits"))  # a Schedule 1 requirement's limits on application (parse_legislation)
    for f in s.get("footnotes") or []:
        add(f.get("text") if isinstance(f, dict) else f)
    for x in s.get("labels") or []:
        add(x)
    # A table's grid and column names hold the same words as its text (the printed rows): count each word once,
    # as often as the text or the grid has it, whichever is more (a union, not a sum).
    grid_origin = "model" if s.get("grid_source") == "model" else "pdf"
    grid = Counter(t for row in s.get("grid") or [] for c in row or [] for t in tokens(c if isinstance(c, str) else str(c or "")))
    cols = Counter(t for c in s.get("columns") or [] for t in tokens(c if isinstance(c, str) else str(c or "")))
    cells = list((grid | cols).elements())
    if cells:
        have = Counter(t for t, _ in out)
        extra = Counter(cells) - have
        for t, n in extra.items():
            out.extend([(t, grid_origin)] * n)
        out.extend((t, "model-copy") for t in cells if t in have)  # for the reverse check only
    return out


def _int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def section_pages(sections: list[dict], last_page: int | None = None) -> list[set[int]]:
    """The pages each section may cover: its spans and crop page when it has them; otherwise the page it starts on
    up to the page where the next section on a later page starts (a paragraph runs on over a page break; tree order
    is not always page order, so sections starting on the same page do not end it). For running text the next
    section is the next one of running text: figures, tables, notes and boxes sit inside it."""
    starts = [_int(s.get("file_page")) for s in sections]
    # Figures, tables, notes and boxes are placed inside the running text: the text before them runs on past them.
    inserted = [s.get("type") in INSERTED or bool(s.get("small_print")) for s in sections]  # footnotes too
    flow = [p if not ins else None for ins, p in zip(inserted, starts)]
    out = []
    for i, s in enumerate(sections):
        pages = {int(p) for p in (s.get("spans") or {}) if _int(p)}
        for k in ("area", "image_bbox", "caption_box"):
            if isinstance(s.get(k), dict) and _int(s[k].get("page")):
                pages.add(int(s[k]["page"]))
        start = starts[i]
        if start is not None:
            pages.add(start)
            if not s.get("spans"):
                nxt = next((p for p in (starts if inserted[i] else flow)[i + 1:]
                            if p is not None and p > start), None)
                if nxt is None:  # the last running text runs on to the end of the file
                    nxt = last_page if last_page and not inserted[i] else start
                pages.update(range(start, nxt + 1))
        out.append(pages)
    return out


def tree_pools(tree: dict, last_page: int | None = None) -> tuple[Counter, dict[int, Counter], list[str], Counter, Counter]:
    """All tree tokens (pdf and model), tokens per page, the token sequence (for split words), and the pdf-origin
    and model-origin tokens apart (for the reverse check; row sentences only there)."""
    sections = tree.get("sections") or []
    pages = section_pages(sections, last_page)
    whole, per_page, seq = Counter(), defaultdict(Counter), []
    pdf_t, model_t = Counter(), Counter()
    for t in tokens(tree.get("title")):
        whole[t] += 1
        seq.append(t)
        pdf_t[t] += 1
    first = min((p for ps in pages for p in ps), default=1)
    for t in tokens(tree.get("title")):
        per_page[first][t] += 1
        per_page[1][t] += 1
    for s, ps in zip(sections, pages):
        all_ws = section_words(s)
        ws = [(t, o) for t, o in all_ws if o != "model-copy"]
        c = Counter(t for t, _ in ws)
        whole.update(c)
        seq.extend(t for t, _ in ws)
        for t, o in all_ws:
            (pdf_t if o == "pdf" else model_t)[t] += 1
        for p in ps:
            per_page[p].update(c)
        for r in s.get("row_sentences") or []:
            model_t.update(tokens(r))
    return whole, per_page, seq, pdf_t, model_t


# ---------------------------------------------------------------- matching words

def _variants(w: str) -> set[str]:
    """w with one ligature written short: removed ("fifind" -> "find", "find" -> "nd") or read as its first letter
    ("fire" -> "fre", "floor" -> "foor"): the PDF font dropped or mangled it."""
    out = set()
    for lig in LIGATURES:
        k = w.find(lig)
        while k >= 0:
            out.add(w[:k] + w[k + len(lig):])
            out.add(w[:k] + lig[:-1] + w[k + len(lig):])
            k = w.find(lig, k + 1)
    out.discard(w)
    return out


def match(seq: list[str], pool: Counter, tree_seq: list[str] | None = None) -> list[bool]:
    """Which raw tokens in seq the pool (tree tokens) covers. Consumes the pool. After the plain multiset match:
    two or three raw tokens that join to a tree token ("W hat" in the PDF), a raw token that is two adjacent tree
    tokens joined ("W hat" in the tree), and a letter pair the PDF font dropped or doubled ("nd" / "fifind" for
    "find", which parse_adoc repairs)."""
    got = [False] * len(seq)
    for i, w in enumerate(seq):
        if pool[w] > 0:
            pool[w] -= 1
            got[i] = True
    missing = [i for i, g in enumerate(got) if not g]
    if not missing:
        return got
    for i in missing:  # raw split, tree whole
        if got[i]:
            continue
        for n in (2, 3):
            if i + n <= len(seq) and not any(got[i:i + n]):
                j = "".join(seq[i:i + n])
                if pool[j] > 0:
                    pool[j] -= 1
                    got[i:i + n] = [True] * n
                    break
    if tree_seq:
        joined = defaultdict(set)
        for a, b in zip(tree_seq, tree_seq[1:]):
            if len(a) <= 3 or len(b) <= 3:
                joined[a + b].add((a, b))
        for i in missing:
            if got[i]:
                continue
            for a, b in joined.get(seq[i], ()):
                if pool[a] > 0 and pool[b] > 0 and (a != b or pool[a] > 1):
                    pool[a] -= 1
                    pool[b] -= 1
                    got[i] = True
                    break
    left = [i for i in missing if not got[i]]
    if left:
        by_variant = defaultdict(list)
        for t, n in pool.items():
            if n > 0 and any(lig in t for lig in LIGATURES):
                for v in _variants(t):
                    by_variant[v].append(t)
        for i in left:
            w = seq[i]
            cand = [t for t in by_variant.get(w, ()) if pool[t] > 0] or [v for v in _variants(w) if pool[v] > 0]
            if cand:
                pool[cand[0]] -= 1
                got[i] = True
    return got


# ---------------------------------------------------------------- why raw words are missing

def raw_lines(page: dict) -> list[dict]:
    """Upright words grouped into lines (top within 2.5pt), left to right."""
    ws = sorted((w for w in page["words"] if w[5]), key=lambda w: (w[2], w[1]))
    lines: list[dict] = []
    for w in ws:
        if lines and abs(w[2] - lines[-1]["top"]) <= 2.5:
            lines[-1]["words"].append(w)
        else:
            lines.append({"top": w[2], "words": [w]})
    for l in lines:
        l["words"].sort(key=lambda w: w[1])
        l["text"] = " ".join(w[0] for w in l["words"])
        l["x0"], l["x1"] = l["words"][0][1], max(w[3] for w in l["words"])
        l["bottom"] = max(w[4] for w in l["words"])
    return lines


PAGE_NO_LINE = re.compile(r"(page\s+)?(\d{1,4}|[ivxlc]{1,6})(\s+of\s+\d+(\s+pages)?)?", re.I)
IMPRINT_RE = re.compile(r"\bISBN\b|©|Crown copyright|Published by|First published|Stock code", re.I)
LABEL_RE = re.compile(r"^(Regulation|ACOP|Guidance|Schedule)\s+\d+[A-Z]?(\(\w+\)([–-]\(\w+\))?)?$|^(Summary|Guidance|ACOP)$")
BULLET_LETTERS = {"n", "l", "q", "u"}
FORM_WORDS = {"Yes", "No", "N/A"}
CONTENTS_TITLES = {"contents", "content", "table of contents", "contents page"}
INDEX_TITLES = {"index", "list of approved documents"}


def _norm_line(t: str) -> str:
    return re.sub(r"\d+", "#", " ".join(tokens(t)))


QUOTED_SKIP_RE = re.compile(r"file page (\d+): (\d+) lines? of [^:]*skipped[^:]*: (.+)$")


def _issue_pages(tree: dict) -> tuple[set[int], list[tuple[int, list[str], int]]]:
    """Pages a tree issue says were skipped as a whole, and (page, first words, line count) for issues that skip a
    few lines and quote them ("2 lines of very small print skipped (...): a b c d"). Only those lines are explained,
    not the rest of their page (a whole-page reason hid lost rows on the same page)."""
    whole, quoted = set(), []
    for i in tree.get("issues") or []:
        q = QUOTED_SKIP_RE.match(str(i))
        if q:
            toks = tokens(q.group(3))
            if len(q.group(3)) >= 40 and len(toks) > 1:
                toks = toks[:-1]  # the quote is cut at 40 characters: its last word may be cut too
            if toks:
                quoted.append((int(q.group(1)), toks, int(q.group(2))))
                continue
        m = re.match(r"file page (\d+): .*(skipped|blacked out)", str(i))
        if m:
            whole.add(int(m.group(1)))
    return whole, quoted


def _quoted_lines(ls: list[dict], toks: list[str], n: int) -> list[list]:
    """The raw words of the n lines an issue quotes: the line whose words start with the quote (from that word
    on, a raw line can hold two columns), and the n - 1 lines under it from the same left edge on."""
    for k, l in enumerate(ls):
        lt = [tokens(w[0]) for w in l["words"]]
        flat = [(j, t) for j, ts in enumerate(lt) for t in ts]
        for a in range(len(flat)):
            if [t for _, t in flat[a:a + len(toks)]] == toks:
                x = l["words"][flat[a][0]][1]
                out = [w for w in l["words"][flat[a][0]:]]
                for l2 in ls[k + 1:k + n]:
                    out += [w for w in l2["words"] if w[1] >= x - 2]
                return out
    return []


def word_reasons(raw: dict, tree: dict) -> tuple[list[list[str | None]], dict]:
    """For every raw word, the rule-based reason a parser may drop it (None: content). Also returns page facts:
    front pages, contents pages, index pages, the last page."""
    pages = raw["pages"]
    count = len(pages)
    is_ad = str(tree.get("parser", "")).startswith(AD_PARSER)
    stops = str(tree.get("parser", "")).startswith(STOPS_AT_INDEX)
    labels = any(s.get("status") for s in tree.get("sections") or [])
    booklet = str(tree.get("parser", "")).startswith("home-office-booklet")
    lines = [raw_lines(p) for p in pages]
    # running headers and footers: a line in the top or bottom band repeating on many pages
    seen: dict[tuple, set] = defaultdict(set)
    for p, ls in zip(pages, lines):
        for l in ls:
            band = "top" if l["top"] < 0.11 * p["height"] else ("bottom" if l["top"] > 0.92 * p["height"] else None)
            if band:
                seen[(band, _norm_line(l["text"]))].add(p["n"])
    need = max(2, min(3, int(0.3 * count)))
    furniture = {k for k, v in seen.items() if len(v) >= need and k[1]}
    fur_texts = defaultdict(list)
    for b, t in furniture:
        fur_texts[b].append(t)
    # pages: where the tree starts, contents, index
    # The first page of content after the cover. parse_pdf keeps content found before the first chapter in a
    # "front-matter" chapter (a cover blurb on page 1) and still drops the imprint and contents pages around it,
    # so that chapter does not end the front matter.
    secs = tree.get("sections") or []
    parent = {s.get("id"): s.get("parent_id") for s in secs}

    def root(sid):
        seen = set()
        while parent.get(sid) and sid not in seen:
            seen.add(sid)
            sid = parent[sid]
        return sid

    starts = [p for s, ps in zip(secs, section_pages(secs)) if root(s.get("id")) != "front-matter" for p in ps]
    first = min(starts, default=count + 1)
    front_ok = first - 1 <= max(4, int(0.15 * count))  # a long run before the first section is not front matter
    contents, index_from = set(), None
    for p, ls in zip(pages, lines):
        n = p["n"]
        head = [l for l in ls if l["top"] < 0.4 * p["height"]]
        if n <= max(6, int(0.2 * count)) and any(" ".join(tokens(l["text"])) in CONTENTS_TITLES for l in head):
            contents.add(n)
        elif n - 1 in contents and n <= max(8, int(0.25 * count)):
            body = [l for l in ls if 0.11 * p["height"] <= l["top"] <= 0.92 * p["height"]]
            entries = sum(1 for l in body if len(l["words"]) >= 2 and re.fullmatch(r"\d{1,3}", l["words"][-1][0]))
            if body and entries >= 0.4 * len(body):  # a contents page runs on: most lines end in a page number
                contents.add(n)
        if index_from is None and stops and n >= 0.7 * count and any(" ".join(tokens(l["text"])) in INDEX_TITLES for l in head):
            index_from = n
    issue_pages, quoted = _issue_pages(tree)
    figs = [s for s in tree.get("sections") or [] if s.get("type") == "figure" and isinstance(s.get("area"), dict)]
    def upright(pg):  # words counted for "a short page": not the sideways spine letters of a cover
        return sum(1 for w in pg["words"] if w[5])

    last_short = bool(pages) and (upright(pages[-1]) < 300  # a short last page, or the publisher's imprint
                                  or any(w[0] in ("ISBN", "©") for w in pages[-1]["words"]))
    out = []
    for p, ls in zip(pages, lines):
        n, ph = p["n"], p["height"]
        reason_of: dict[int, str] = {}
        page_reason = None
        if n in issue_pages:
            page_reason = "issue"
        elif n < first and front_ok and (n in contents or upright(p) < (150 if n == 1 else 100)
                                         or IMPRINT_RE.search(" ".join(w[0] for w in p["words"]))):
            page_reason = "cover" if n == 1 else ("contents" if n in contents else "front")
        elif n in contents:
            page_reason = "contents"
        elif index_from and n >= index_from:
            page_reason = "index"
        elif n == count and count > 2 and last_short:
            page_reason = "back"
        for qp, toks, nl in quoted:
            if qp == n and not page_reason:
                for w in _quoted_lines(ls, toks, nl):
                    reason_of[id(w)] = "issue"
        prev_texts: list[tuple[float, float, str]] = []
        for l in ls:
            t = l["text"].strip()
            nt = _norm_line(t)
            band = "top" if l["top"] < 0.11 * ph else ("bottom" if l["top"] > 0.92 * ph else None)
            r = None
            if band and PAGE_NO_LINE.fullmatch(t):
                r = "page-number"
            elif re.fullmatch(r"(?:\S\s){4,}\S(?:\s+\d+)?|(?:\d+\s+)?(?:\S\s){4,}\S", t) and "O N L I N E" in t.upper():
                r = "watermark"
            elif band and ((band, nt) in furniture or (len(t) >= 6 and any(nt and nt in ft for ft in fur_texts[band]))):
                r = "furniture"
            elif is_ad and (l["top"] < 82 or l["top"] >= 795):
                r = "furniture"
            elif re.search(r"(\.\s?){4,}\s*\d+$|\s{0,1}\.{4,}", t) and re.search(r"\d+$", t):
                r = "contents"
            elif any(abs(l["top"] - a) <= 8 and abs(l["x0"] - b) <= 12 and t == c for a, b, c in prev_texts):
                r = "duplicate"
            prev_texts.append((l["top"], l["x0"], t))
            if r:
                for w in l["words"]:
                    reason_of[id(w)] = r
                continue
            ws = l["words"]
            if len(ws) > 1 and ws[0][0] in BULLET_LETTERS:
                reason_of[id(ws[0])] = "bullet"
            if labels and ws[0][1] < 120:
                for k in (2, 1):
                    if len(ws) >= k and LABEL_RE.match(" ".join(w[0] for w in ws[:k])):
                        for w in ws[:k]:
                            reason_of[id(w)] = "margin-label"
                        break
            if booklet:
                for w in ws:
                    if w[0] in FORM_WORDS:
                        reason_of[id(w)] = "form"
        dup = set()  # a word printed again within 4pt of itself (bold faked by overprinting, "3.14 3.14")
        recent: list = []
        for w in sorted(p["words"], key=lambda w: (w[2], w[1])):
            if any(o[0] == w[0] and abs(o[1] - w[1]) <= 4 and abs(o[2] - w[2]) <= 4 for o in recent):
                dup.add(id(w))
            else:
                recent = (recent + [w])[-12:]
        rs = []
        for w in p["words"]:
            if not w[5]:
                rs.append("sideways")
            elif page_reason:
                rs.append(page_reason)
            elif id(w) in dup:
                rs.append("duplicate")
            elif id(w) in reason_of:
                rs.append(reason_of[id(w)])
            elif any(f["area"].get("page") == n and f["area"]["x0"] - 2 <= w[1] and w[3] <= f["area"]["x1"] + 2
                     and f["area"]["top"] - 2 <= w[2] and w[4] <= f["area"]["bottom"] + 2 for f in figs):
                rs.append("in-figure")
            else:
                rs.append(None)
        out.append(rs)
    facts = {"first_page": first, "front_ok": front_ok, "contents": sorted(contents), "index_from": index_from,
             "issue_pages": sorted(issue_pages), "furniture": sorted(" / ".join(k) for k in furniture)[:20]}
    return out, facts


# ---------------------------------------------------------------- the three checks

def _snippet(words: list, limit: int = 18) -> str:
    words = [w for w in words if w]
    s = " ".join(words[:limit])
    return s + (" ..." if len(words) > limit else "")


def check_text(raw: dict, tree: dict, sha8: str) -> dict:
    reasons, facts = word_reasons(raw, tree)
    whole, per_page, tree_seq, pdf_t, model_t = tree_pools(tree, len(raw["pages"]))
    # raw tokens, with page, reason and the printed word they came from
    occ = []  # (page, token, reason, printed word)
    for p, rs in zip(raw["pages"], reasons):
        for w, r in zip(p["words"], rs):
            for k, t in enumerate(tokens(w[0])):
                occ.append((p["n"], t, r, w[0] if k == 0 else None))  # the printed word once, for snippets
    content = [o for o in occ if o[2] is None]
    dropped = [o for o in occ if o[2] is not None]
    pool = Counter(whole)
    got = match([o[1] for o in content], pool, tree_seq)
    got_d = match([o[1] for o in dropped], pool, tree_seq)
    # per page, against the sections that cover that page
    grams = {tuple(tree_seq[k:k + 4]) for k in range(len(tree_seq) - 3)}
    by_page = defaultdict(list)
    for o, g in zip(content, got):
        by_page[o[0]].append((o, g))
    pages, items = [], []
    for p in raw["pages"]:
        n = p["n"]
        rows = by_page.get(n, [])
        local = match([o[1] for o, _ in rows], Counter(per_page.get(n, Counter())), tree_seq) if rows else []
        hit = sum(local)
        miss_words = [o[3] for (o, g), lg in zip(rows, local) if not lg and not g]
        pages.append({"page": n, "words": len(rows), "local": hit, "unexplained": len(miss_words)})
        if len(rows) >= PAGE_MIN_WORDS and hit < PAGE_EMPTY * len(rows):
            lost = [o[3] for (o, g), lg in zip(rows, local) if not lg]
            seq = [o[1] for o, _ in rows]
            runs = [tuple(seq[k:k + 4]) for k in range(len(seq) - 3)]
            found = sum(r in grams for r in runs) / len(runs) if runs else 0.0
            how = (f"{found:.0%} of its 4-word runs are in the tree under other pages (repeated text, or a wrong "
                   f"file_page)" if found >= 0.5 else "lost")
            items.append({"key": f"{sha8}:p{n}:text", "kind": "page" if how == "lost" else "page-misplaced", "page": n,
                          "detail": f"{len(rows)} words, {hit} in the tree on this page, {how}: \"{_snippet(lost)}\""})
    n_raw, n_content = len(occ), len(content)
    matched = sum(got)
    unexplained = n_content - matched
    explained = Counter(o[2] for o, g in zip(dropped, got_d) if not g)
    share = unexplained / n_content if n_content else 0.0
    worst = sorted((p for p in pages if p["unexplained"]), key=lambda p: -p["unexplained"])[:3]
    examples = []
    for wp in worst:
        rows = by_page[wp["page"]]
        miss = [o[3] for o, g in rows if not g]
        examples.append(f"p{wp['page']} ({wp['unexplained']} words): \"{_snippet(miss, 14)}\"")
    if n_content and share > DOC_UNEXPLAINED:
        items.append({"key": f"{sha8}:doc:text", "kind": "doc", "page": None,
                      "detail": f"{share:.0%} of {n_content} words missing for no named reason; "
                                + "; ".join(examples)})
    if n_raw == 0 and (whole or tree.get("sections")):
        pass  # a PDF with no text layer: the image check speaks for it
    # reverse: tree words that are nowhere in the raw file (set-based; model rows repeat headers)
    raw_set = {o[1] for o in occ}
    raw_seq = [o[1] for o in occ]
    raw_set |= {a + b for a, b in zip(raw_seq, raw_seq[1:])}
    raw_var = {v for t in raw_set for v in _variants(t)} if raw_set else set()

    def novel(c: Counter) -> Counter:
        return Counter({t: n for t, n in c.items() if t not in raw_set and t not in raw_var
                        and not (_variants(t) & raw_set)})

    extra_pdf, extra_model = novel(pdf_t), novel(model_t)
    return {"raw_words": n_raw, "content_words": n_content, "matched": matched, "unexplained": unexplained,
            "unexplained_share": share, "explained": dict(explained), "coverage": matched / n_content if n_content else 1.0,
            "pages": pages, "items": items, "examples": examples, "facts": facts,
            "extra_pdf": sum(extra_pdf.values()), "extra_pdf_words": [t for t, _ in extra_pdf.most_common(8)],
            "extra_model": sum(extra_model.values()), "extra_model_words": [t for t, _ in extra_model.most_common(8)],
            "tree_words": sum(whole.values())}


def _rect(d: dict | None) -> tuple | None:
    if not isinstance(d, dict) or not all(k in d for k in ("x0", "x1", "top", "bottom")):
        return None
    return (d["x0"], d["top"], d["x1"], d["bottom"])


def _inter(a: tuple, b: tuple) -> float:
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def figure_boxes(tree: dict) -> dict[int, list[tuple]]:
    """Every figure crop and picture box in the tree, by page."""
    out = defaultdict(list)
    for s in tree.get("sections") or []:
        for k in ("area", "image_bbox", "images_bbox", "box"):
            d = s.get(k)
            r = _rect(d)
            if r and _int(d.get("page")):
                out[int(d["page"])].append(r)
            if isinstance(d, dict) and isinstance(d.get("single"), dict) and _rect(d["single"]):
                out[int(d["single"].get("page", d.get("page")))].append(_rect(d["single"]))
    return out


def table_spans(tree: dict) -> dict[int, list[tuple[float, float, str]]]:
    """Vertical spans of table sections per page (top, bottom, section id)."""
    out = defaultdict(list)
    for s in tree.get("sections") or []:
        if s.get("type") == "table":
            for p, v in (s.get("spans") or {}).items():
                if _int(p) and isinstance(v, list) and len(v) == 2:
                    out[int(p)].append((v[0], v[1], s["id"]))
    return out


def _signature_or_logo(im: tuple, n: int, ls: list[dict]) -> bool:
    """parse_pdf.signature_or_logo on this module's own lines (S107: one rule, not a copy). A raw line here can
    hold two text columns, so each line also carries the words under the image."""
    from system.rag.parse_pdf import signature_or_logo

    x0, top, x1, bottom = im
    lines = [{"text": l["text"], "top": l["top"], "bottom": l["bottom"], "x0": l["x0"], "x1": l["x1"],
              "under": " ".join(w[0] for w in l["words"] if w[1] < x1 and w[3] > x0) or l["text"],
              "left": " ".join(w[0] for w in l["words"] if w[3] <= x0 + 5)} for l in ls]
    return signature_or_logo({"x0": x0, "top": top, "x1": x1, "bottom": bottom}, n, lines)


def check_images(raw: dict, tree: dict, text: dict, sha8: str) -> dict:
    facts = text["facts"]
    count = len(raw["pages"])
    boxes = figure_boxes(tree)
    tspans = table_spans(tree)
    issue_at = set()
    for i in tree.get("issues") or []:
        m = re.match(r"image on file page (\d+) at (-?[\d.]+) has no caption", str(i))
        if m:
            issue_at.add((int(m.group(1)), round(float(m.group(2)))))
    seen_on = Counter()
    for p in raw["pages"]:
        for b in {tuple(round(v) for v in im) for im in p["images"]}:
            seen_on[b] += 1
    words_on = {pg["page"]: pg["words"] for pg in text["pages"]}
    total, in_crop, explained, items = 0, 0, Counter(), []
    for p in raw["pages"]:
        n, pw, ph = p["n"], p["width"], p["height"]
        ls = None
        done = set()
        for im in p["images"]:
            r = (max(im[0], 0), max(im[1], 0), min(im[2], pw), min(im[3], ph))
            area = max(r[2] - r[0], 0) * max(r[3] - r[1], 0)
            key = tuple(round(v) for v in im)
            if area < MIN_IMAGE_SHARE * pw * ph or key in done:
                continue
            done.add(key)
            total += 1
            if any(_inter(r, b) >= IMAGE_IN_CROP * area for b in boxes.get(n, [])):
                in_crop += 1
                continue
            why = None
            if n < facts["first_page"] and facts["front_ok"] or n in facts["contents"]:
                why = "cover"
            elif facts["index_from"] and n >= facts["index_from"] or n == count and count > 2:
                why = "back"
            elif area >= 0.6 * pw * ph and words_on.get(n, 0) >= 50:
                why = "background"
            elif min(r[2] - r[0], r[3] - r[1]) < 0.025 * min(pw, ph) or \
                    max(r[2] - r[0], r[3] - r[1]) >= 8 * max(min(r[2] - r[0], r[3] - r[1]), 1):
                why = "band"
            elif seen_on[key] >= 3:
                why = "repeated"
            elif (n, round(im[1])) in issue_at or (n, round(im[1], 1)) in issue_at:
                why = "issue"
            elif any(t - 2 <= r[1] and r[3] <= b + 2 for t, b, _ in tspans.get(n, [])):
                why = "table"
            else:
                ls = ls if ls is not None else raw_lines(p)
                if _signature_or_logo(r, n, ls):
                    why = "signature"
            if why:
                explained[why] += 1
                continue
            items.append({"key": f"{sha8}:p{n}:image@{round(im[0])},{round(im[1])}", "kind": "image", "page": n,
                          "detail": f"image {round(r[2] - r[0])}x{round(r[3] - r[1])}pt at ({round(im[0])}, "
                                    f"{round(im[1])}), {area / (pw * ph):.0%} of the page, in no figure crop"})
    return {"images": total, "in_crop": in_crop, "explained": dict(explained), "items": items}


def check_tables(raw: dict, tree: dict, text: dict, sha8: str) -> dict:
    facts = text["facts"]
    _, per_page, tree_seq, _, _ = tree_pools(tree, len(raw["pages"]))
    secs = defaultdict(list)  # page -> [(top, bottom) or None, id] of table and figure sections
    for s, ps in zip(tree.get("sections") or [], section_pages(tree.get("sections") or [], len(raw["pages"]))):
        if s.get("type") not in TABLE_HOMES:
            continue
        spans = s.get("spans") or {}
        area = s.get("area") if isinstance(s.get("area"), dict) else None
        for p in ps:
            v = spans.get(str(p)) or spans.get(p)
            if isinstance(v, list) and len(v) == 2:
                secs[p].append(((v[0], v[1]), s["id"]))
            elif area and _int(area.get("page")) == p:
                secs[p].append(((area["top"], area["bottom"]), s["id"]))
            elif not spans and not area:
                secs[p].append((None, s["id"]))
    total, found, explained, items = 0, 0, Counter(), []
    crops = defaultdict(list)  # figure crops (the area cut out), by page
    for s in tree.get("sections") or []:
        a = s.get("area")
        if s.get("type") == "figure" and _rect(a) and _int(a.get("page")):
            crops[int(a["page"])].append(_rect(a))
    for p in raw["pages"]:
        n = p["n"]
        for t in p["tables"]:
            total += 1
            x0, top, x1, bottom = t["bbox"]
            if (x1 - x0) >= PAGE_FRAME * p["width"] and (bottom - top) >= PAGE_FRAME * p["height"]:
                explained["a frame round the whole page, not a table"] += 1  # its words are in the text check
                continue
            if any(b[0] - 2 <= x0 and x1 <= b[2] + 2 and b[1] - 2 <= top and bottom <= b[3] + 2 for b in crops.get(n, [])):
                explained["inside a figure crop (kept as the picture)"] += 1  # as words inside a crop are
                continue
            if n < facts["first_page"] and facts["front_ok"] or n in facts["contents"] or n in facts["issue_pages"] \
                    or facts["index_from"] and n >= facts["index_from"]:
                explained["front or back matter, contents, index"] += 1
                continue
            cell = [w for r in t["rows"] for c in r for w in tokens(c)]
            got = match(cell, Counter(per_page.get(n, Counter())), tree_seq) if cell else []
            share = sum(got) / len(cell) if cell else 1.0
            sec = next((sid for span, sid in secs.get(n, []) if span is None or span[0] < bottom + 5 and top - 5 < span[1]),
                       None)
            if sec and share >= TABLE_WORDS:
                found += 1
                continue
            first_row = " | ".join(c for c in t["rows"][0] if c)[:70]
            if sec:
                why = f"{sec} is there but only {share:.0%} of the cell words"
                kind = "words missing"
            elif share >= TABLE_WORDS:
                why = f"no table, figure or requirement section here; {share:.0%} of the cell words are in the tree as text"
                kind = "as text"
            else:
                why = f"no table, figure or requirement section here and only {share:.0%} of the cell words"
                kind = "missing"
            items.append({"key": f"{sha8}:p{n}:table@{round(top)}", "kind": "table", "page": n, "table": kind,
                          "detail": f"{len(t['rows'])}x{max(len(r) for r in t['rows'])} table at top {round(top)}: "
                                    f"{why}; first row \"{first_row}\""})
    return {"tables": total, "found": found, "explained": dict(explained), "items": items}


# ---------------------------------------------------------------- versions in scope, accepted items, report

def versions_in_scope(source_ids: list[str] | None = None) -> list[tuple[dict, Path]]:
    """(version record, tree path) for every version in scope (corpus.in_scope, ADR 0016: in force on or after
    1 January 2025) with a reader for its file type and a parsed tree."""
    from system.rag.corpus import in_scope as version_in_scope

    sources = {s["id"]: s for s in load_sources()["sources"]}
    out = []
    parsed = CORPUS_DIR / "parsed"
    ids = source_ids or sorted(p.name for p in parsed.iterdir() if p.is_dir()) if parsed.exists() else []
    for sid in ids:
        for tp in sorted((parsed / sid).glob("*.json")):
            vid = tp.stem
            rp = CORPUS_DIR / "versions" / sid / f"{vid}.json"
            if not rp.exists():
                continue
            rec = json.loads(rp.read_text(encoding="utf-8"))
            if version_in_scope(rec, sources.get(sid)) and rec.get("media_type") in READERS:
                out.append((rec, tp))
    return out


def accepted_path(source_id: str) -> Path:
    return CORPUS_DIR / "coverage" / f"{source_id}.json"


def load_accepted(source_id: str) -> dict:
    p = accepted_path(source_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"source_id": source_id,
            "about": f"Coverage items a person looked at and keeps, for {source_id} (system/rag/coverage.py).",
            "accepted": {}}


def check_version(rec: dict, tree: dict, raw: dict | None = None) -> dict:
    raw = raw if raw is not None else raw_doc(rec)
    sha8 = rec["sha256"][:8]
    if raw.get("kind") in ("html", "xml"):
        r = check_blocks(raw, tree, sha8)
        items = r["text"]["items"] + r["images"]["items"] + r["tables"]["items"]
        if not tree.get("sections") and r["text"]["content_words"]:
            items.insert(0, {"key": f"{sha8}:doc:empty", "kind": "empty", "page": None,
                             "detail": f"the tree has no sections; the file has {r['text']['content_words']} words"})
        return {"source_id": rec["source_id"], "version_id": rec["version_id"], "parser": tree.get("parser"),
                "pages": 0, "blocks": len(raw["blocks"]), **r, "items": items}
    text = check_text(raw, tree, sha8)
    images = check_images(raw, tree, text, sha8)
    tables = check_tables(raw, tree, text, sha8)
    items = text["items"] + images["items"] + tables["items"]
    if not tree.get("sections") and text["raw_words"]:
        items.insert(0, {"key": f"{sha8}:doc:empty", "kind": "empty", "page": None,
                         "detail": f"the tree has no sections; the PDF has {text['raw_words']} words"})
    return {"source_id": rec["source_id"], "version_id": rec["version_id"], "parser": tree.get("parser"),
            "pages": len(raw["pages"]), "text": text, "images": images, "tables": tables, "items": items}


def check_source(source_id: str, versions: list[tuple[dict, Path]]) -> list[dict]:
    acc = load_accepted(source_id)["accepted"]
    out = []
    for rec, tp in versions:
        r = check_version(rec, json.loads(tp.read_text(encoding="utf-8")))
        r["open"] = [i for i in r["items"] if i["key"] not in acc]
        r["accepted"] = [i for i in r["items"] if i["key"] in acc]
        out.append(r)
    return out


def fill_caches(versions: list[tuple[dict, Path]], workers: int = 3) -> None:
    todo = [rec for rec, _ in versions
            if not (cache_path(rec["source_id"], rec["sha256"], rec["media_type"]).exists() and (ROOT / rec["raw_path"]).exists())]
    todo = [r for r in todo if (ROOT / r["raw_path"]).exists()]
    if not todo:
        return
    print(f"reading {len(todo)} raw files (cached afterwards) ...", file=sys.stderr)
    if workers > 1 and len(todo) > 1:
        from multiprocessing import Pool

        with Pool(workers) as pool:
            for _ in pool.imap_unordered(_fill_cache, todo):
                pass
    else:
        for r in todo:
            _fill_cache(r)


def _line(r: dict) -> str:
    t, im, tb = r["text"], r["images"], r["tables"]
    return (f"text {t['coverage']:.1%} (unexplained {t['unexplained_share']:.1%}), "
            f"pages lost {sum(1 for i in r['items'] if i['kind'] == 'page')}, "
            f"misplaced {sum(1 for i in r['items'] if i['kind'] == 'page-misplaced')}, "
            f"images unexplained {len(im['items'])}/{im['images']}, "
            f"tables missing {len(tb['items'])}/{tb['tables']}, "
            f"tree words not in the PDF {t['extra_pdf']} (model grids {t['extra_model']})")


def report(source_ids: list[str] | None = None, verbose: bool = False, workers: int = 3,
           json_out: Path | None = None) -> int:
    versions = [v for v in versions_in_scope(source_ids) if (ROOT / v[0]["raw_path"]).exists()]
    fill_caches(versions, workers)
    by_src = defaultdict(list)
    for v in versions:
        by_src[v[0]["source_id"]].append(v)
    tot = Counter()
    reasons, img_reasons = Counter(), Counter()
    shares, results = [], []
    for sid in sorted(by_src):
        for r in check_source(sid, by_src[sid]):
            results.append({k: v for k, v in r.items() if k != "text"} | {"text": {k: v for k, v in r["text"].items() if k != "pages"}})
            t, im, tb = r["text"], r["images"], r["tables"]
            name = sid if len(by_src[sid]) == 1 else f"{sid} {r['version_id'][:50]}"
            print(f"{name}: {_line(r)}" + (f", accepted {len(r['accepted'])}" if r["accepted"] else ""))
            for i in r["open"]:
                print(f"    [{i['kind']}] {i['key']}: {i['detail']}")
            if verbose:
                print(f"    reasons: " + ", ".join(f"{k} {v}" for k, v in sorted(t["explained"].items(), key=lambda kv: -kv[1])))
                if t["extra_pdf_words"]:
                    print(f"    tree words not in the PDF (text fields): {' '.join(t['extra_pdf_words'])}")
                if t["extra_model_words"]:
                    print(f"    tree words not in the PDF (model grids): {' '.join(t['extra_model_words'])}")
                for e in t["examples"]:
                    print(f"    unexplained {e}")
            shares.append((t["unexplained_share"], name))
            reasons.update(t["explained"])
            img_reasons.update(im["explained"])
            tot.update(versions=1, pages=r["pages"], raw=t["raw_words"], content=t["content_words"],
                       matched=t["matched"], unexplained=t["unexplained"], images=im["images"], in_crop=im["in_crop"],
                       img_open=len(im["items"]), tables=tb["tables"], tables_found=tb["found"],
                       tables_open=len(tb["items"]), pages_flagged=sum(1 for i in r["items"] if i["kind"] == "page"),
                       pages_misplaced=sum(1 for i in r["items"] if i["kind"] == "page-misplaced"),
                       docs_flagged=sum(1 for i in r["items"] if i["kind"] in ("doc", "empty")),
                       open=len(r["open"]), accepted=len(r["accepted"]), extra_pdf=t["extra_pdf"],
                       extra_model=t["extra_model"])
    content = tot["content"] or 1
    print(f"TOTAL: {tot['versions']} versions, {tot['pages']} pages; text {tot['matched'] / content:.1%} of "
          f"{tot['content']} words (unexplained {tot['unexplained'] / content:.1%}; {tot['raw'] - tot['content']} "
          f"more dropped by named reasons); documents flagged {tot['docs_flagged']}, pages flagged "
          f"{tot['pages_flagged']} lost, {tot['pages_misplaced']} with their text under another page; images {tot['images']}: {tot['in_crop']} in crops, {tot['img_open']} unexplained; "
          f"tables {tot['tables']}: {tot['tables_found']} found, {tot['tables_open']} missing; open items "
          f"{tot['open']}, accepted {tot['accepted']}")
    if json_out:
        json_out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    if verbose:
        print("dropped words by reason: " + ", ".join(f"{k} {v}" for k, v in reasons.most_common()))
        print("explained images by reason: " + ", ".join(f"{k} {v}" for k, v in img_reasons.most_common()))
        cuts = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
        dist = Counter(next((f"<={c:.1%}" for c in cuts if s <= c), ">50%") for s, _ in shares)
        print("unexplained share per document: " + ", ".join(f"{k} {dist[k]}" for k in
                                                              [f"<={c:.1%}" for c in cuts] + [">50%"] if dist[k]))
    return 1 if tot["open"] else 0


def accept(source_id: str, item: str, reason: str, by: str, today: str | None = None) -> int:
    """A person looked at a flagged item and keeps it: record why. The item must be flagged now."""
    versions = versions_in_scope([source_id])
    flagged = {i["key"]: (r["version_id"], i) for r in check_source(source_id, versions) for i in r["items"]}
    if item not in flagged:
        print(f"{item} is not flagged for {source_id}")
        return 1
    doc = load_accepted(source_id)
    vid, i = flagged[item]
    doc["accepted"][item] = {"version_id": vid, "kind": i["kind"], "page": i["page"], "detail": i["detail"],
                             "reason": reason, "by": by, "date": today or datetime.date.today().isoformat()}
    doc["accepted"] = dict(sorted(doc["accepted"].items()))
    p = accepted_path(source_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"accepted {item}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        return audit()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("audit", help="write corpus/coverage.md (which sources are parsed, checked, chunked)")
    r = sub.add_parser("report", help="raw file against parsed tree: text, images, tables")
    r.add_argument("--source", nargs="*")
    r.add_argument("--verbose", action="store_true", help="reasons, words not in the PDF, examples, distribution")
    r.add_argument("--workers", type=int, default=3)
    r.add_argument("--json", type=Path, help="also write every result here, for analysis")
    c = sub.add_parser("accept", help="keep a flagged item, with the reason")
    c.add_argument("--source", required=True)
    c.add_argument("--item", required=True)
    c.add_argument("--reason", required=True)
    c.add_argument("--by", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "audit":
        return audit()
    if a.cmd == "accept":
        return accept(a.source, a.item, a.reason, a.by)
    return report(a.source, a.verbose, a.workers, a.json)


if __name__ == "__main__":
    sys.exit(main())
