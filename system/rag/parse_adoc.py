"""Parse an Approved Document PDF (AD B first) into a document tree.

    python -m system.rag.parse_adoc --source adb --part approved-document-b-fire-safety-volume-1-dwellings

Design: architecture/design/regulations-corpus.md, ADR 0010. Same tree format as parse_pdf (HSE guides), so
the model-check step (system/rag/checks.py), saved fixes and image cutting are shared. The layout of the
2019-style Approved Documents is regular, so most decisions come from fonts, sizes and colours:

- page furniture: the "ONLINE VERSION" watermark, the coloured section tab, the footer (printed page number);
- edition banners at the top of a page ("Effective until 1 September 2029", "2029 amendment - effective from
  2 September 2029") date every section that starts on those pages; the two copies of an appendix get their
  own ids (suffix -until-YYYY-MM-DD / -from-YYYY-MM-DD) and valid_from / valid_to;
- chapters: 26pt bold titles (Section N, Requirement B1, Regulation 38, Appendix A, Introduction ...);
- headings: 20pt bold (level 1), 15pt bold (level 2), all-bold 12pt lines (level 3);
- numbered paragraphs: a line whose first word is a semibold number (2.18, B5, C1);
- definitions: Appendix A key terms, a semibold term followed by its meaning (two columns);
- diagrams: white caption text on a green band ("Diagram 2.2 ..."); the small text above it, back to the
  last body line, is the diagram's labels; the area is cut as an image for the model check;
- tables: a bold "Table N.N" caption; small text below it until the next body line; "Table N.N Continued"
  carries on; PDF grids from pdfplumber are attached as a hint for the model check;
- requirement boxes: the small-print legal text under Requirement and Regulation chapters;
- marked terms: green words in body text (the document's links to its key terms);
- two-column pages (key terms, standards, documents referred to) are read left column first;
- line text is rebuilt from the PDF's words: AD PDFs have no space characters, and pdfplumber's own line
  text splits some words ("T he"); the word splitter does not.

Contents, index and the cover are skipped.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import Counter, defaultdict

from system.rag.corpus import CORPUS_DIR, slugify
from system.rag.fixes import content_key, index, load_fixes
from system.rag.parse_pdf import read_pdf, render_images

PARSER = "approved-document-pdf/0.1"
BODY = 12.0
SMALL = 10.6  # below this: diagram labels, table text, requirement boxes (some list items are 11pt)
RARE_AFTER_F = set("bcdgjkmnpqsvwxz")  # letters that almost never follow "f" in English words
NUM_RE = re.compile(r"^(\d{1,2}\.\d{1,3}|[A-G]\d{1,3})$")
LIST_RE = re.compile(r"^(?:[a-z]|[ivx]{1,4})\.\s|^•\s|^\(\w{1,4}\)\s")
TABLE_RE = re.compile(r"^Table ([A-Z]?\d+(?:\.\d+)?)\b\s*(.*)$")
DIAGRAM_RE = re.compile(r"^Diagram ([A-Z]?\d+(?:\.\d+)?|[ivx]{1,4})\b\s*(.*)$")
BANNER_RE = re.compile(r"(?i)(effective until|effective from) (\d{1,2} \w+ \d{4})")
SKIP_CHAPTERS = {"contents"}
STOP_CHAPTERS = {"index", "list of approved documents"}


def _date(text: str) -> str:
    return datetime.datetime.strptime(text, "%d %B %Y").date().isoformat()


def _white(w) -> bool:
    return w.get("c") in ([1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0])


def _green(w) -> bool:
    c = w.get("c")
    return bool(c) and len(c) == 3 and c[1] > 0.3 and c[0] < 0.2 and c[2] < 0.5


def _bold(w) -> bool:
    return bool(w.get("b"))


def _text(words) -> str:
    return " ".join(w["text"] for w in words)


def _line(words, src) -> dict:
    return {**src, "words": words, "text": _text(words), "x0": words[0]["x0"] if words else src["x0"]}


class AdocBuilder:
    def __init__(self, doc: dict, meta: dict, fixes: list[dict] | None = None):
        self.meta = meta
        self.fixes = index(fixes)
        self.title = meta.get("title") or meta.get("source_id", "")
        self.page_width = doc.get("page_width") or 595.0
        self.doc_tables = doc.get("tables", [])
        self.sections: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self.issues: list[str] = []
        self.checks: list[dict] = []
        self.definitions: list[dict] = []
        self.printed: dict[int, str] = {}
        self.banner: dict[int, tuple[str, str]] = {}
        self.pages: dict[int, list[dict]] = defaultdict(list)
        self._diagram_top: dict[tuple[int, int], float] = {}
        self._furniture(doc["lines"])

    # -------------------------------------------------- pages

    def _furniture(self, lines) -> None:
        for l in sorted(lines, key=lambda l: (l["page"], l["top"], l["x0"])):
            t = l["text"].strip()
            if l["top"] < 82:
                m = BANNER_RE.search(t)
                if m:
                    self.banner[l["page"]] = ("until" if "until" in m.group(1).lower() else "from", _date(m.group(2)))
                continue
            if l["top"] >= 795:
                if re.fullmatch(r"[0-9]{1,3}|[ivxlc]{1,6}", t) and l["size"] >= 13:
                    self.printed[l["page"]] = t
                continue
            if "O N L I N E" in t:
                continue
            self.pages[l["page"]].append(_line(l["words"], l) if l.get("words") else l)
        self._ligatures()
        for p in self.pages:
            self.pages[p] = self._columns(p, self._scripts(self.pages[p]))

    def _scripts(self, lines: list[dict]) -> list[dict]:
        """Put small sub- and superscripts (B ROOF, footnote marks) back into the text line they belong to."""
        body = [l for l in lines if l["size"] >= 9.5 and l.get("words")]
        kept = []
        for l in lines:
            ws = l.get("words") or []
            if l["size"] <= 8.5 and ws and all(len(w["text"]) <= 6 for w in ws):
                places = []
                for w in ws:
                    host = next((b for b in body if abs(b["top"] - l["top"]) <= 9 and b["size"] > l["size"] + 1.5
                                 and b["words"][0]["x0"] - 2 <= w["x0"] <= b["words"][-1]["x1"] + 4), None)
                    before = [x for x in host["words"] if x["x0"] < w["x0"]] if host else []
                    if not before:
                        break
                    places.append((host, before[-1], w))
                if len(places) == len(ws):
                    for host, word, w in places:
                        word["text"] += w["text"]
                        host["text"] = _text(host["words"])
                    continue
            kept.append(l)
        return kept

    def _ligatures(self) -> None:
        """Some words lose letters of an "fi" or "fl" pair in these PDFs ("fre", "foor", "specifed", "Ofces"), show
        "ff" as a degree sign ("E°ective"), or split a capital from its word ("M easurement"). Put them back when
        the repaired word is more common in the same document than the broken one (and used at least 3 times). Every repair is counted."""
        vocab = Counter(re.sub(r"[^a-z]", "", w["text"].lower()) for ls in self.pages.values() for l in ls
                        for w in l.get("words") or [])
        fixes: dict[str, str] = {}
        for word, n in vocab.items():
            if len(word) < 3:
                continue
            best = None
            cands = [word[:i] + x + word[i:] for i in range(1, len(word) + 1) if word[i - 1] == "f" for x in ("i", "l")]
            cands += [word[:i] + x + word[i:] for i in range(len(word) + 1) for x in ("fi", "fl")]
            for cand in cands:
                if vocab.get(cand, 0) >= 3 and n < vocab[cand] and (best is None or vocab[cand] > vocab[best]):
                    best = cand
            if not best:
                # "f" followed by a letter that almost never follows it in English ("defnition", "roofng"): the
                # broken form may be the more common one (the index repeats it), so a single correct use is enough.
                for i in range(len(word) - 1):
                    if word[i] == "f" and word[i + 1] in RARE_AFTER_F:
                        for x in ("i", "l"):
                            cand = word[:i + 1] + x + word[i + 1:]
                            if vocab.get(cand, 0) >= 1 and (best is None or vocab[cand] > vocab[best]):
                                best = cand
            if best:
                fixes[word] = best
        self.repairs: Counter = Counter()
        for ls in self.pages.values():
            for l in ls:
                changed = False
                ws = l.get("words") or []
                for w in ws:  # "ff" printed as a degree sign: "E°ective"
                    if re.search(r"[A-Za-z]°[a-z]", w["text"]):
                        opts = [re.sub(r"(?<=[A-Za-z])°(?=[a-z])", x, w["text"]) for x in ("ff", "ffi", "ffl")]
                        good = max(opts, key=lambda o: vocab.get(re.sub(r"[^a-z]", "", o.lower()), 0))
                        self.repairs[f"{w['text']} -> {good}"] += 1
                        w["text"], changed = good, True
                k = 0
                while k < len(ws) - 1:  # "M easurement": a capital split from the rest of its word
                    a, b = ws[k]["text"], ws[k + 1]["text"]
                    rest = re.sub(r"[^a-z]", "", b.lower())
                    if re.fullmatch(r"[A-Z]", a) and re.match(r"^[a-z]{2,}", b) and vocab.get(rest, 0) == 0 \
                            and vocab.get((a + re.match(r"^[a-z]+", b).group(0)).lower(), 0) >= 1:
                        self.repairs[f"{a} {b} -> {a}{b}"] += 1
                        ws[k] = {**ws[k], "text": a + b, "x1": ws[k + 1]["x1"]}
                        del ws[k + 1]
                        changed = True
                    k += 1
                for w in ws:
                    m = re.match(r"^([^A-Za-z]*)([A-Za-z]+)([^A-Za-z]*)$", w["text"])
                    if m and m.group(2).lower() in fixes:
                        good = fixes[m.group(2).lower()]
                        while good in fixes and fixes[good] != good:  # two pairs broken in one word
                            good = fixes[good]
                        good = good.capitalize() if m.group(2)[0].isupper() else good
                        self.repairs[f"{m.group(2)} -> {good}"] += 1
                        w["text"] = m.group(1) + good + m.group(3)
                        changed = True
                if changed:
                    l["text"] = _text(l["words"])

    def _columns(self, page: int, lines: list[dict]) -> list[dict]:
        """Two-column pages: split body-size lines at the gutter and read the left column first."""
        gutters = Counter()
        for l in lines:
            if l["size"] < SMALL:
                continue
            ws = l.get("words") or []
            if ws and 280 <= ws[0]["x0"] <= 345:
                gutters[round(ws[0]["x0"])] += 1
            for a, b in zip(ws, ws[1:]):
                if b["x0"] - a["x1"] > 10 and 280 <= b["x0"] <= 345:
                    gutters[round(b["x0"])] += 1
        if sum(gutters.values()) < 6:
            return lines
        g = min(x for x, c in gutters.items() if c >= 2)  # the right column can have two indents: use the outer one
        left, right = [], []
        for l in lines:
            ws = l.get("words") or []
            if l["size"] < SMALL or l["size"] > 21 or not ws:  # small print and chapter titles are not split
                left.append(l)
                continue
            lw = [w for w in ws if w["x0"] < g - 4]
            rw = [w for w in ws if w["x0"] >= g - 4]
            if lw:
                left.append(_line(lw, l))
            if rw:
                right.append(_line(rw, {**l, "x0": rw[0]["x0"]}))
        return sorted(left, key=lambda l: l["top"]) + sorted(right, key=lambda l: l["top"])

    def page_label(self, page: int) -> str:
        return self.printed.get(page, str(page))

    # -------------------------------------------------- sections

    def add(self, sid, kind, parent, number, title, page, text="") -> dict:
        path = [*(parent["heading_path"] if parent else [self.title]), title or kind.title()]
        sec = {"id": sid, "parent_id": parent["id"] if parent else None, "type": kind, "number": number,
               "title": title, "heading_path": path, "text": text, "printed_page": self.page_label(page),
               "file_page": page, "applies_to": None, "footnotes": []}
        chap = self.chapter
        if chap and chap.get("valid_to"):
            sec["valid_to"] = chap["valid_to"]
        if chap and chap.get("valid_from"):
            sec["valid_from"] = chap["valid_from"]
        if sid in self.by_id:
            self.issues.append(f"duplicate section id {sid} (file page {page})")
            sid = sec["id"] = f"{sid}-p{page}"
        self.sections.append(sec)
        self.by_id[sid] = sec
        return sec

    def suffix(self) -> str:
        chap = self.chapter
        if chap and chap.get("valid_to"):
            return f"-until-{chap['valid_to']}"
        if chap and chap.get("valid_from"):
            return f"-from-{chap['valid_from']}"
        return ""

    @staticmethod
    def span(sec, page, top, bottom) -> None:
        sp = sec.setdefault("spans", {})
        a, b = sp.get(str(page), (top, bottom))
        sp[str(page)] = (min(a, top), max(b, bottom))

    # -------------------------------------------------- regions on a page

    def regions(self, page: int, lines: list[dict]) -> dict[int, tuple[str, int]]:
        """Which lines belong to a diagram, a table or a small-print box. Returns {line index: (kind, n)},
        where n numbers the region on the page."""
        out: dict[int, tuple[str, int]] = {}
        n = 0
        # Diagrams: white caption, then labels back to the last body-size line above.
        i = 0
        while i < len(lines):
            l = lines[i]
            ws = l.get("words") or []
            if ws and _white(ws[0]) and DIAGRAM_RE.match(l["text"]):
                n += 1
                j = i + 1
                while j < len(lines) and (lines[j].get("words") or [{}])[0] and _white(lines[j]["words"][0]) \
                        and lines[j]["top"] - lines[j - 1]["top"] < 18:
                    j += 1
                for k in range(i, j):
                    out[k] = ("caption", n)
                top_limit = max([m["top"] for k, m in enumerate(lines[:i]) if m["top"] < l["top"]
                                 and (m["size"] >= SMALL and "Medium" not in m["font"] and k not in out
                                      or out.get(k, ("",))[0] == "caption")],
                                default=0.0)
                for k, m in enumerate(lines):
                    if k not in out and top_limit < m["top"] < l["top"] and (m["size"] < SMALL or "Medium" in m["font"]):
                        out[k] = ("diagram", n)
                self._diagram_top[(page, n)] = top_limit
                i = j
                continue
            i += 1
        # Tables: bold caption, then small text until the next body-size line.
        for i, l in enumerate(lines):
            if i in out:
                continue
            ws = l.get("words") or []
            if TABLE_RE.match(l["text"]) and ws and _bold(ws[0]) and l["size"] >= 11.5:
                n += 1
                out[i] = ("table-caption", n)
                last = l
                for k in range(i + 1, len(lines)):
                    m = lines[k]
                    if k in out or m["top"] < l["top"]:
                        continue
                    mw = m.get("words") or []
                    if last is not None and mw and all(_bold(w) for w in mw) and abs(m["size"] - l["size"]) < 0.6 \
                            and 0 < m["top"] - last["top"] < 17 and not TABLE_RE.match(m["text"]):
                        out[k] = ("table-caption-more", n)
                        last = m
                        continue
                    last = None
                    if m["size"] >= SMALL and "Medium" not in m["font"]:
                        break
                    out[k] = ("table", n)
        # Small print outside diagrams and tables: requirement boxes and similar.
        prev = None
        for i, l in enumerate(lines):
            if i in out or l["size"] >= SMALL:
                prev = None
                continue
            if prev is None:
                n += 1
            out[i] = ("small", n)
            prev = i
        return out

    # -------------------------------------------------- build

    def build(self) -> dict:
        self.chapter = None
        root = None
        h1 = h2 = h3 = None
        current = None  # the section running text goes to
        skipping = True  # cover
        tables: dict[str, dict] = {}
        last_table = None
        for page in sorted(self.pages):
            lines = self.pages[page]
            reg = self.regions(page, lines)
            region_secs: dict[int, dict] = {}
            tiny = [l for k, l in enumerate(lines) if reg.get(k, ("",))[0] == "small" and l["size"] < 9.0]
            if len(tiny) >= 10:
                # A picture of a page made of text (AD B page 8, the "how to use" sample page): if it has a diagram
                # caption, everything else on the page is that diagram's labels; if not, skip the page.
                caps = [v for v in reg.values() if v[0] == "caption"]
                if not caps:
                    self.issues.append(f"file page {page}: picture made of text with no caption, {len(lines)} lines skipped")
                    continue
                reg = {k: (reg[k] if reg.get(k, ("",))[0] == "caption" else ("diagram", caps[0][1]))
                       for k in range(len(lines))}
                self._diagram_top[(page, caps[0][1])] = 0.0  # the picture fills the page
            for i, l in enumerate(lines):
                ws = l.get("words") or []
                t = l["text"].strip()
                if not t:
                    continue
                kind, n = reg.get(i, (None, None))
                # Chapters
                if kind is None and 25 <= l["size"] <= 27.5 and ws and _bold(ws[0]) and l["top"] < 200:
                    if self.chapter and self.chapter["file_page"] == page and current is self.chapter \
                            and not self.chapter["text"] and l["top"] - self.chapter.get("_top", 0) < 40:
                        self.chapter["title"] = (f"{self.chapter['title']} {t}")
                        self.chapter["heading_path"][-1] = self.chapter["title"]
                        self.chapter["_top"] = l["top"]
                        continue
                    title = (t)
                    low = title.lower()
                    if low in STOP_CHAPTERS:
                        return self.finish()
                    skipping = low in SKIP_CHAPTERS
                    if skipping:
                        continue
                    self.chapter = None
                    chap = self.add("x", "chapter", None, None, title, page)  # id set below
                    self.by_id.pop("x", None)
                    ban = self.banner.get(page)
                    if ban:
                        chap["valid_to" if ban[0] == "until" else "valid_from"] = ban[1]
                    self.chapter = chap
                    m = re.match(r"^(Section|Appendix|Requirement|Regulation)\s+([A-Z]?\d*[A-Z]?\d*)\b", title)
                    chap["type"] = "appendix" if m and m.group(1) == "Appendix" else "chapter"
                    chap["number"] = m.group(2) if m else None
                    base = f"{m.group(1).lower()}-{m.group(2).lower()}" if m else slugify(title)[:60]
                    chap["id"] = base + self.suffix()
                    if chap["id"] in self.by_id:
                        self.issues.append(f"duplicate section id {chap['id']} (file page {page})")
                        chap["id"] += f"-p{page}"
                    self.by_id[chap["id"]] = chap
                    chap["_top"] = l["top"]
                    h1 = h2 = h3 = None
                    current = chap
                    continue
                if skipping or self.chapter is None:
                    continue
                parent_h = h3 or h2 or h1 or self.chapter
                # Diagrams
                if kind in ("caption", "diagram"):
                    sec = region_secs.get(n)
                    if sec is None:
                        sec = region_secs[n] = {"labels": [], "caption": [], "lines": []}
                    sec["caption" if kind == "caption" else "labels"].append(l)
                    continue
                # Tables
                if kind == "table-caption":
                    m = TABLE_RE.match(t)
                    num, rest = m.group(1), m.group(2).strip()
                    if rest.lower().startswith("continued") and last_table:
                        region_secs[n] = last_table
                        self.span(last_table, page, l["top"], l["top"] + 14)
                        continue
                    sid = f"table-{num.lower()}" + self.suffix()
                    sec = self.add(sid, "table", parent_h, num, (rest), page)
                    sec["kind_label"] = "table"
                    self.span(sec, page, l["top"], l["top"] + 14)
                    tables[sid] = last_table = region_secs[n] = sec
                    continue
                if kind == "table-caption-more":
                    sec = region_secs.get(n)
                    if sec is not None and sec.get("type") == "table":
                        sec["title"] = f"{sec['title']} {t}".strip()
                        sec["heading_path"][-1] = sec["title"]
                    continue
                if kind == "table":
                    sec = region_secs.get(n) or last_table
                    if sec is None:
                        self.issues.append(f"table text with no caption on file page {page}: {t[:40]}")
                        continue
                    sec["text"] = (sec["text"] + "\n" + t) if sec["text"] else t
                    self.span(sec, page, l["top"], l["top"] + l["size"] + 2)
                    continue
                # Small-print boxes
                if kind == "small":
                    sec = region_secs.get(n)
                    if sec is None:
                        is_req = self.chapter["id"].startswith(("requirement-", "regulation-"))
                        block = [m for k2, m in enumerate(lines) if reg.get(k2) == ("small", n)]
                        sizes = sorted(m["size"] for m in block)
                        if is_req:
                            k = 1 + sum(1 for s in self.sections if s["parent_id"] == self.chapter["id"]
                                        and s["type"] == "requirement")
                            sec = self.add(f"{self.chapter['id']}-box-{k}", "requirement", self.chapter, None,
                                           self.chapter["title"], page)
                        elif sizes[len(sizes) // 2] >= 9.0 and len(block) >= 3:
                            # A table with no caption (Appendix E): named after the heading above it.
                            host = h3 or h2 or h1 or self.chapter
                            k = 1 + sum(1 for s in self.sections if s["parent_id"] == host["id"] and s["type"] == "table")
                            sec = self.add(f"{host['id']}-table-{k}", "table", host, None, host["title"], page)
                            last_table = sec
                        else:
                            self.issues.append(f"file page {page}: {len(block)} lines of very small print skipped "
                                               f"(a picture made of text, e.g. a sample page): {t[:40]}")
                            sec = {"_skip": True}
                        region_secs[n] = sec
                    if sec.get("_skip"):
                        continue
                    sec["text"] = (sec["text"] + "\n" + t) if sec["text"] else t
                    self.span(sec, page, l["top"], l["top"] + l["size"] + 2)
                    continue
                all_bold = ws and all(_bold(w) for w in ws)
                # Definitions (key terms): a bold term at the start of a line, then its meaning.
                if self.chapter["id"].startswith("appendix-a") and ws and _bold(ws[0]) and not t.startswith("NOTE") \
                        and abs(l["size"] - BODY) < 0.6:
                    k = 0
                    while k < len(ws) and _bold(ws[k]):
                        k += 1
                    term = _text(ws[:k]).lstrip("*").strip()
                    if current is not None and current["type"] == "definition" and not current["text"]:
                        current["title"] = f"{current['title']} {term}"  # the term wraps onto this line
                        current["heading_path"][-1] = current["title"]
                        current["text"] = _text(ws[k:])
                        self._terms(current, ws[k:])
                        continue
                    from_regs = ws[0]["text"].startswith("*")
                    sec = self.add(f"definition-tmp-{len(self.sections)}", "definition", self.chapter, None, term, page, _text(ws[k:]))
                    sec["from_building_regulations"] = from_regs
                    current = sec
                    self._terms(sec, ws[k:])
                    continue
                # Headings
                if all_bold and l["size"] >= 14.5 and current is not None and current["type"] == "heading" \
                        and current.get("_heading_top") is not None and current.get("_size") == l["size"] \
                        and 0 < l["top"] - current["_heading_top"] < l["size"] * 1.3:
                    current["title"] = f"{current['title']} {t}"
                    current["heading_path"][-1] = current["title"]
                    current["_heading_top"] = l["top"]
                    continue
                if all_bold and l["size"] >= 19.5:
                    h1 = self._heading(t, page, self.chapter, 1, l)
                    h2 = h3 = None
                    current = h1
                    continue
                if all_bold and 14.5 <= l["size"] < 19.5:
                    if t == "Requirement" and self.chapter["id"].startswith("requirement-"):
                        continue  # the box below carries the requirement
                    h2 = self._heading(t, page, h1 or self.chapter, 2, l)
                    h3 = None
                    current = h2
                    continue
                if all_bold and 11.5 <= l["size"] < 14.5 and not t.startswith("NOTE") and not NUM_RE.match(ws[0]["text"]):
                    if current is not None and current.get("_heading_top") is not None and current["type"] == "heading" \
                            and current["level"] == 3 and l["top"] - current["_heading_top"] < 16:
                        current["title"] = (current["title"] + " " + t)
                        current["heading_path"][-1] = current["title"]
                        continue
                    h3 = self._heading(t, page, h2 or h1 or self.chapter, 3, l)
                    current = h3
                    continue
                # Numbered paragraphs ("3.100Doors": a long number can touch the first word)
                if ws and _bold(ws[0]) and abs(l["size"] - BODY) < 0.6:
                    m = re.match(r"^(\d{1,2}\.\d{1,3}|[A-G]\d{1,3})([A-Z][a-z].*)$", ws[0]["text"])
                    if m:
                        ws = [{**ws[0], "text": m.group(1)}, {**ws[0], "text": m.group(2), "b": False}] + ws[1:]
                if ws and _bold(ws[0]) and NUM_RE.match(ws[0]["text"]) and abs(l["size"] - BODY) < 0.6:
                    num = ws[0]["text"]
                    sec = self.add(f"para-{num.lower()}" + self.suffix(), "paragraph", parent_h, num,
                                   f"Paragraph {num}", page, _text(ws[1:]))
                    current = sec
                    self._terms(sec, ws[1:])
                    continue
                # Running text
                if current is None or current["type"] in ("chapter", "appendix", "heading"):
                    host = current or self.chapter
                    k = 1 + sum(1 for s in self.sections if s["parent_id"] == host["id"] and s["type"] == "text")
                    current = self.add(f"{host['id']}-text-{k}", "text", host, None, None, page)
                current["text"] = self._join(current["text"], t)
                self._terms(current, ws)
            # Close this page's diagrams.
            for n, r in region_secs.items():
                if isinstance(r, dict) and "caption" in r and r["caption"]:
                    self._diagram(page, r, h3 or h2 or h1 or self.chapter, self._diagram_top.get((page, n), 0.0))
        return self.finish()

    def _heading(self, t, page, parent, level, l) -> dict:
        title = (t)
        sid = f"{parent['id']}-{slugify(title)[:50]}"
        sec = self.add(sid, "heading", parent, None, title, page)
        sec["level"] = level
        sec["_heading_top"] = l["top"]
        sec["_size"] = l["size"]
        return sec

    def _diagram(self, page, r, parent, above: float = 0.0) -> None:
        cap = " ".join(c["text"] for c in r["caption"])
        m = DIAGRAM_RE.match(cap)
        num, title = m.group(1), (m.group(2).strip())
        labels = [(x["text"]) for x in sorted(r["labels"], key=lambda x: (x["top"], x["x0"]))]
        sec = self.add(f"diagram-{num.lower()}" + self.suffix(), "figure", parent, num, title, page, title)
        sec["kind_label"] = "diagram"
        sec["labels"] = labels
        # The drawing can reach above its highest label: cut from just below the last text line above it.
        top = above + 16 if above else 70.0
        bottom = max(x["top"] for x in r["caption"]) + 16
        sec["area"] = {"page": page, "top": max(70.0, top), "bottom": min(800.0, bottom), "x0": 28.0,
                       "x1": self.page_width - 28.0}
        sec["caption_box"] = {"page": page, "top": r["caption"][0]["top"], "x0": r["caption"][0]["x0"], "x1": 10_000}
        self.span(sec, page, sec["area"]["top"], sec["area"]["bottom"])

    def _terms(self, sec, ws) -> None:
        """Green words are the document's own links to its key terms."""
        run, terms = [], sec.setdefault("marked_terms", [])
        for w in list(ws) + [{"text": ""}]:
            if _green(w) and not _bold(w):
                run.append(w["text"])
                continue
            if run:
                term = (" ".join(run)).strip(" .,;:()")
                if term and term not in terms:
                    terms.append(term)
                run = []

    def _join(self, text: str, line: str) -> str:
        if not text:
            return line
        if LIST_RE.match(line) or line.startswith("NOTE"):
            return f"{text}\n{line}"
        if text.endswith("-") and len(text) > 1 and text[-2].isalpha():
            return text + line
        return f"{text} {line}"

    # -------------------------------------------------- finish

    def finish(self) -> dict:
        for s in [s for s in self.sections if s["type"] == "definition"]:
            self.by_id.pop(s["id"], None)
            sid = f"definition-{slugify(s['title'])}"
            s["id"] = sid if sid not in self.by_id else f"{sid}-p{s['file_page']}"
            if s["id"] != sid:
                self.issues.append(f"duplicate definition {s['title']!r}")
            self.by_id[s["id"]] = s
            self.definitions.append({"term": s["title"], "section_id": s["id"],
                                     "from_building_regulations": s.get("from_building_regulations", False)})
        for s in self.sections:
            s.pop("_top", None)
            s.pop("_heading_top", None)
            s.pop("_size", None)
            s["text"] = (s["text"]) if s.get("text") else s.get("text", "")
        self.attach_grids()
        for s in self.sections:
            if s["type"] in ("table", "figure", "requirement") and not self.apply_fix(s):
                if s["type"] == "requirement" and not s.get("grid"):
                    continue
                self.checks.append({"kind": "table" if s["type"] in ("table", "requirement") else "figure",
                                    "section_id": s["id"], "file_page": s["file_page"], "key": self.check_key(s),
                                    "area": s.get("area"), "spans": s.get("spans")})
        counts = Counter(s["type"] for s in self.sections)
        if not counts.get("paragraph"):
            self.issues.append("no numbered paragraphs found")
        return {
            **{k: self.meta.get(k) for k in ("source_id", "version_id", "valid_from", "valid_to", "sha256")},
            "title": self.title, "parser": PARSER, "page_count": max(self.pages, default=0),
            "image_display": self.meta.get("image_display", True),
            "sections": self.sections, "definitions": self.definitions, "issues": self.issues,
            "checks": self.checks, "repairs": dict(self.repairs.most_common()),
        }

    def attach_grids(self) -> None:
        for s in self.sections:
            if s["type"] not in ("table", "requirement"):
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
            elif s["type"] == "table":
                self.issues.append(f"{s['id']}: no ruled table found on its pages; the model must build the grid")

    def apply_fix(self, s: dict) -> bool:
        key = self.check_key(s)
        if s["type"] in ("table", "requirement"):
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


def build_tree(doc: dict, meta: dict, fixes: list[dict] | None = None) -> dict:
    return AdocBuilder(doc, meta, fixes).build()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--part", required=True, help="the part name in the version records")
    a = ap.parse_args(argv)
    import yaml

    doc = yaml.safe_load((CORPUS_DIR / "sources.yaml").read_text(encoding="utf-8"))
    src = next((s for s in doc["sources"] if s["id"] == a.source), {}) or {}
    root = CORPUS_DIR.parent
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (CORPUS_DIR / "versions" / a.source).glob("*.json")]
    recs = [r for r in recs if r["valid_to"] is None and r.get("part") == a.part]
    if not recs:
        print(f"no current version of {a.source} part {a.part}")
        return 1
    for r in recs:
        raw = root / r["raw_path"]
        if not raw.exists():
            print(f"missing raw file: {r['raw_path']}")
            return 1
        meta = {**r, "title": r.get("part_title") or src.get("title", a.source),
                "image_display": src.get("images", "show") != "check-only"}
        tree = build_tree(read_pdf(raw), meta, fixes=load_fixes(a.source))
        out = CORPUS_DIR / "parsed" / a.source / f"{r['version_id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        render_images(raw, tree, out.parent / r["version_id"])
        out.write_text(json.dumps(tree, ensure_ascii=False, indent=1), encoding="utf-8")
        types = Counter(s["type"] for s in tree["sections"])
        print(f"{r['version_id']}: {dict(types)}, {len(tree['issues'])} issues, {len(tree['checks'])} model checks, "
              f"-> {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
