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
from system.rag.parse_pdf import render_images

PARSER = "approved-document-pdf/0.1"
BODY = 12.0
SMALL = 10.6  # below this: diagram labels, table text, requirement boxes (some list items are 11pt)
LABEL_MAX = 10.95  # labels above a diagram caption can be a little larger (AD K Diagram 10.2: 10.9pt)
RARE_AFTER_F = set("bcdgjkmnpqsvwxz")  # letters that almost never follow "f" in English words
NUM_RE = re.compile(r"^(\d{1,2}\.\d{1,3}|[A-G]\d{1,3}|\d[A-H]\d{1,2})$")  # 2.5, B24, 2C17 (AD A sections 2A-2E)
LIST_RE = re.compile(r"^(?:[a-z]|[ivx]{1,4})\.\s|^•\s|^\(\w{1,4}\)\s")
TABLE_RE = re.compile(r"^Table ([A-Z]?\d+(?:\.\d+)?)\b\s*(.*)$")
TABLE_TO_RE = re.compile(r"^Table (to Diagram \d+)\b\s*(.*)$")  # AD J: "Table to Diagram 34"
SEE_RE = re.compile(r"^See (para|paragraph|paragraphs|paras) [0-9A-Z.]+( (to|and) [0-9A-Z.]+)?$")  # a drawing's own pointer
CONTINUED_RE = re.compile(r"^(Continued on page \d+|Continued)$")
DIAGRAM_RE = re.compile(r"^Diagram ([A-Z]?\d+(?:\.\d+)?|[ivx]{1,4})\b\s*(.*)$")
DOUBLED_RE = re.compile(r"(ffi|ffl|ff|fi|fl)\1+")
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}  # ligature characters in diagram labels
LIGATURE_RE = re.compile("[" + "".join(LIGATURES) + "]")  # a ligature printed twice: "specifification"
BANNER_RE =re.compile(r"(?i)(effective until|effective from) (\d{1,2} \w+ \d{4})")
SKIP_CHAPTERS = {"contents"}
STOP_CHAPTERS = {"index", "list of approved documents"}


def _date(text: str) -> str:
    return datetime.datetime.strptime(text, "%d %B %Y").date().isoformat()


def _white(w) -> bool:
    return w.get("c") in ([1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0])


def _green(w) -> bool:
    c = w.get("c")
    return bool(c) and len(c) == 3 and c[1] > 0.3 and c[0] < 0.2 and c[2] < 0.5


def _accent(w) -> bool:
    """Text in a spot (one-ink) colour: the key terms of the 2013 editions."""
    c = w.get("c")
    return bool(c) and len(c) == 1 and c[0] > 0.5


def _bold(w) -> bool:
    return bool(w.get("b"))


def _text(words) -> str:
    return " ".join(w["text"] for w in words)


def _part_size(words, default: float) -> float:
    """The most common word size of part of a line (words carry "s"), or the line's size."""
    sizes = Counter(round(w["s"], 1) for w in words if w.get("s"))
    return sizes.most_common(1)[0][0] if sizes else default


def _line(words, src) -> dict:
    return {**src, "words": words, "text": _text(words), "x0": words[0]["x0"] if words else src["x0"]}


class AdocBuilder:
    def __init__(self, doc: dict, meta: dict, fixes: list[dict] | None = None):
        self.meta = meta
        self.fixes = index(fixes)
        self.title = meta.get("title") or meta.get("source_id", "")
        self.page_width = doc.get("page_width") or 595.0
        if self.page_width > 700:  # older reads took the width of a double-page cover
            self.page_width = 595.3
        self.rects = doc.get("rects", [])
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
        self._diagram_area: dict[tuple[int, int], tuple[float, float, float, float]] = {}
        self.gutter: dict[int, float] = {}
        sizes = Counter()
        for l in doc["lines"]:
            if 100 < l["top"] < 780:
                sizes[l["size"]] += len(l["text"])
        body = sizes.most_common(1)[0][0] if sizes else BODY
        # The older two-column layout (2004-2016 editions: A, C, E, G, H, J, M ...): 10.5pt body text, 23pt chapter
        # titles, 14pt headings, captions in 12pt roman type above the drawing or table.
        # Some classic editions (AD M volume 2, 2015) set the body in 12pt: their 23pt chapter titles tell them apart.
        pages23 = {l["page"] for l in doc["lines"] if 22 <= l["size"] <= 24 and l["page"] > 1 and l["top"] < 200
                   and l.get("words") and _bold(l["words"][0])}
        pages26 = {l["page"] for l in doc["lines"] if 25 <= l["size"] <= 27.5 and l["page"] > 1 and l["top"] < 200
                   and l.get("words") and _bold(l["words"][0]) and l["text"].strip().lower() not in STOP_CHAPTERS}
        self.classic = 9.8 <= body <= 11.2 or len(pages23) >= 3 and not pages26
        self.body = body
        xs = Counter(round(l["x0"]) for l in doc["lines"] if abs(l["size"] - body) <= 0.6 and 100 < l["top"] < 780)
        self.margins = [x for x, _ in xs.most_common(6)]  # column left edges; captions sit 5.6pt inside them
        # Short documents without chapter titles (amendment booklets, corrections, FAQ notes): the largest size
        # used for headings on two or more pages after the cover is the chapter size.
        chap_range = (22, 24) if self.classic else (25, 27.5)
        has_chapters = any(chap_range[0] <= l["size"] <= chap_range[1] and l["page"] > 1 and l["top"] < 200
                           and l.get("words") and _bold(l["words"][0]) and l["text"].strip().lower() not in STOP_CHAPTERS
                           for l in doc["lines"])
        self.simple = not has_chapters
        self.chapter_size = 0.0
        if self.simple:
            self.classic = False
            pages_by_size = defaultdict(set)
            for l in doc["lines"]:
                if l["page"] > 1 and body + 4 <= l["size"] <= 30 and 40 < l["top"] < 780 \
                        and l["text"].strip().lower() not in {"contents", "the building regulations 2010", *STOP_CHAPTERS}:
                    pages_by_size[l["size"]].add(l["page"])
            sizes2 = [sz for sz, ps in pages_by_size.items() if len(ps) >= 2]
            self.chapter_size = max(sizes2, default=max(pages_by_size, default=0.0))
            if not self.chapter_size:  # a one-page note (corrections to AD G): its largest bold headings
                bolds = [l["size"] for l in doc["lines"] if l["page"] > 1 and body + 3 <= l["size"] <= 30
                         and 40 < l["top"] < 780 and l.get("words") and _bold(l["words"][0])]
                self.chapter_size = max(bolds, default=0.0)
        self._furniture(doc["lines"])

    # -------------------------------------------------- pages

    def _furniture(self, lines) -> None:
        head = 40 if self.classic else 82  # classic: the section tab and running header sit above 40
        for l in sorted(lines, key=lambda l: (l["page"], l["top"], l["x0"])):
            t = l["text"].strip()
            if l["top"] < head and not (l["size"] >= 20 and t.lower() in STOP_CHAPTERS):  # the back page title stops
                m = BANNER_RE.search(t)
                if m:
                    self.banner[l["page"]] = ("until" if "until" in m.group(1).lower() else "from", _date(m.group(2)))
                continue
            if l["top"] >= 795:
                if re.fullmatch(r"[0-9]{1,3}|[ivxlc]{1,6}", t) and l["size"] >= 13:
                    self.printed[l["page"]] = t
                elif self.classic:  # "O N L I N E V E R S I O N 13", "14 O N L I N E V E R S I O N"
                    m = re.fullmatch(r"(?:([0-9]{1,3}|[ivxlc]{1,6})\s+)?O N L I N E V E R S I O N(?:\s+([0-9]{1,3}|[ivxlc]{1,6}))?", t)
                    if m and (m.group(1) or m.group(2)):
                        self.printed[l["page"]] = m.group(1) or m.group(2)
                continue
            if "O N L I N E" in t:
                continue
            if self.simple and l["size"] >= 18 and t == "The Building Regulations 2010":
                continue  # the banner above each Approved Document's list of amendments
            if self.classic:
                l = self._normalise(l)
            elif self.simple:
                l = self._normalise_simple(l)
            self.pages[l["page"]].append(_line(l["words"], l) if l.get("words") else l)
        self._ligatures()
        if self.classic:
            self._find_gutters()
        for p in self.pages:
            ls = self._scripts(self.pages[p])
            self.pages[p] = self._columns_classic(p, ls) if self.classic else self._columns(p, ls)

    def _normalise(self, l: dict) -> dict:
        """Classic layout: map sizes onto the 2019 ones the rest of the parser knows (body 12, headings 15,
        chapters 26), and mark captions ("Table 2 ...", "Diagram 1 ...", 12pt roman) for regions()."""
        s, ws = l["size"], l.get("words") or []
        if len(ws) > 1 and (ws[0].get("s") or s) < 7 and (ws[1].get("s") or 0) >= 9:
            s = ws[1]["s"]  # a reference number in tiny type in front of a body line ("3 BS 7913:1998")
        bold0 = bool(ws) and _bold(ws[0])
        if 11.5 <= s <= 12.5 and ws and not bold0 and re.match(r"^(Table|Diagram)$", ws[0]["text"]) \
                and (TABLE_RE.match(l["text"]) or DIAGRAM_RE.match(l["text"]) or TABLE_TO_RE.match(l["text"])) \
                and (abs(s - self.body) > 0.6 or any(abs(ws[0]["x0"] - 5.6 - m) < 2 for m in self.margins)):
            return {**l, "size": BODY + 0.5, "cap": True}  # 12pt caption (also when the body is 12pt: inset 5.6pt)
        if abs(s - self.body) <= 0.6:
            s = BODY
        elif 22 <= s <= 24 and bold0:
            s = 26.0
        elif 13.5 <= s <= 14.5 and bold0:
            s = 15.0
        elif 11.5 <= s <= 12.5 and ws and not bold0 and re.match(r"^(Table|Diagram)$", ws[0]["text"]):
            return {**l, "size": BODY + 0.5, "cap": True}
        elif 11.5 <= s <= 12.5:
            s = 13.0  # other 12pt text (sub-headings): above body, below headings
        return {**l, "size": s}

    def _normalise_simple(self, l: dict) -> dict:
        """Documents without chapter titles: the chapter size becomes 26 and bold, other sizes between body and
        chapter become bold 15pt headings, body text 12pt."""
        s, ws = l["size"], l.get("words") or []
        if self.chapter_size and abs(s - self.chapter_size) < 0.3:
            return {**l, "size": 26.0, "words": [{**w, "b": True} for w in ws]}
        if self.body + 2 <= s < self.chapter_size:
            return {**l, "size": 15.0, "words": [{**w, "b": True} for w in ws]}
        if abs(s - self.body) <= 0.6:
            return {**l, "size": BODY}
        return l

    def _find_gutters(self) -> None:
        """The gutter of each page: where the right column starts (it differs on odd and even pages). Pages with
        little text use the most common gutter of pages with the same parity."""
        found: dict[int, float] = {}
        for p, ls in self.pages.items():
            xs = Counter()
            for l in ls:
                ws = l.get("words") or []
                if abs(l["size"] - BODY) > 0.6 or not ws:
                    continue
                if 280 <= ws[0]["x0"] <= 345:
                    xs[round(ws[0]["x0"])] += 1
                for a, b in zip(ws, ws[1:]):
                    if b["x0"] - a["x1"] > 8 and 280 <= b["x0"] <= 345:
                        xs[round(b["x0"])] += 1
            good = [x for x, c in xs.items() if c >= 3]
            if good:
                found[p] = float(min(good))
        for parity in (0, 1):
            vals = Counter(v for p, v in found.items() if p % 2 == parity)
            default = vals.most_common(1)[0][0] if vals else 310.0
            for p in self.pages:
                if p % 2 == parity:
                    self.gutter[p] = found.get(p, default)

    def _columns_classic(self, page: int, lines: list[dict]) -> list[dict]:
        """Classic layout: cut lines at the gutter, give each a column (0 left, 1 right, None for lines that cross
        the gutter: chapter titles, wide tables and drawings) and read band by band: lines that cross the gutter
        separate bands; inside a band the left column comes first."""
        g = self.gutter.get(page, 310.0)
        parts = []
        for l in lines:
            ws = l.get("words") or []
            if not ws:
                continue
            lw = [w for w in ws if w["x0"] < g - 4]
            rw = [w for w in ws if w["x0"] >= g - 4]
            if lw and rw and rw[0]["x0"] - lw[-1]["x1"] > 4:
                # pdfplumber joins words at the same height in both columns. Cut a body line, a caption beside
                # text, or any line whose two sides differ in size (a table row beside body text).
                sl, sr = lw[-1].get("s"), rw[0].get("s")
                differ = bool(sl and sr) and abs(sl - sr) > 1
                body_line = BODY - 0.6 <= l["size"] <= 21 and not 12.4 <= l["size"] <= 13.1
                # 12pt caption lines of two tables set side by side ("calculations – taps | calculations – baths")
                twin = 12.4 <= l["size"] <= 13.1 and rw[0]["x0"] - lw[-1]["x1"] > 15 and lw[-1]["x1"] < g - 2
                if body_line or differ or twin or l.get("cap") and lw[-1]["x1"] < g - 2:
                    right = _line(rw, {**{k: v for k, v in l.items() if k != "cap"}, "x0": rw[0]["x0"]})
                    if sr:
                        right = self._normalise({**right, "size": sr})
                    parts += [{**_line(lw, l), "col": 0}, {**right, "col": 1}]
                    continue
            x1 = max(w["x1"] for w in ws)
            col = 1 if ws[0]["x0"] >= g - 4 else (0 if x1 <= g - 1 else None)
            if l["size"] > 21:
                col = None
            parts.append({**l, "col": col})
        parts.sort(key=lambda l: (l["top"], l["x0"]))
        left = {}
        for l in parts:
            if l["col"] is not None and abs(l["size"] - BODY) < 0.6:
                left[l["col"]] = min(left.get(l["col"], 1e9), l["x0"])
        for l in parts:
            if l["col"] in left:
                l["indent"] = l["x0"] - left[l["col"]]
        band, prev_full, out = 0, False, []
        for l in parts:
            full = l["col"] is None
            if full != prev_full:
                band += 1
            prev_full = full
            out.append((band, l["col"] or 0, l["top"], l["x0"], l))
        out.sort(key=lambda x: x[:4])
        return [x[4] for x in out]

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
        the repaired word is more common in the same document than the broken one (and used at least 3 times). Every repair is counted.
        Some 2021-2023 PDFs (AD L, F, O) print a ligature twice ("specifification", "flfloor", "effiffifficiency"):
        the repeated pair is dropped first."""
        self.repairs: Counter = Counter()
        for ls in self.pages.values():
            for l in ls:
                changed = False
                def tripled(t3):
                    return len(t3) >= 3 and len(t3) % 3 == 0 and all(t3[i] == t3[i + 1] == t3[i + 2] for i in range(0, len(t3), 3))
                def doubled(t2):  # "CCoonntteennttss" (AD M volume 2 contents title)
                    return len(t2) >= 8 and len(t2) % 2 == 0 and all(t2[i] == t2[i + 1] for i in range(0, len(t2), 2))
                ws3 = l.get("words") or []
                whole = len(ws3) >= 2 and sum(tripled(w["text"]) for w in ws3) * 2 >= len(ws3)
                if len(ws3) <= 3 and ws3 and all(doubled(w["text"]) for w in ws3):
                    for w in ws3:
                        good = w["text"][::2]
                        self.repairs[f"{w['text']} -> {good}"] += 1
                        w["text"], changed = good, True
                    ws3 = []
                for w in ws3:
                    t3 = w["text"]
                    if whole and tripled(t3):
                        # text printed three times over for a bold effect (AD P 2013 requirement box): "RRReeeqqq"
                        good = t3[::3]
                        self.repairs[f"{t3} -> {good}"] += 1
                        w["text"], changed = good, True
                        continue
                    if LIGATURE_RE.search(w["text"]) or DOUBLED_RE.search(w["text"]):
                        good = DOUBLED_RE.sub(r"\1", LIGATURE_RE.sub(lambda m: LIGATURES[m.group(0)], w["text"]))
                        self.repairs[f"{w['text']} -> {good}"] += 1
                        w["text"], changed = good, True
                if changed:
                    l["text"] = _text(l["words"])
        vocab = Counter(re.sub(r"[^a-z]", "", w["text"].lower()) for ls in self.pages.values() for l in ls
                        for w in l.get("words") or [])
        fixes: dict[str, str] = {}
        for word, n in vocab.items():
            if len(word) < 3:
                continue
            best = None
            cands = [word[:i] + x + word[i:] for i in range(1, len(word) + 1) if word[i - 1] == "f" for x in ("i", "l")]
            cands += [word[:i] + x + word[i:] for i in range(len(word) + 1) for x in ("fi", "fl")
                      if i > 0 or len(word) >= 4]  # "red" is not a broken "fired"
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
            if l["size"] < max(SMALL, self.body - 0.6):  # 11pt text in a table or drawing (AD L vol 2 Table 5.6) is not a column
                continue
            ws = l.get("words") or []
            if ws and 280 <= ws[0]["x0"] <= 345:
                gutters[round(ws[0]["x0"])] += 1
            for a, b in zip(ws, ws[1:]):
                if b["x0"] - a["x1"] > 10 and 280 <= b["x0"] <= 345:
                    gutters[round(b["x0"])] += 1
        if sum(gutters.values()) < 6 or max(gutters.values()) < 2:  # scattered starts are not a column
            return lines
        g = min(x for x, c in gutters.items() if c >= 2)  # the right column can have two indents: use the outer one
        left, right = [], []
        for l in lines:
            ws = l.get("words") or []
            if l["size"] < SMALL or l["size"] > 21 or not ws:  # small print and chapter titles are not split
                # small print wholly in the right column (AD L vol 2 Table A2 beside the key terms) is read there
                (right if ws and l["size"] < SMALL and ws[0]["x0"] >= g - 4 else left).append(l)
                continue
            lw = [w for w in ws if w["x0"] < g - 4]
            rw = [w for w in ws if w["x0"] >= g - 4]
            # Each half takes its own words' size: a 12pt key term beside a 10pt table row was read as one line
            # (AD L 2026 vol 2 Table A1 beside the key terms).
            if lw:
                left.append(_line(lw, {**l, "size": _part_size(lw, l["size"]) if rw else l["size"]}))
            if rw:
                right.append(_line(rw, {**l, "x0": rw[0]["x0"], "size": _part_size(rw, l["size"]) if lw else l["size"]}))
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
        if sid in self.by_id and chap and kind in ("paragraph", "table", "figure") \
                and self.by_id[sid].get("_chapter") not in (None, chap["id"]):
            # The same number in another chapter (two volumes or two Parts in one booklet): scope it by chapter.
            sid = sec["id"] = f"{chap['id']}-{sid}"
        if sid in self.by_id and kind == "heading" and self.classic:
            k = 2  # classic: "Technical solution" / "Alternative approach" repeat under one chapter
            while f"{sid}-{k}" in self.by_id:
                k += 1
            sid = sec["id"] = f"{sid}-{k}"
        if sid in self.by_id:
            self.issues.append(f"duplicate section id {sid} (file page {page})")
            sid = sec["id"] = f"{sid}-p{page}"
        if chap:
            sec["_chapter"] = chap["id"]
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
        if self.classic:
            n = self._regions_classic(page, lines, out)
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
                                 and (m["size"] >= LABEL_MAX and "Medium" not in m["font"] and k not in out and not SEE_RE.match(m["text"])
                                      or out.get(k, ("",))[0] == "caption")],
                                default=0.0)
                # A table straight above the drawing (AD F Table 3.1 over Diagram 3.1): the labels start after the
                # widest gap between the table's caption and the diagram caption.
                tcap = [m["top"] for m in lines if top_limit <= m["top"] < l["top"] and TABLE_RE.match(m["text"])
                        and (m.get("words") or [{}])[0].get("b")]
                if tcap:
                    mid = sorted(m["top"] for m in lines if max(tcap) < m["top"] < l["top"])
                    gaps = [(b - a, a) for a, b in zip(mid, mid[1:])]
                    if gaps:
                        top_limit = max(gaps)[1]
                for k, m in enumerate(lines):
                    if k not in out and top_limit < m["top"] < l["top"] and (m["size"] < LABEL_MAX or "Medium" in m["font"] or SEE_RE.match(m["text"])):
                        out[k] = ("diagram", n)
                # Under another diagram's caption band, start below the band (its last line is about 22pt tall).
                cap_above = any(out.get(k, ("",))[0] == "caption" and m["top"] == top_limit for k, m in enumerate(lines))
                self._diagram_top[(page, n)] = top_limit + (8 if cap_above else 0)
                i = j
                continue
            i += 1
        # Tables: bold caption, then small text until the next body-size line.
        for i, l in enumerate(lines):
            if i in out:
                continue
            ws = l.get("words") or []
            if TABLE_RE.match(l["text"]) and ws and _bold(ws[0]) and l["size"] >= 11.5 and not self.classic:
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
                        # Body-size lines indented to the caption's title, straight after it, are the table's own
                        # introduction (AD L vol 2 Table D1): they stay in the table, and its rows follow.
                        cw = l.get("words") or []
                        tx = cw[2]["x0"] if len(cw) > 2 else None
                        if tx and not self.classic and abs(m["x0"] - tx) < 3 and not any(_bold(w) for w in mw[:1]) \
                                and all(out.get(j, ("",))[0] in ("table", "table-caption", "table-caption-more")
                                        for j in range(i + 1, k)):
                            out[k] = ("table", n)
                            continue
                        # A list a little larger than table text, set far inside the table, just under its rows (AD L
                        # 2026 vol 2 Table 5.6: 11pt conversion factors in the "Product standard" cell) is table text.
                        prev = max((lines[j]["top"] for j in range(i + 1, k) if out.get(j, ("",)) == ("table", n)), default=None)
                        if not self.classic and m["size"] < self.body - 0.6 and m["x0"] - l["x0"] > 150 \
                                and prev is not None and 0 < m["top"] - prev < 20:
                            out[k] = ("table", n)
                            continue
                        break
                    out[k] = ("table", n)
        # Footnotes (classic layout, AD C): a tiny superscript number, then 6.5pt text, at the foot of a column.
        if self.classic:
            last = None
            for i, l in enumerate(lines):
                ws = l.get("words") or []
                if i in out or l["size"] >= SMALL:
                    last = None
                    continue
                if l["top"] > 450 and len(ws) > 1 and re.fullmatch(r"\d{1,3}", ws[0]["text"]) \
                        and (ws[0].get("s") or l["size"]) < 5.0:
                    out[i] = ("footnote", i)
                    last = i
                elif last is not None and l["size"] < 7.5 and 0 < l["top"] - lines[last]["top"] < 14:
                    out[i] = ("footnote-more", out[last][1])
                    last = i
                else:
                    last = None
        # Small print just under a table's last row, in its column, is more of that table (AD L vol 2 Table A2: a
        # row set in body size splits the table's small print in two).
        if not self.classic:
            tl = {}
            for i, l in enumerate(lines):
                if out.get(i, ("",))[0] == "table":
                    tl[out[i][1]] = l
                elif i not in out and l["size"] < SMALL:
                    for n2, last in list(tl.items()):
                        if 0 < l["top"] - last["top"] < 36 and abs(l["x0"] - last["x0"]) < 40:
                            out[i] = ("table", n2)
                            tl[n2] = l
                            break
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

    def _regions_classic(self, page: int, lines: list[dict], out: dict) -> int:
        """Classic layout: the caption sits above its table or drawing. The region is the small print below the
        caption, in the caption's column (or both columns when the small print crosses the gutter), down to the
        next body-size line or caption there."""
        g = self.gutter.get(page, 310.0)
        n = 0
        caps = [i for i, l in enumerate(lines) if l.get("cap")]
        for i in caps:
            if i in out:
                continue
            c = lines[i]
            kind = "table" if c["text"].startswith("Table") else "diagram"
            if not (TABLE_RE.match(c["text"]) or TABLE_TO_RE.match(c["text"])) if kind == "table" else not DIAGRAM_RE.match(c["text"]):
                continue
            n += 1
            out[i] = ("table-caption" if kind == "table" else "caption", n)
            col = 1 if c["x0"] >= g - 4 else 0
            last = c
            wraps = [k for k, m in enumerate(lines) if k not in out and 12.4 <= m["size"] <= 13.1]
            for k in sorted(wraps, key=lambda k: lines[k]["top"]):  # wrapped caption (its words can be bold)
                m = lines[k]
                if 0 < m["top"] - last["top"] < 16 and -2 <= m["x0"] - c["x0"] < 90 \
                        and not TABLE_RE.match(m["text"]) and not DIAGRAM_RE.match(m["text"]):
                    out[k] = ("table-caption-more" if kind == "table" else "caption", n)
                    last = m
            def bottom_for(cols):
                stops = [m["top"] for k, m in enumerate(lines) if m["top"] > last["top"] + 2 and m.get("col") in cols
                         and k not in out and (abs(m["size"] - BODY) < 0.6 and m.get("col") is not None
                                               or m["size"] >= 14.5 or m.get("cap"))]  # body text never crosses the gutter
                return min(stops, default=795.0)
            # Full width when any of its small print, down to the next text in its own column, lies right of the gutter.
            b0 = bottom_for({col, None})
            wide = col == 0 and (c.get("col") is None or max(w["x1"] for w in c["words"]) > g + 20) or col == 0 and any(last["top"] < m["top"] < b0 and m.get("col") in (1, None) and k not in out
                                    and (m["size"] < SMALL or 12.4 <= m["size"] <= 13.1) for k, m in enumerate(lines))
            cols = {0, 1, None} if wide else {col, None}
            bottom = bottom_for(cols)
            for k, m in enumerate(lines):  # small print, and 12pt sub-titles inside a drawing ("Figure 3a")
                if k not in out and last["top"] < m["top"] < bottom and (m["size"] < SMALL or 12.4 <= m["size"] <= 13.1) \
                        and m.get("col") in cols:
                    out[k] = (kind, n)
            x0, x1 = (28.0, self.page_width - 28.0) if wide else ((28.0, g - 2) if col == 0 else (g - 10, self.page_width - 28.0))
            if kind == "diagram":
                # The drawing's frame (a filled box starting just under the caption) gives its true extent: many
                # classic drawings have their labels as outlines, not text.
                frame = [r for r in self.rects if r["page"] == page and 0 <= r["top"] - c["top"] < 40
                         and abs(r["x0"] - c["x0"]) < 15 and r["bottom"] - r["top"] > 40]
                if frame:
                    r = max(frame, key=lambda r: r["bottom"] - r["top"])
                    self._diagram_area[(page, n)] = (c["top"] - 4, min(r["bottom"] + 4, 800.0), r["x0"] - 4, r["x1"] + 4)
                else:
                    self._diagram_area[(page, n)] = (c["top"] - 4, min(bottom - 4, 800.0), x0, x1)
        return n

    # -------------------------------------------------- build

    def build(self) -> dict:
        self.chapter = None
        root = None
        h1 = h2 = h3 = None
        current = None  # the section running text goes to
        prev_line = None  # ((page, column), top) of the last line added to running text
        skipping = True  # cover
        tables: dict[str, dict] = {}
        last_table = None
        for page in sorted(self.pages):
            lines = self.pages[page]
            reg = self.regions(page, lines)
            region_secs: dict[int, dict] = {}
            # (classic layout: tables and requirement boxes are set in 8pt, so only far smaller text counts)
            tiny = [l for k, l in enumerate(lines) if reg.get(k, ("",))[0] == "small"
                    and l["size"] < (0.0 if self.classic else 9.0)]  # classic: no pictures of pages
            if len(tiny) >= 10:
                # A picture of a page made of text (AD B page 8, the "how to use" sample page): if it has a diagram
                # caption, everything else on the page is that diagram's labels; if not, skip the page.
                caps = [v for v in reg.values() if v[0] == "caption"]
                if not caps:
                    self.issues.append(f"file page {page}: picture made of text with no caption, {len(lines)} lines skipped")
                    continue
                # Text below the caption band is the page's own text again (AD P page 14: para 2.5 under Diagram 1).
                cap_bottom = max(lines[k]["top"] for k, v in reg.items() if v == caps[0])
                new = {}
                for k in range(len(lines)):
                    if lines[k]["top"] <= cap_bottom:
                        new[k] = reg[k] if reg.get(k, ("",))[0] == "caption" else ("diagram", caps[0][1])
                    elif k in reg:
                        new[k] = reg[k]
                reg = new
                self._diagram_top[(page, caps[0][1])] = 0.0  # the picture fills the page
            for i, l in enumerate(lines):
                ws = l.get("words") or []
                t = l["text"].strip()
                if not t or self.classic and CONTINUED_RE.match(t):
                    continue
                kind, n = reg.get(i, (None, None))
                # Chapters
                if kind is None and ws and _bold(ws[0]) and (25 <= l["size"] <= 27.5 and (l["top"] < 200 or self.simple and l["top"] < 760)
                                                  or self.simple and self.chapter is None and page > 1
                                                  and 14.5 <= l["size"] < 25):  # booklet: "Introduction"
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
                    if chap["id"] in self.by_id and m:  # "Regulation 23(1) ..." and "Regulation 23(2) ...": use the code words
                        chap["id"] = slugify(title.split(":")[0])[:60] + self.suffix()
                    if chap["id"] in self.by_id and not m:  # a second "Guidance" chapter: number it
                        k = 2
                        while f"{chap['id']}-{k}" in self.by_id:
                            k += 1
                        chap["id"] += f"-{k}"
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
                    m = TABLE_RE.match(t) or TABLE_TO_RE.match(t)
                    num, rest = m.group(1), m.group(2).strip().lstrip(":").strip()
                    if rest.lower().startswith("continued") and last_table:
                        region_secs[n] = last_table
                        self.span(last_table, page, l["top"], l["top"] + 14)
                        continue
                    sid = f"table-{slugify(num) if ' ' in num else num.lower()}" + self.suffix()
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
                if kind in ("footnote", "footnote-more"):
                    host = current or self.chapter
                    if kind == "footnote":
                        host["footnotes"].append(t)
                    elif host["footnotes"]:
                        host["footnotes"][-1] += " " + t
                    continue
                if kind == "small":
                    sec = region_secs.get(n)
                    if sec is None:
                        is_req = self.chapter["id"].startswith(("requirement-", "regulation-")) or \
                            re.match(r"(?i)^(the )?requirements?\b", self.chapter["title"] or "")
                        block = [m for k2, m in enumerate(lines) if reg.get(k2) == ("small", n)]
                        sizes = sorted(m["size"] for m in block)
                        if is_req:
                            k = 1 + sum(1 for s in self.sections if s["parent_id"] == self.chapter["id"]
                                        and s["type"] == "requirement")
                            sec = self.add(f"{self.chapter['id']}-box-{k}", "requirement", self.chapter, None,
                                           self.chapter["title"], page)
                        elif sizes[len(sizes) // 2] >= 9.0 and len(block) >= 3 and not self.classic \
                                and sum(len(m["text"].split()) for m in block) >= 3 * len(block) \
                                and sum(1 for m in block if len(m["text"]) <= 3) <= 2:  # short label lines: a drawing
                            # A table with no caption (Appendix E): named after the heading above it.
                            host = h3 or h2 or h1 or self.chapter
                            k = 1 + sum(1 for s in self.sections if s["parent_id"] == host["id"] and s["type"] == "table")
                            sec = self.add(f"{host['id']}-table-{k}", "table", host, None, host["title"], page)
                            last_table = sec
                        elif page == max(self.pages):  # the publisher's back cover
                            sec = {"_skip": True}
                        elif self.classic or len(block) >= 3:
                            # Classic notes boxes; and (2019 layout) the labels of a drawing whose caption is not
                            # text (AD K Diagrams 9.1 and 9.2): kept as a text box, not a table.
                            # Classic layout: worked examples, notes and keys are set in 8pt: keep them as a text box.
                            host = h3 or h2 or h1 or self.chapter
                            k = 1 + sum(1 for s in self.sections if s["parent_id"] == host["id"] and s["id"].startswith(f"{host['id']}-box-"))
                            sec = self.add(f"{host['id']}-box-{k}", "text", host, None, host["title"], page)
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
                if self.classic and all_bold and abs(l["size"] - BODY) < 0.6 and prev_line and current is not None \
                        and current["type"] in ("paragraph", "text") and prev_line[0] == (page, l.get("col")) \
                        and 0 < l["top"] - prev_line[1] < 13:
                    all_bold = False  # a bold run-in title wrapping onto the next line ("2C6 Solid external walls ...")
                # Definitions (key terms): a bold term at the start of a line, then its meaning.
                # Older editions (AD P 2013) print the term in the accent colour on its own line, the meaning below.
                if self.chapter["id"].startswith("appendix-a") and ws and not t.startswith("NOTE") \
                        and (_bold(ws[0]) or all(_accent(w) for w in ws)) and abs(l["size"] - BODY) < 0.6:
                    k = 0
                    while k < len(ws) and (_bold(ws[k]) or _accent(ws[k])):
                        k += 1
                    term = _text(ws[:k]).strip("*").strip()
                    if current is not None and current["type"] == "definition" and not current["text"]:
                        current["title"] = f"{current['title']} {term}"  # the term wraps onto this line
                        current["heading_path"][-1] = current["title"]
                        current["text"] = _text(ws[k:])
                        self._terms(current, ws[k:])
                        continue
                    from_regs = ws[0]["text"].startswith("*") or ws[k - 1]["text"].endswith("*")
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
                    self._redo_duplicate_id(current)
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
                if ws and _bold(ws[0]) and NUM_RE.match(ws[0]["text"]) and abs(l["size"] - BODY) < 0.6 \
                        and l.get("indent", 0) <= 4 \
                        and not (self.classic and prev_line and prev_line[0] == (page, l.get("col"))
                                 and 0 < l["top"] - prev_line[1] < 13):  # classic: a bold cross-reference in running text
                    num = ws[0]["text"]
                    sec = self.add(f"para-{num.lower()}" + self.suffix(), "paragraph", parent_h, num,
                                   f"Paragraph {num}", page, _text(ws[1:]))
                    current = sec
                    self._terms(sec, ws[1:])
                    prev_line = ((page, l.get("col")), l["top"])
                    continue
                # Running text
                if current is None or current["type"] in ("chapter", "appendix", "heading"):
                    host = current or self.chapter
                    k = 1 + sum(1 for s in self.sections if s["parent_id"] == host["id"] and s["type"] == "text")
                    current = self.add(f"{host['id']}-text-{k}", "text", host, None, None, page)
                current["text"] = self._join(current["text"], t)
                prev_line = ((page, l.get("col")), l["top"])
                self._terms(current, ws)
            # Close this page's diagrams.
            for n, r in region_secs.items():
                if isinstance(r, dict) and "caption" in r and r["caption"]:
                    self._diagram(page, r, h3 or h2 or h1 or self.chapter, self._diagram_top.get((page, n), 0.0),
                                  self._diagram_area.get((page, n)))
        return self.finish()

    def _redo_duplicate_id(self, sec) -> None:
        """A heading whose first line repeats an earlier heading ("MAIN CHANGES MADE BY THE" / "2013 AMENDMENTS"):
        once its wrapped line is joined, give it an id from the whole title. Headings that were unique keep the id
        from their first line, so ids already in use do not move."""
        dup = f"-p{sec['file_page']}"
        if not sec["id"].endswith(dup):
            return
        parent = self.by_id.get(sec["parent_id"])
        sid = f"{parent['id'] if parent else ''}-{slugify(sec['title'])[:80]}".strip("-")
        if sid in self.by_id:
            return
        msg = f"duplicate section id {sec['id'][:-len(dup)]} (file page {sec['file_page']})"
        if msg in self.issues:
            self.issues.remove(msg)
        for s in self.sections:
            if s["parent_id"] == sec["id"]:
                s["parent_id"] = sid
        self.by_id.pop(sec["id"], None)
        sec["id"] = sid
        self.by_id[sid] = sec

    def _heading(self, t, page, parent, level, l) -> dict:
        title = (t)
        sid = f"{parent['id']}-{slugify(title)[:50]}"
        sec = self.add(sid, "heading", parent, None, title, page)
        sec["level"] = level
        sec["_heading_top"] = l["top"]
        sec["_size"] = l["size"]
        return sec

    def _diagram(self, page, r, parent, above: float = 0.0, area=None) -> None:
        cap = " ".join(c["text"] for c in r["caption"])
        m = DIAGRAM_RE.match(cap)
        num, title = m.group(1), (m.group(2).strip())
        labels = [(x["text"]) for x in sorted(r["labels"], key=lambda x: (x["top"], x["x0"]))]
        sid = f"diagram-{num.lower()}" + self.suffix()
        prev = self.by_id.get(sid)
        if prev is not None and prev["type"] == "figure" and prev["file_page"] == page - 1:
            sid += "-continued"  # a diagram carried over two pages (AD A Diagram 6)
        sec = self.add(sid, "figure", parent, num, title, page, title)
        sec["kind_label"] = "diagram"
        sec["labels"] = labels
        # The drawing can reach above its highest label: cut from just below the last text line above it.
        top = above + 16 if above else 70.0
        bottom = max(x["top"] for x in r["caption"]) + 16
        sec["area"] = {"page": page, "top": max(70.0, top), "bottom": min(800.0, bottom), "x0": 28.0,
                       "x1": self.page_width - 28.0}
        if area:  # classic layout: caption above, the drawing below it down to the next text
            sec["area"] = {"page": page, "top": max(40.0, area[0]), "bottom": max(area[0] + 40, area[1]),
                           "x0": area[2], "x1": area[3]}
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
            s.pop("_chapter", None)
            s["text"] = (s["text"]) if s.get("text") else s.get("text", "")
        pre = self.meta.get("id_prefix") or ""
        if pre:  # one source, several parts (two volumes, FAQ, amendment booklets): ids unique across the parts
            for s in self.sections:
                s["id"] = pre + s["id"]
                if s["parent_id"]:
                    s["parent_id"] = pre + s["parent_id"]
            for d in self.definitions:
                d["section_id"] = pre + d["section_id"]
            self.by_id = {s["id"]: s for s in self.sections}
        self.attach_grids()
        for s in self.sections:
            if s["type"] in ("table", "figure", "requirement") and not self.apply_fix(s):
                if s["type"] == "requirement" and not s.get("grid"):
                    continue
                self.checks.append({"kind": "table" if s["type"] in ("table", "requirement") else "figure",
                                    "section_id": s["id"], "file_page": s["file_page"], "key": self.check_key(s),
                                    "area": s.get("area"), "spans": s.get("spans")})
        counts = Counter(s["type"] for s in self.sections)
        if not counts.get("paragraph") and not self.simple:
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


def read_adoc_pdf(path) -> dict:
    """The PDF's lines, words, coloured boxes, images and ruled tables, as pdfplumber gives them. Lines are
    NOT cut into columns here (parse_pdf.read_pdf does that for HSE guides): this parser finds the Approved
    Document columns itself, so a change to the guide reader does not move AD text and its saved fixes."""
    import pdfplumber

    from system.rag.parse_pdf import _colour

    def _words(chars: list[dict]) -> list[dict]:
        """Words with x positions, size (s), bold (b) and colour (c) of their first character. AD PDFs have no
        space characters, only gaps. Bold fonts: "Bold", "Bd" (HelveticaNeueLTStd-Bd), "Heavy", "Black", "Semibold"."""
        words, cur, x0, x1, first, prev = [], "", None, None, None, None

        def emit():
            w = {"x0": round(x0, 1), "x1": round(x1, 1), "text": cur, "s": round(first["size"], 1)}
            fn = first.get("fontname") or ""
            if any(k in fn for k in ("Bold", "Heavy", "Black", "Semibold")) or re.search(r"-Bd(?:Cn|It)?$", fn):
                w["b"] = True
            col = _colour(first.get("non_stroking_color"))
            if col and col not in ((0.0,), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)):
                w["c"] = list(col)
            words.append(w)

        for c in chars:
            gap = prev is not None and c["x0"] - prev["x1"] > 1.5
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

    lines, rects, images, tables = [], [], [], []
    with pdfplumber.open(str(path)) as pdf:
        for n, page in enumerate(pdf.pages, start=1):
            for l in page.extract_text_lines(return_chars=True):
                first = l["chars"][0]
                m = first.get("matrix") or (1, 0, 0, 1)
                if not first.get("upright", True) or m[0] < 0 or m[3] < 0:  # sideways or upside-down text
                    continue
                lines.append({"page": n, "top": round(l["top"], 1), "x0": round(l["x0"], 1),
                              "size": round(first["size"], 1), "font": first["fontname"].split("+")[-1],
                              "text": l["text"], "words": _words(l["chars"])})
            for r in page.rects:
                col = _colour(r.get("non_stroking_color"))
                if r["width"] > 100 and r["height"] > 12 and col and col not in ((1.0,), (1.0, 1.0, 1.0)):
                    rects.append({"page": n, "top": round(r["top"], 1), "bottom": round(r["bottom"], 1),
                                  "x0": round(r["x0"], 1), "x1": round(r["x1"], 1), "colour": col})
            for im in page.images:
                images.append({"page": n, "top": round(im["top"], 1), "bottom": round(im["bottom"], 1),
                               "x0": round(im["x0"], 1), "x1": round(im["x1"], 1)})
            for t in page.find_tables():  # ruled tables: a hint for the model check
                rows = [[" ".join((c or "").split()) for c in row] for row in t.extract()]
                rows = [r for r in rows if any(r)]
                if rows:
                    x0, top, x1, bottom = t.bbox
                    tables.append({"page": n, "top": round(top, 1), "bottom": round(bottom, 1),
                                   "x0": round(x0, 1), "x1": round(x1, 1), "rows": rows})
        count = len(pdf.pages)
        widths = Counter(round(float(pg.width), 1) for pg in pdf.pages)  # the cover can be a double-page spread
        width = widths.most_common(1)[0][0] if widths else 595.0
    return {"lines": lines, "rects": rects, "images": images, "tables": tables, "page_count": count,
            "page_width": width}


def part_prefix(part: str, parts: list[str]) -> str:
    """Section-id prefix for one part of a source with several parts, so ids never repeat across the parts of
    one source (search keys are "<source>:<section_id>"). A source with one part gets no prefix (AD B volume 1
    keeps its ids). Rule: "...volume-N..." -> "vN-"; "frequently-asked-questions" -> "faq-"; "corrections..." ->
    "corrections-"; the main document ("approved-document-...") -> no prefix; an amendment booklet "<words>-amendment(s)-to-..." -> "amendments-<words>-" (e.g.
    "amendments-february-2023-"); any other part -> its slug up to 30 characters plus "-"."""
    if len(parts) <= 1:
        return ""
    m = re.match(r"^(.*?)-?amendments?-to-", part)
    if m:
        return f"amendments-{m.group(1)}-" if m.group(1) else "amendments-"
    m = re.search(r"volume-(\d+)", part)
    if m:
        return f"v{m.group(1)}-"
    if part.startswith("frequently-asked-questions"):
        return "faq-"
    if part.startswith("corrections"):
        return "corrections-"
    if "approved-document" in part:  # the main document of the source keeps plain ids
        return ""
    return slugify(part)[:30].strip("-") + "-"


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
                "image_display": src.get("images", "show") != "check-only",
                "id_prefix": part_prefix(a.part, (src.get("parser") or {}).get("parts") or [a.part])}
        tree = build_tree(read_adoc_pdf(raw), meta, fixes=load_fixes(a.source))
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
