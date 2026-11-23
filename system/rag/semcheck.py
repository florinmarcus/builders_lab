"""Semantic check: does each parsed tree say what its source says? A model reads the source next to the tree.

The coverage check (plain code) counts words, images and ruled tables. It cannot see a table whose cells sit in
the wrong column, a heading read as body text, a paragraph under the wrong number or two columns read as one.
This tool asks a model, in Claude Code on the user's plan (never Bedrock, never on our server, ADR 0006), to
compare the source with the tree, unit by unit:

- PDF: one page. The rendered page image against that page's tree content in reading order.
- Web page: one part of a page (split at its headings when long). The visible text against the tree sections.
- Legislation: one provision. The raw XML of the provision against its tree sections.

    python -m system.rag.semcheck sample                      # draw the sample once (fixed seed), corpus/semchecks/sample.json
    python -m system.rag.semcheck export [--source ID ...]    # packets for sampled units not judged yet
    python -m system.rag.semcheck run [--parallel 4]          # headless `claude -p`, batches of 6 packets
    python -m system.rag.semcheck save --answers DIR --by "Fable 5.2, Claude Code headless"
    python -m system.rag.semcheck report [--verbose] [--json FILE]
    python -m system.rag.semcheck accept --source ID --key KEY --as model-wrong|kept --reason "..." --by "..."

Verdicts are saved in `corpus/semchecks/<source>.json`, keyed by a hash of the source side (the page image, the
visible text, the XML) and the unit's tree content. A unit that did not change is not judged again; a unit that
changed (after a parser fix) comes back. A finding is a parser bug to fix, a model mistake (`accept --as
model-wrong`, after a person or the lead agent looked at the source) or a known limit kept on purpose (`accept
--as kept`). Never accept a finding only to make the report pass.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import random
import re
import subprocess
import sys
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from system.rag import coverage as C
from system.rag.corpus import CORPUS_DIR

ROOT = CORPUS_DIR.parent
SEED = 20261122
SCALE = 1.5                 # page images at 108 dpi: small print stays readable, an A4 page is about 890 x 1260
MODEL = "claude-fable-5-2"  # the only model used for this check (Florin, 22 Nov 2026)
BATCH = 6
LINE = 1500                 # no packet line is longer: the Read tool cuts lines over 2,000 characters
LONG_TEXT = 3000            # a section that runs over pages and is longer than this is cut to the part on the page
XML_LIMIT = 24000           # characters of a provision's XML and of its tree text shown; the rest is cut
WEB_PART_WORDS = 2000       # a web page is split at its headings into parts of about this many words
PDF_SHARE, PDF_MIN, PDF_CAP = 0.10, 3, 1500
LEG_TARGET, LEG_MIN = 300, 2

KINDS = ("missing", "garbled", "order", "structure", "table", "figure", "extra")
VERDICTS = ("ok",) + KINDS
SEVERITIES = ("high", "low")
ACCEPT_AS = ("model-wrong", "kept")
LEG_CONTAINERS = {"part", "chapter", "block", "schedule", "schedule-part"}

FINDINGS = """Findings. Give one for each real difference, the most important first, at most 8:
- "missing": text in the source that carries meaning and is not in the tree. Quote it.
- "garbled": words wrong, run together, split, or with wrong characters. Quote the source and the tree.
- "order": the reading order is wrong, or two columns are mixed into one text.
- "structure": the wrong type (a table read as running text or the reverse, a heading read as body text or the
  reverse), a wrong heading level or parent in `heading_path`, a wrong number, a footnote or note attached to
  the wrong place, two provisions merged into one or one split in two.
- "table": a table's cells, columns or rows do not match the source (a value in the wrong column or row, a
  missing or invented row or column, a wrong heading).
- "figure": a figure's description or labels contradict the picture.
- "extra": the tree has text that is not in the source.
Severity: "high" when the difference changes the meaning or loses a rule, a number, a limit, a unit, a "not",
a condition or a table value, or puts a rule under the wrong provision, so that a reader of the tree would be
misled. "low" when it is cosmetic: spacing, a split or joined word that still reads right, punctuation, a
heading level that changes nothing, a label out of order.
`verdict` is "ok" when there are no findings; otherwise the kind of the most serious finding. Do not report a
difference you are not sure you can see. In `evidence` quote the exact words (at most 25), as
`source: "..." / tree: "..."` when both sides matter."""

INSTRUCTIONS = {
    "pdf": """You check one page of a regulations or guidance document against what a parser kept of it.
The image is the page as printed. `content` is everything the parsed tree holds for this page, in reading order:
each section with its type, heading path (the breadcrumb of headings above it), number, title and text (`text`
is a list of lines; line breaks carry no meaning). Tables have `columns` and `grid` (one list of cells per row),
and `text`: the table's printed words as the file gives them, rows run together, with the notes printed under
the table at the end. Judge the cells from `grid` and the notes from `text`.
Figures have their caption in `title`, the words printed inside them in `labels`, and a `description` written
by a model.
Read the whole page image first, including small print, table cells, numbers and units. Then compare it with
`content` block by block.

Not errors (dropped or changed on purpose, do not report them):
- running headers and footers, page numbers, watermarks ("ONLINE VERSION"), the cover, contents pages, the
  index, the publisher's imprint, logos and decorative pictures. An empty `content` for such a page is "ok".
- line breaks, hyphens at line ends, bullet symbols, quote styles, bold and italic.
- a section with `from_earlier_page`: it started on an earlier page and only its end is on this page. A section
  with `may_run_on`: it may go on to the next page. `text_cut` means the text was cut to the part near this
  page ("[...]" marks the cut). Text of such sections that is not on this page is not "extra".
- a table that covers several pages is given whole (`table_pages`): judge only the rows on this page. In a grid,
  a cell that spans several rows is repeated on each row, a group heading may be moved into a first column of
  its own, and header rows printed one above the other may be joined into one column name. These are not errors
  when every value still sits under the right heading and beside the right row label.
- a figure's description is a summary. Report it only when it contradicts the picture or names the wrong thing.
  Words inside a picture that are missing from `labels` are "low", unless they give a rule, a number or a limit.
- text printed sideways in a margin, and a heading that the tree keeps only in `heading_path` or `title`.
""" + FINDINGS,
    "html": """You check one part of a web page (GOV.UK or HSE) against what a parser kept of it.
`source` is the visible text of this part of the page in reading order, one line per block, each starting with
its HTML tag in angle brackets (<h2>, <p>, <li>, <td> ...). A line that starts with "[dropped: reason]" is text
the parser leaves out on purpose (site header and footer, menus, breadcrumbs, cookie banner, feedback, "last
updated", contents list, related links). `source_tables` and `source_images` list this part's tables (rows of
cells) and pictures (alt text). `content` is what the parsed tree holds for this part, in reading order: each
section with its type, heading path, number, title and text (a list of lines); tables as `columns` and `grid`
(a table's `text`, when given, repeats its cells as running text).
Compare them block by block.

Not errors: the dropped lines, as long as they are page furniture and not guidance; line breaks; list bullets;
a heading that the tree keeps in `title` and `heading_path`; a numbered paragraph whose number is in `number`;
a picture kept only as its alt text. A "[dropped: ...]" line that is real guidance is "missing".
""" + FINDINGS,
    "xml": """You check one provision of UK legislation against what a parser kept of it.
`source_xml` is the provision's raw XML from legislation.gov.uk (a list of lines). `content` is the provision in
the parsed tree: the provision itself and the sections under it, each with its type, heading path, number,
title, text (a list of lines), status and `applies_to` (E, W, S, N.I.).
Compare the wording, the numbering and the nesting.

Not errors (dropped or changed on purpose): amendment markers and commentary references (CommentaryRef,
Addition, Substitution and Repeal tags: the words inside them are kept, the markers are not), footnote
references, formatting tags, extent attributes. A parent's `text` holds the text of its children too, and each
child is then given as its own section: that repeat is by design. Dots in the source that stand for repealed
text may be kept or shown as a status. A table is kept as rows of text. `source_xml` may be cut at the end
("[cut]"), and so may `content`: do not report what lies after a cut. The provision's title is the Title line
put first (it sits just above the provision in the file).
""" + FINDINGS,
}

ANSWER_FORMAT = {"verdict": "ok | " + " | ".join(KINDS),
                 "findings": [{"kind": " | ".join(KINDS), "problem": "one plain sentence",
                               "evidence": "the quoted words", "severity": "high | low"}],
                 "confidence": "high | medium | low"}

PROMPT = """You check a parsed regulations corpus against its sources. Work in the repo at `{root}`. Do not change any file except the one answers file named below.

For EACH packet below, separately and in order:
1. Read the JSON packet at the path given (paths are relative to `{root}`).
2. Open every image listed in its `images` (paths are relative to `{root}`) with the Read tool.
3. Follow the packet's `instructions` exactly. Judge each packet on its own.
4. Produce one line of JSON in the shape of `answer_format` (copy `key` and `kind` exactly from the packet).

Packets:
{packets}

Write all answers, one JSON object per line, in packet order, to `{root}/{answers}` with the Write tool. Each line must be valid JSON on a single line. Then reply only with "done" and the number of lines written."""


# ---------------------------------------------------------------- small helpers

def _sha(*parts: bytes | str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, bytes) else p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


def _canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def lines(text: str | None, width: int = LINE) -> list[str]:
    """A text as lines no longer than `width`: its own lines, long ones wrapped at a space."""
    out = []
    for ln in (text or "").split("\n"):
        ln = ln.strip()
        while len(ln) > width:
            cut = ln.rfind(" ", 0, width)
            cut = cut if cut > 0 else width
            out.append(ln[:cut])
            ln = ln[cut:].strip()
        if ln:
            out.append(ln)
    return out


def dump_packet(p: dict) -> str:
    """JSON with one short line per value; a table row is one line when it fits."""
    rows: list[str] = []

    def mark(o):
        if isinstance(o, dict):
            return {k: (_rows(v) if k in ("grid", "rows") else mark(v)) for k, v in o.items()}
        if isinstance(o, list):
            return [mark(x) for x in o]
        return o

    def _rows(v):
        out = []
        for r in v or []:
            one = json.dumps(r, ensure_ascii=False)
            if len(one) <= LINE:
                rows.append(one)
                out.append(f"@@ROW{len(rows) - 1}@@")
            else:
                out.append([x for c in r for x in (lines(str(c)) or [""])] if isinstance(r, list) else r)
        return out

    s = json.dumps(mark(p), ensure_ascii=False, indent=1)
    return re.sub(r'"@@ROW(\d+)@@"', lambda m: rows[int(m.group(1))], s)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for k of n."""
    if not n:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, mid - half), min(1.0, mid + half)


def family(tree: dict) -> str:
    return (tree.get("parser") or "unknown").split("/")[0]


def verdicts_path(source_id: str) -> Path:
    return CORPUS_DIR / "semchecks" / f"{source_id}.json"


def sample_path() -> Path:
    return CORPUS_DIR / "semchecks" / "sample.json"


def load_verdicts(source_id: str) -> dict:
    p = verdicts_path(source_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"source_id": source_id,
            "about": f"Model verdicts on source against tree for {source_id} (system/rag/semcheck.py).", "verdicts": {}}


def load_sample() -> dict:
    p = sample_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# ---------------------------------------------------------------- tree content of a unit

def _entry(s: dict, text: str | None = None, doc_title: str | None = None) -> dict:
    """One section as the model sees it: only the fields that carry content."""
    e = {"id": s.get("id"), "type": s.get("type")}
    if s.get("number") not in (None, ""):
        e["number"] = str(s["number"])
    if s.get("title"):
        e["title"] = s["title"]
    hp = [str(h) for h in s.get("heading_path") or []]
    if hp and doc_title and hp[0] == doc_title:
        hp = hp[1:]  # the document's title is in the packet once
    if hp:
        e["heading_path"] = " > ".join(hp)
    if s.get("type") == "table" and s.get("grid"):
        if s.get("columns"):
            e["columns"] = s["columns"]
        e["grid"] = s["grid"]
        if s.get("heading_rows"):
            e["heading_rows"] = s["heading_rows"]
    t = lines(s.get("text") if text is None else text)
    if t:
        e["text"] = t
    if s.get("type") == "figure":
        if s.get("labels"):
            e["labels"] = [x for lb in s["labels"] for x in lines(str(lb))]
        if s.get("description"):
            e["description"] = lines(s["description"])
    notes = [f.get("text") if isinstance(f, dict) else f for f in s.get("footnotes") or []]
    notes = [x for n in notes if n for x in lines(str(n))]
    if notes:
        e["footnotes"] = notes
    for k in ("limits", "status", "applies_to", "valid_from", "valid_to"):
        if s.get(k) not in (None, "", []):
            e[k] = lines(s[k]) if k == "limits" else s[k]
    return e


def _grams(toks: list[str], n: int = 3) -> set[tuple]:
    return {tuple(toks[k:k + n]) for k in range(len(toks) - n + 1)}


def _run_members(ok: list[bool], need: int) -> list[int]:
    """Indexes that lie in a run of at least `need` True values."""
    out, k = [], 0
    while k < len(ok):
        if not ok[k]:
            k += 1
            continue
        j = k
        while j < len(ok) and ok[j]:
            j += 1
        if need and j - k >= need:
            out.extend(range(k, j))
        k = j
    return out


def page_part(text: str, page_grams: set[tuple], margin: int = 40) -> tuple[str, bool, bool]:
    """The part of a long text that is on a page: from the first to the last word that starts a 3-word run found
    on the page, with a margin. Returns (text, cut, found)."""
    words = text.split()
    toks = [(i, t) for i, w in enumerate(words) for t in C.tokens(w)]
    ok = [tuple(t for _, t in toks[k:k + 3]) in page_grams for k in range(len(toks) - 2)]
    # three hits in a row = five words in a row on the page (one shared phrase like "see Table B2" is not enough);
    # a text shorter than five words needs all of its runs
    need = min(3, len(ok))
    hits = [toks[k][0] for k in _run_members(ok, need)]
    if not hits:
        return "", False, False
    if len(text) <= LONG_TEXT:
        return text, False, True
    a, b = max(0, hits[0] - margin), min(len(words), hits[-1] + 3 + margin)
    part = " ".join(words[a:b])
    return ("[...] " if a else "") + part + (" [...]" if b < len(words) else ""), bool(a or b < len(words)), True


def pdf_page_content(tree: dict, page: int, raw_page: dict | None, pages: list[set[int]] | None = None,
                     last_page: int | None = None) -> list[dict]:
    """What the tree holds for one PDF page, in tree order. A section that started on an earlier page is kept only
    when some of its words are on this page (three in a row), and a long one is cut to that part."""
    sections = tree.get("sections") or []
    pages = pages if pages is not None else C.section_pages(sections, last_page)
    grams = _grams([t for w in (raw_page or {}).get("words") or [] for t in C.tokens(w[0])])
    title = tree.get("title")
    last_flow = max((i for i, (s, ps) in enumerate(zip(sections, pages))
                     if page in ps and not s.get("spans") and C._int(s.get("file_page")) == page), default=None)
    out = []
    for i, (s, ps) in enumerate(zip(sections, pages)):
        if page not in ps:
            continue
        start = C._int(s.get("file_page"))
        spans = sorted(int(p) for p in (s.get("spans") or {}) if C._int(p))
        if s.get("type") == "table" and s.get("grid"):
            cells = " ".join(str(c) for row in s["grid"] for c in row if c)
            if not spans and start is not None and start < page and raw_page is not None \
                    and not page_part(cells, grams)[2]:
                continue  # a table with no page spans: on a later page only when its cells are there
            e = _entry(s, None, title)
            if len(spans) > 1:
                e["table_pages"] = spans
            out.append(e)
            continue
        own = set(spans) | {int(s[k]["page"]) for k in ("area", "image_bbox", "caption_box")
                            if isinstance(s.get(k), dict) and C._int(s[k].get("page"))}
        earlier = start is not None and start < page and page not in own
        if earlier and s.get("type") == "figure":
            continue  # a figure is on the page of its crop only
        if earlier:
            text, cut, found = page_part(s.get("text") or "", grams) if raw_page is not None else (s.get("text") or "", False, True)
            if not found:
                continue
            e = _entry(s, text, title)
            e["from_earlier_page"] = start
            if cut:
                e["text_cut"] = True
        else:
            e = _entry(s, None, title)
            if start is not None and start < page:
                e["from_earlier_page"] = start
        if i == last_flow or (len(spans) > 1 and page != spans[-1]):
            e["may_run_on"] = True
        out.append(e)
    return out


def pdf_strata(tree: dict) -> tuple[set[int], set[int]]:
    """(pages that hold a table section, pages that hold a figure section and no table)."""
    tables, figures = set(), set()
    for s in tree.get("sections") or []:
        if s.get("type") not in ("table", "figure"):
            continue
        ps = {int(p) for p in (s.get("spans") or {}) if C._int(p)}
        for k in ("area", "image_bbox"):
            if isinstance(s.get(k), dict) and C._int(s[k].get("page")):
                ps.add(int(s[k]["page"]))
        if not ps and C._int(s.get("file_page")):
            ps.add(int(s["file_page"]))
        (tables if s["type"] == "table" else figures).update(ps)
    return tables, figures - tables


# ---------------------------------------------------------------- web pages

def _block_text(bl: dict) -> tuple[str, list[tuple[str, str]]]:
    """(content text of a block, [(reason, dropped text)])."""
    keep = " ".join("".join(t for t, r in bl["parts"] if not r).split())
    dropped = [(r, " ".join(t.split())) for t, r in bl["parts"] if r and t.strip()]
    return keep, dropped


def html_parts(raw: dict, tree: dict, max_words: int = WEB_PART_WORDS) -> list[dict]:
    """A web page as parts: (raw blocks, tree sections) cut at headings found on both sides in the same order,
    grouped up to about max_words. A page with no shared headings, or a short one, is one part."""
    blocks, sections = raw.get("blocks") or [], tree.get("sections") or []
    titles = [tuple(C.tokens(s.get("title"))) if s.get("type") in ("chapter", "heading", "appendix") else () for s in sections]
    anchors, j = [(0, 0)], 0
    for i, bl in enumerate(blocks):
        if not re.fullmatch(r"h[1-6]", bl.get("tag") or ""):
            continue
        want = tuple(C.tokens(_block_text(bl)[0]))
        if not want:
            continue
        k = next((k for k in range(j, len(sections)) if titles[k] == want), None)
        if k is not None and i > 0 and k > 0:
            anchors.append((i, k))
            j = k + 1
    words = [len(_block_text(bl)[0].split()) for bl in blocks]
    cuts, size = [(0, 0)], 0
    for (i, k), (i2, _) in zip(anchors, anchors[1:] + [(len(blocks), len(sections))]):
        seg = sum(words[i:i2])
        if size and size + seg > max_words:
            cuts.append((i, k))
            size = 0
        size += seg
    table_at, at = [], 0  # the block where each table starts: the first cell block with the table's first cell text
    for t in raw.get("tables") or []:
        first = next((tuple(C.tokens(c)) for r in t.get("rows") or [] for c in r if C.tokens(c)), None)
        hit = next((b for b in range(at, len(blocks)) if blocks[b].get("tag") in ("td", "th")
                    and tuple(C.tokens(_block_text(blocks[b])[0])) == first), None)
        at = hit if hit is not None else at
        table_at.append(at)
    parts = []
    for n, ((i, k), (i2, k2)) in enumerate(zip(cuts, cuts[1:] + [(len(blocks), len(sections))]), start=1):
        src = []
        for bl in blocks[i:i2]:
            keep, dropped = _block_text(bl)
            for reason, text in dropped:
                if not src or not src[-1].startswith(f"[dropped: {reason}]") or len(src[-1]) > 300:
                    src.append(f"[dropped: {reason}] {text}"[:400])
                elif len(src[-1]) < 300:
                    src[-1] = (src[-1] + " / " + text)[:400]
            if keep:
                src.extend(lines(f"<{bl.get('tag')}> {keep}"))
        tabs = [t["rows"] for t, at in zip(raw.get("tables") or [], table_at) if not t.get("reason") and i <= at < i2]
        imgs = [im.get("alt") or "(no alt text)" for im in raw.get("images") or []
                if not im.get("reason") and im.get("block") is not None and i <= im["block"] < i2]
        parts.append({"part": n, "source": src, "source_tables": tabs, "source_images": imgs,
                      "content": [_entry(s, None, tree.get("title")) for s in sections[k:k2]]})
    for p in parts:
        p["of"] = len(parts)
    return parts


# ---------------------------------------------------------------- legislation

def leg_units(tree: dict) -> list[dict]:
    """Provisions: sections that are not a container (Part, Chapter, cross-heading, Schedule) and sit directly
    under one, or at the top."""
    by_id = {s["id"]: s for s in tree.get("sections") or []}
    return [s for s in tree.get("sections") or [] if s.get("type") not in LEG_CONTAINERS
            and (s.get("parent_id") is None or by_id.get(s["parent_id"], {}).get("type") in LEG_CONTAINERS)]


def leg_content(tree: dict, unit_id: str, limit: int = XML_LIMIT) -> list[dict]:
    """A provision and everything under it, in tree order; cut after about `limit` characters."""
    sections = tree.get("sections") or []
    under = {unit_id}
    out, size = [], 0
    for s in sections:  # tree order: a parent comes before its children
        if s["id"] == unit_id or s.get("parent_id") in under:
            under.add(s["id"])
            text = s.get("text") or ""
            if len(text) > limit:
                text = text[:limit] + "\n[cut]"
            if size > limit:
                out.append({"note": "[cut] more sections under this provision are not shown"})
                break
            out.append(_entry(s, text, tree.get("title")))
            size += len(text)
    return out


def xml_snippet(el, limit: int = XML_LIMIT) -> list[str]:
    """An XML element as text lines: namespace declarations taken out, long lines wrapped, cut at `limit`. A
    provision's title sits in the group around it (P1group), so that Title is put first."""
    from lxml import etree

    s = etree.tostring(el, encoding="unicode", with_tail=False)
    s = re.sub(r'\s+xmlns(:\w+)?="[^"]*"', "", s)
    s = re.sub(r">\s*<", ">\n<", s)
    if len(s) > limit:
        s = s[:limit] + "\n[cut]"
    parent = el.getparent()
    if parent is not None and isinstance(parent.tag, str) and parent.tag.endswith("}P1group"):
        t = next((c for c in parent if isinstance(c.tag, str) and c.tag.endswith("}Title")), None)
        if t is not None:
            s = f"<Title>{' '.join(''.join(t.itertext()).split())}</Title> (the heading over this provision)\n" + s
    return lines(s)


def xml_ids(path: Path) -> dict:
    from lxml import etree

    root = etree.parse(str(path), etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)).getroot()
    out: dict[str, list] = {}
    for e in root.iter():
        if isinstance(e.tag, str) and e.get("id"):
            out.setdefault(e.get("id"), []).append(e)
    return out


def pick_version(els: list, extent: str | None):
    """The element of a provision printed in several versions for different extents (HSWA s.43A for E+W+S and for
    N.I., both with the id "section-43A"): the one whose RestrictExtent is the tree's `applies_to`, else the first."""
    return next((e for e in els if extent and e.get("RestrictExtent") == extent), els[0])


# ---------------------------------------------------------------- the sample

def sample_pages(n_pages: int, tables: set[int], figures: set[int], rng: random.Random,
                 share: float = PDF_SHARE, least: int = PDF_MIN) -> dict[int, str]:
    """One document's pages: a random `share` (at least `least`, all when the document is shorter) as "base";
    every other table page as "table"; a random half of the other figure-only pages as "figure"."""
    all_pages = list(range(1, n_pages + 1))
    k = n_pages if n_pages <= least else max(least, round(share * n_pages))
    out = {p: "base" for p in sorted(rng.sample(all_pages, k))}
    for p in sorted(tables):
        if 1 <= p <= n_pages:
            out.setdefault(p, "table")
    rest = sorted(p for p in figures if 1 <= p <= n_pages and p not in out)
    for p in sorted(rng.sample(rest, len(rest) // 2)):
        out[p] = "figure"
    return out


def fit_cap(docs: dict[tuple, dict[int, str]], cap: int) -> dict[tuple, dict[int, str]]:
    """Base pages and table pages always stay. The extra figure pages stay only when the total fits the cap."""
    if sum(len(v) for v in docs.values()) > cap:
        for v in docs.values():
            for p in [p for p, s in v.items() if s == "figure"]:
                del v[p]
    return docs


def leg_allocation(counts: dict[str, int], target: int = LEG_TARGET, least: int = LEG_MIN) -> dict[str, int]:
    """Provisions to draw per law: in proportion to its size, at least `least` (all when it has fewer)."""
    total = sum(counts.values()) or 1
    return {k: min(n, max(least, round(target * n / total))) for k, n in counts.items()}


def in_scope_versions(source_ids: list[str] | None = None) -> list[tuple[dict, Path]]:
    return [v for v in C.versions_in_scope(source_ids) if (ROOT / v[0]["raw_path"]).exists()]


def draw_sample(today: str | None = None, cap: int = PDF_CAP, all_pages: tuple[str, ...] = ()) -> dict:
    """The sample, from the trees on this machine. Each document has its own random stream (seed, source, version),
    so adding a document does not move another document's pages. `all_pages`: parser families checked in full."""
    docs: dict[tuple, dict[int, str]] = {}
    fam: dict[tuple, str] = {}
    n_pages: dict[tuple, int] = {}
    web, leg_pop, counts = [], {}, Counter()
    for rec, tp in in_scope_versions():
        tree = json.loads(tp.read_text(encoding="utf-8"))
        key = (rec["source_id"], rec["version_id"])
        fam[key] = family(tree)
        if rec["media_type"] == C.PDF:
            n = n_pages[key] = len(C.raw_doc(rec)["pages"])
            counts["pdf_pages"] += n
            tables, figures = pdf_strata(tree)
            counts["pdf_table_pages"] += len(tables)
            counts["pdf_figure_only_pages"] += len(figures)
            docs[key] = sample_pages(n, tables, figures, random.Random(f"{SEED}|{key[0]}|{key[1]}"))
        elif rec["media_type"] == C.HTML:
            web.append(key)
        elif rec["media_type"] == C.XML:
            ids = xml_ids(ROOT / rec["raw_path"])
            units = [u["id"] for u in leg_units(tree)]
            counts["leg_provisions"] += len(units)
            counts["leg_provisions_without_xml_id"] += sum(1 for u in units if u not in ids)
            leg_pop[key] = [u for u in units if u in ids]
    before = Counter(s for v in docs.values() for s in v.values())
    docs = fit_cap(docs, cap)
    for key, v in docs.items():
        if fam[key] in all_pages:
            for p in range(1, n_pages[key] + 1):
                v.setdefault(p, "widened")
    alloc = leg_allocation({f"{k[0]}|{k[1]}": len(v) for k, v in leg_pop.items()})
    units: dict[str, dict] = defaultdict(dict)
    for key, v in sorted(docs.items()):
        units[key[0]][key[1]] = {"family": fam[key], "pdf_pages": {str(p): s for p, s in sorted(v.items())}}
    for key in sorted(web):
        units[key[0]][key[1]] = {"family": fam[key], "web": "all parts"}
    for key, pop in sorted(leg_pop.items()):
        rng = random.Random(f"{SEED}|{key[0]}|{key[1]}")
        units[key[0]][key[1]] = {"family": fam[key], "provisions": sorted(rng.sample(pop, alloc[f"{key[0]}|{key[1]}"]))}
    after = Counter(s for v in docs.values() for s in v.values())
    return {
        "about": "The sample for the semantic check (system/rag/semcheck.py). Drawn once; do not edit by hand.",
        "seed": SEED, "date": today or datetime.date.today().isoformat(),
        "rule": {
            "pdf": f"Per document: a random {PDF_SHARE:.0%} of its pages, at least {PDF_MIN} (all when shorter) = base. "
                   "Then every other page with a table section (table) and a random half of the other pages with "
                   f"figures only (figure), but the figure pages only when the total stays within {cap} pages. "
                   "Base and table pages always stay.",
            "web": "Every web page in scope, every part.",
            "legislation": f"About {LEG_TARGET} provisions over all laws in scope, in proportion to each law's "
                           f"provisions, at least {LEG_MIN} per law. A provision is a section directly under a Part, "
                           "Chapter, cross-heading or Schedule (or at the top) whose id is an element id in the XML.",
            "all_pages": sorted(all_pages),
        },
        "population": dict(counts),
        "drawn": {"pdf_before_cap": dict(before), "pdf": dict(after), "pdf_documents": len(docs), "web_pages": len(web),
                  "provisions": sum(len(v["provisions"]) for s in units.values() for v in s.values() if "provisions" in v),
                  "laws": len(leg_pop)},
        "units": units,
    }


# ---------------------------------------------------------------- packets

def _page_image(source_id: str, rec: dict, page: int, renderers: dict) -> Path:
    """The rendered page, kept on disk under the raw file's hash (rendered once)."""
    out = CORPUS_DIR / "parsed" / source_id / "semcheck" / "pages" / f"{rec['sha256'][:16]}-p{page}.png"
    if not out.exists():
        from system.rag.cropcheck import _page_renderer

        if rec["sha256"] not in renderers:
            renderers[rec["sha256"]] = _page_renderer(ROOT / rec["raw_path"], SCALE)
        out.parent.mkdir(parents=True, exist_ok=True)
        renderers[rec["sha256"]][0](page).convert("RGB").save(out)
    return out


def _packet(kind: str, rec: dict, tree: dict, unit: str, key: str, stratum: str, body: dict, images: list[str]) -> dict:
    return {"source_id": rec["source_id"], "version_id": rec["version_id"], "key": key, "kind": f"semcheck-{kind}",
            "unit": unit, "family": family(tree), "stratum": stratum, "title": tree.get("title") or "",
            "instructions": INSTRUCTIONS[kind].split("\n"),
            "answer_format": {"key": key, "kind": f"semcheck-{kind}", **ANSWER_FORMAT}, "images": images, **body}


def unit_packets(rec: dict, tree: dict, chosen: dict) -> list[dict]:
    """Packets for one version's sampled units, each with the key that names its source side and tree content."""
    renderers: dict = {}
    sid, out = rec["source_id"], []
    if "pdf_pages" in chosen:
        raw = C.raw_doc(rec)
        sections = tree.get("sections") or []
        pages = C.section_pages(sections, len(raw["pages"]))
        for p, stratum in sorted(((int(p), s) for p, s in chosen["pdf_pages"].items())):
            if p > len(raw["pages"]):
                continue
            content = pdf_page_content(tree, p, raw["pages"][p - 1], pages)
            img = _page_image(sid, rec, p, renderers)
            key = _sha(img.read_bytes(), _canon(content))
            out.append(_packet("pdf", rec, tree, f"p{p}", key, stratum, {"page": p, "content": content},
                               [img.relative_to(ROOT).as_posix()]))
    elif "web" in chosen:
        for part in html_parts(C.raw_doc(rec), tree):
            body = {k: part[k] for k in ("part", "of", "source", "source_tables", "source_images", "content")}
            key = _sha(_canon([part["source"], part["source_tables"], part["source_images"]]), _canon(part["content"]))
            out.append(_packet("html", rec, tree, f"part{part['part']}", key, "all", body, []))
    elif "provisions" in chosen:
        ids = xml_ids(ROOT / rec["raw_path"])
        for uid in chosen["provisions"]:
            if uid not in ids:
                continue
            content = leg_content(tree, uid)
            src = xml_snippet(pick_version(ids[uid], (content[0] if content else {}).get("applies_to")))
            out.append(_packet("xml", rec, tree, uid, _sha(_canon(src), _canon(content)), "sample",
                               {"source_xml": src, "content": content}, []))
    for r in renderers.values():
        r[1].close()
    return out


def sampled_packets(source_ids: list[str] | None = None, sample: dict | None = None):
    """(record, tree, packet) for every sampled unit of the versions on this machine."""
    sample = sample if sample is not None else load_sample()
    units = sample.get("units") or {}
    for rec, tp in in_scope_versions(source_ids):
        chosen = (units.get(rec["source_id"]) or {}).get(rec["version_id"])
        if not chosen:
            continue
        tree = json.loads(tp.read_text(encoding="utf-8"))
        for pk in unit_packets(rec, tree, chosen):
            yield rec, tree, pk


def export(source_ids: list[str] | None = None, all_: bool = False) -> int:
    if not load_sample():
        print("no sample: run `python -m system.rag.semcheck sample` first")
        return 1
    n = skipped = 0
    cleared, done = set(), {}
    for rec, _tree, pk in sampled_packets(source_ids):
        sid = rec["source_id"]
        out = CORPUS_DIR / "parsed" / sid / "semcheck"
        if sid not in cleared:
            out.mkdir(parents=True, exist_ok=True)
            for old in out.glob("*.json"):
                old.unlink()
            cleared.add(sid)
            done[sid] = load_verdicts(sid)["verdicts"]
        if pk["key"] in done[sid] and not all_:
            skipped += 1
            continue
        n += 1
        name = f"{pk['kind'].split('-')[1]}-{pk['version_id'][-8:]}-{pk['unit'][:40].replace('/', '_')}-{pk['key']}.json"
        (out / name).write_text(dump_packet(pk), encoding="utf-8")
    print(f"{n} packets -> corpus/parsed/<source>/semcheck/ ({skipped} units already judged)")
    return 0


# ---------------------------------------------------------------- run (headless Claude Code)

def packet_files(source_ids: list[str] | None = None) -> list[Path]:
    base = CORPUS_DIR / "parsed"
    ids = source_ids or sorted(p.name for p in base.iterdir() if (p / "semcheck").is_dir())
    return [f for sid in ids for f in sorted((base / sid / "semcheck").glob("*.json"))]


def batches(files: list[Path], size: int = BATCH) -> list[list[Path]]:
    return [files[i:i + size] for i in range(0, len(files), size)]


def run(source_ids: list[str] | None = None, parallel: int = 4, model: str = MODEL, out_dir: Path | None = None,
        timeout: int = 1500, by: str | None = None) -> int:
    """Run the open packets through headless Claude Code, `parallel` batches at a time. Answers go to out_dir
    (one .jsonl per batch). With `by`, each batch's answers are saved as soon as it ends, so a run that is cut
    off loses nothing. A batch that fails or times out leaves no file: `export` and run again."""
    out_dir = out_dir or CORPUS_DIR / "parsed" / "_semcheck" / datetime.datetime.now().strftime("run-%Y%m%d-%H%M%S")
    out_dir = (out_dir if out_dir.is_absolute() else ROOT / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    # Only packets with no verdict yet: a folder left from an earlier export (another --source) is not judged again.
    files = [f for f in packet_files(source_ids)
             if (pk := json.loads(f.read_text(encoding="utf-8")))["key"] not in load_verdicts(pk["source_id"])["verdicts"]]
    todo = batches(files)

    lock = threading.Lock()
    failed = [0]  # batches in a row that left no answers: after 8 the run stops (the plan's usage limit is spent)

    def one(arg):
        n, files = arg
        if failed[0] >= 8:
            return False
        ans = out_dir / f"batch_{n:04d}.jsonl"
        prompt = PROMPT.format(root=ROOT, answers=ans.relative_to(ROOT).as_posix(),
                               packets="\n".join(f"- `{f.relative_to(ROOT).as_posix()}`" for f in files))
        try:
            subprocess.run(["claude", "-p", prompt, "--model", model, "--allowedTools", "Read,Write"], check=False,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        except subprocess.TimeoutExpired:
            pass
        failed[0] = 0 if ans.exists() else failed[0] + 1
        if ans.exists() and by:
            with lock:
                save(ans, by, quiet=True)
        return ans.exists()

    with ThreadPoolExecutor(max_workers=parallel) as ex:
        ok = sum(ex.map(one, enumerate(todo, start=1)))
    print(f"{len(todo)} batches, {ok} with answers -> {out_dir.relative_to(ROOT)}")
    return 0 if ok == len(todo) else 1


# ---------------------------------------------------------------- save

def check_answer(a: dict) -> str | None:
    """Why an answer is refused, or None."""
    if a.get("verdict") not in VERDICTS:
        return f"unknown verdict {a.get('verdict')!r}"
    fs = a.get("findings")
    if fs is None:
        fs = []
    if not isinstance(fs, list):
        return "findings must be a list"
    if a["verdict"] == "ok":
        return "verdict ok with findings" if fs else None
    if not fs:
        return "a verdict other than ok needs at least one finding"
    for f in fs:
        if not isinstance(f, dict) or f.get("kind") not in KINDS:
            return f"finding with unknown kind {f.get('kind') if isinstance(f, dict) else f!r}"
        if f.get("severity") not in SEVERITIES:
            return "finding without severity high or low"
        if not str(f.get("problem") or "").strip() or not str(f.get("evidence") or "").strip():
            return "finding without problem or evidence"
    if a["verdict"] not in {f["kind"] for f in fs}:
        return "verdict is not the kind of one of its findings"
    return None


def save(answers: Path, by: str, source_ids: list[str] | None = None, today: str | None = None,
         quiet: bool = False) -> int:
    """Check each answer against its packet and the rules; save the good ones per source, report the rest."""
    packets = {}
    for f in packet_files(source_ids):
        pk = json.loads(f.read_text(encoding="utf-8"))
        packets[pk["key"]] = pk
    files = sorted(answers.glob("*.jsonl")) if answers.is_dir() else [answers]
    today = today or datetime.date.today().isoformat()
    docs: dict[str, dict] = {}
    saved = rejected = 0
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                a = json.loads(line)
            except json.JSONDecodeError:
                a = {}
            pk = packets.get(a.get("key")) if isinstance(a, dict) else None
            why = "unknown key or not JSON" if not pk else ("kind differs from the packet" if a.get("kind") != pk["kind"]
                                                           else check_answer(a))
            if why:
                print(f"{f.name} line {n}: {why}")
                rejected += 1
                continue
            sid = pk["source_id"]
            doc = docs.setdefault(sid, load_verdicts(sid))
            doc["verdicts"][a["key"]] = {
                "version_id": pk["version_id"], "unit": pk["unit"], "kind": pk["kind"], "family": pk["family"],
                "verdict": a["verdict"],
                "findings": [{"kind": x["kind"], "severity": x["severity"], "problem": str(x["problem"]).strip(),
                              "evidence": str(x["evidence"]).strip()} for x in a.get("findings") or []],
                "confidence": a.get("confidence") if a.get("confidence") in ("high", "medium", "low") else "medium",
                "by": by, "date": today}
            saved += 1
    for sid, doc in docs.items():
        p = verdicts_path(sid)
        p.parent.mkdir(parents=True, exist_ok=True)
        doc["verdicts"] = dict(sorted(doc["verdicts"].items(), key=lambda kv: (kv[1]["version_id"], kv[1]["unit"], kv[0])))
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not quiet:
        print(f"saved {saved}, rejected {rejected} -> corpus/semchecks/ ({len(docs)} sources)")
    return 1 if rejected else 0


def accept(source_id: str, key: str, as_: str, reason: str, by: str, finding: int | None = None,
           today: str | None = None) -> int:
    """Settle findings of one verdict after looking at the source: the model was wrong, or the difference is real
    and kept on purpose. `finding` is the finding's place (from 1); none means all of them."""
    doc = load_verdicts(source_id)
    v = doc["verdicts"].get(key)
    if as_ not in ACCEPT_AS or not reason.strip():
        print("accept needs --as model-wrong or kept, and a reason")
        return 1
    if not v or not v.get("findings"):
        print(f"no findings saved under {key}")
        return 1
    which = range(len(v["findings"])) if finding is None else [finding - 1]
    if any(not 0 <= i < len(v["findings"]) for i in which):
        print(f"{key} has {len(v['findings'])} findings")
        return 1
    for i in which:
        v["findings"][i]["settled"] = {"as": as_, "reason": reason, "by": by,
                                       "date": today or datetime.date.today().isoformat()}
    verdicts_path(source_id).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"settled {len(list(which))} finding(s) of {key} as {as_}")
    return 0


# ---------------------------------------------------------------- report

def open_findings(v: dict) -> list[dict]:
    return [f for f in v.get("findings") or [] if not f.get("settled")]


def real_findings(v: dict) -> list[dict]:
    """Findings not shown to be the model's mistake: open ones and those kept on purpose."""
    return [f for f in v.get("findings") or [] if (f.get("settled") or {}).get("as") != "model-wrong"]


def status(source_ids: list[str] | None = None, sample: dict | None = None) -> list[dict]:
    """One row per sampled unit on this machine: its key, stratum and the saved verdict for that key (or None)."""
    rows, cache = [], {}
    for rec, _tree, pk in sampled_packets(source_ids, sample):
        sid = rec["source_id"]
        if sid not in cache:
            cache[sid] = load_verdicts(sid)["verdicts"]
        rows.append({"source_id": sid, "version_id": rec["version_id"], "unit": pk["unit"], "key": pk["key"],
                     "kind": pk["kind"], "family": pk["family"], "stratum": pk["stratum"],
                     "verdict": cache[sid].get(pk["key"])})
    return rows


def summarise(rows: list[dict]) -> dict:
    """Counts for a set of units. `high` counts units with a high-severity finding that is not the model's mistake."""
    judged = [r for r in rows if r["verdict"]]
    real = [(r, real_findings(r["verdict"])) for r in judged]
    high = sum(1 for _, fs in real if any(f["severity"] == "high" for f in fs))
    low = sum(1 for _, fs in real if fs and not any(f["severity"] == "high" for f in fs))
    lo, hi = wilson(high, len(judged))
    return {"units": len(rows), "judged": len(judged), "not_judged": len(rows) - len(judged),
            "ok": sum(1 for _, fs in real if not fs), "high": high, "low_only": low,
            "open": sum(1 for r in judged if open_findings(r["verdict"])),
            "open_high": sum(1 for r in judged if any(f["severity"] == "high" for f in open_findings(r["verdict"]))),
            "model_wrong": sum(1 for r in judged for f in r["verdict"].get("findings") or []
                               if (f.get("settled") or {}).get("as") == "model-wrong"),
            "kept": sum(1 for r in judged for f in r["verdict"].get("findings") or []
                        if (f.get("settled") or {}).get("as") == "kept"),
            "findings": dict(Counter(f"{f['kind']}/{f['severity']}" for _, fs in real for f in fs)),
            "high_rate": high / len(judged) if judged else 0.0, "high_low": lo, "high_high": hi}


def _line(name: str, s: dict) -> str:
    return (f"{name}: {s['units']} units, {s['judged']} judged, {s['not_judged']} not judged; ok {s['ok']}, "
            f"low only {s['low_only']}, high {s['high']} = {s['high_rate']:.1%} (95% {s['high_low']:.1%} to "
            f"{s['high_high']:.1%}); open {s['open']} ({s['open_high']} high); findings settled: model wrong "
            f"{s['model_wrong']}, kept {s['kept']}")


def report(source_ids: list[str] | None = None, verbose: bool = False, json_out: Path | None = None) -> int:
    rows = status(source_ids)
    by_family = defaultdict(list)
    for r in rows:
        by_family[r["family"]].append(r)
    for fam in sorted(by_family):
        rs = by_family[fam]
        print(_line(fam, summarise(rs)))
        strata = sorted({r["stratum"] for r in rs})
        if len(strata) > 1:
            for st in strata:
                print("   " + _line(f"stratum {st}", summarise([r for r in rs if r["stratum"] == st])))
        s = summarise(rs)
        if s["findings"]:
            print("   findings: " + ", ".join(f"{k} {v}" for k, v in sorted(s["findings"].items())))
    total = summarise(rows)
    print(_line("TOTAL", total))
    if verbose:
        for r in rows:
            for i, f in enumerate((r["verdict"] or {}).get("findings") or [], start=1):
                if not f.get("settled"):
                    print(f"   {r['source_id']} {r['version_id'][:36]} {r['unit']} {r['key']}#{i} {f['kind']}/"
                          f"{f['severity']}: {f['problem']} [{f['evidence'][:160]}]")
    if json_out:
        json_out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if total["open"] or total["not_judged"] else 0


# ---------------------------------------------------------------- command line

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sm = sub.add_parser("sample", help="draw the sample (fixed seed) and write corpus/semchecks/sample.json")
    sm.add_argument("--cap", type=int, default=PDF_CAP)
    sm.add_argument("--all-pages", nargs="*", default=[], help="parser families checked on every page")
    e = sub.add_parser("export")
    e.add_argument("--source", nargs="*")
    e.add_argument("--all", action="store_true", help="also units already judged")
    r = sub.add_parser("run", help="run the packets with headless Claude Code")
    r.add_argument("--source", nargs="*")
    r.add_argument("--parallel", type=int, default=4)
    r.add_argument("--out", type=Path)
    r.add_argument("--by", help="save each batch's answers as it ends, under this name")
    s = sub.add_parser("save")
    s.add_argument("--answers", required=True, type=Path, help="a .jsonl file or a folder of them")
    s.add_argument("--by", required=True)
    s.add_argument("--source", nargs="*")
    c = sub.add_parser("accept", help="settle findings after looking at the source")
    c.add_argument("--source", required=True)
    c.add_argument("--key", required=True)
    c.add_argument("--as", dest="as_", required=True, choices=ACCEPT_AS)
    c.add_argument("--finding", type=int)
    c.add_argument("--reason", required=True)
    c.add_argument("--by", required=True)
    p = sub.add_parser("report")
    p.add_argument("--source", nargs="*")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "sample":
        doc = draw_sample(cap=a.cap, all_pages=tuple(a.all_pages))
        sample_path().parent.mkdir(parents=True, exist_ok=True)
        sample_path().write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"population": doc["population"], "drawn": doc["drawn"]}, indent=1))
        return 0
    if a.cmd == "export":
        return export(a.source, all_=a.all)
    if a.cmd == "run":
        return run(a.source, parallel=a.parallel, out_dir=a.out, by=a.by)
    if a.cmd == "save":
        return save(a.answers, a.by, a.source)
    if a.cmd == "accept":
        return accept(a.source, a.key, a.as_, a.reason, a.by, a.finding)
    return report(a.source, verbose=a.verbose, json_out=a.json)


if __name__ == "__main__":
    sys.exit(main())
