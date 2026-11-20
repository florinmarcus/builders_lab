"""Parse legislation.gov.uk XML (one point-in-time version) into a document tree.

    python -m system.rag.parse_legislation --source br2010 --current
    python -m system.rag.parse_legislation --source br2010 --since 2026-01-01

Design: architecture/design/regulations-corpus.md, ADR 0010. The tree is written to
corpus/parsed/<source_id>/<version_id>.json (not in git; rebuilt from raw files).

Tree:
    source_id, version_id, valid_from, valid_to, sha256, title, parser
    sections:    id, parent_id, type (part, chapter, block, regulation, paragraph, schedule,
                 schedule-part, requirement, schedule-paragraph, table),
                 number, title, heading_path, applies_to (E, W, E+W, ...), status,
                 text (clean, numbered lines, no amendment markers), amendments
                 (id, type, text), references (words, target, uri, internal), url,
                 alt_of / alt_versions (Wales copies of England-only provisions),
                 limits (requirements only), label_source (code-guess / model) on duplicated Parts
    definitions: id, term, text, section_id
    issues:      what this parser did not handle or only guessed
    checks:      decisions for the model, with key, question, guess and evidence; answers are saved
                 in corpus/fixes/<source_id>.json (system/rag/fixes.py) and reused on the next run

Covers the Body (Parts, Chapters, regulations) and the Schedules. Schedule 1 becomes one section per
requirement (B1, M4(1)) with its limits on application. Parts printed twice (England and Wales copies)
get a code guess from their amendment notes, listed in issues for a model check.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from lxml import etree

from system.rag.corpus import CORPUS_DIR, slugify
from system.rag.fixes import content_key, index, load_fixes

PARSER = "legislation-xml/0.3"
NS = "http://www.legislation.gov.uk/namespaces/legislation"
L = f"{{{NS}}}"
X = "{http://www.w3.org/1999/xhtml}"
P_LEVELS = {f"{L}P{n}" for n in range(2, 8)} | {f"{L}P"}
SKIP_INLINE = {f"{L}Pnumber", f"{L}CommentaryRef", f"{L}FootnoteRef"}
DOC_PATH_RE = re.compile(r"legislation\.gov\.uk/(?:id/)?([a-z]+/\d{4}/\d+)")
KEEP_NOTE_TYPES = {"F", "E", "C", "I", "X"}  # M notes are only citations of the enabling law
# A Schedule 1 requirement starts with its code: "B1.", "K5.1.", "M4(1).", "M4(2) optional requirement",
# "G2A", or the code alone ("S1").
CODE_RE = re.compile(r"^((?:RA|[A-T])\d+[A-Z]?(?:\.\d+)?)(\(\d\))?(?=[.\s]|$)")
HEADER_CELLS = ("Requirement", "Limits on application")


def tag(e) -> str:
    return e.tag[len(L):] if isinstance(e.tag, str) and e.tag.startswith(L) else ""


def inline(e) -> str:
    """Visible text of an element, without markers, whitespace collapsed."""
    parts: list[str] = []

    def walk(x):
        if x is not e and x.tag in SKIP_INLINE:
            if x.tail:
                parts.append(x.tail)
            return
        if x.text:
            parts.append(x.text)
        for c in x:
            walk(c)
        if x is not e and x.tail:
            parts.append(x.tail)

    walk(e)
    return " ".join("".join(parts).split())


def lines(e) -> list[str]:
    """Block text of a provision as numbered lines: '(1) ...', '(a) ...'."""
    out: list[str] = []
    for c in e:
        t = tag(c)
        if t in ("Pnumber", "Title", "Number", "TitleBlock", "Reference"):
            continue
        if t == "Text":
            s = inline(c)
            if s:
                out.append(s)
        elif c.tag in P_LEVELS:
            num = c.find(f"{L}Pnumber")
            sub = lines(c)
            if num is not None and sub:
                sub[0] = f"({inline(num)}) {sub[0]}"
            out.extend(sub)
        elif isinstance(c.tag, str):
            out.extend(lines(c))
    return out


def extent(e) -> str | None:
    for x in [e, *e.iterancestors()]:
        if x.get("RestrictExtent"):
            return x.get("RestrictExtent")
    return None


def status(e) -> str:
    return "repealed" if any(x.get("Status") == "Repealed" for x in [e, *e.iterancestors()]) else "in_force"


def heading(kind: str | None, number: str | None, title: str | None) -> str:
    return " ".join(p for p in [kind, number, title] if p)


def sentence(text: str) -> str:
    """'FIRE SAFETY' -> 'Fire safety'. Mixed-case text is kept as it is."""
    return text[:1].upper() + text[1:].lower() if text.isupper() else text


def cell_paragraphs(cell) -> list[tuple[str, bool]]:
    """Paragraphs of a table cell, each with 'bold' = all its text is inside <Strong>."""
    texts = list(cell.iter(f"{L}Text")) or [cell]
    out = []
    for t in texts:
        s = inline(t)
        if not s:
            continue
        strong = " ".join(inline(x) for x in t.iter(f"{L}Strong"))
        out.append((s, " ".join(strong.split()) == s))
    return out


class Parser:
    def __init__(self, data: bytes, meta: dict, fixes: list[dict] | None = None):
        self.root = etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True))
        self.meta = meta
        self.fixes = index(fixes)
        self.checks: list[dict] = []
        self.title = meta.get("title") or self._doc_title()
        self.notes = {c.get("id"): c for c in self.root.iter(f"{L}Commentary")}
        self.doc_path = self._doc_path()
        self.sections: list[dict] = []
        self.definitions: list[dict] = []
        self.issues: list[str] = []
        self.by_id: dict[str, dict] = {}
        self.alt_owner: dict[str, str] = {}  # Version id -> England section id

    def _doc_title(self) -> str:
        t = self.root.find(".//{http://purl.org/dc/elements/1.1/}title")
        return t.text.strip() if t is not None and t.text else self.meta.get("source_id", "")

    def _doc_path(self) -> str | None:
        for e in self.root.iter():
            for a in ("IdURI", "DocumentURI"):
                m = DOC_PATH_RE.search(e.get(a) or "")
                if m:
                    return m.group(1)
        m = DOC_PATH_RE.search(self.meta.get("fetched_url") or "")
        return m.group(1) if m else None

    # ------------------------------------------------------------ metadata of a subtree

    def amendments(self, e) -> list[dict]:
        refs: list[str] = []
        for x in e.iter():
            for r in (x.get("Ref") if x.tag == f"{L}CommentaryRef" else None, x.get("CommentaryRef")):
                if r and r not in refs:
                    refs.append(r)
        out = []
        for r in refs:
            c = self.notes.get(r)
            if c is None:
                self.issues.append(f"amendment note {r} not found")
                continue
            if c.get("Type") in KEEP_NOTE_TYPES:
                out.append({"id": r, "type": c.get("Type"), "text": inline(c)})
        return out

    def references(self, e) -> list[dict]:
        out: list[dict] = []
        for x in e.iter(f"{L}CitationSubRef", f"{L}Citation"):
            uri = x.get("URI") or ""
            m = DOC_PATH_RE.search(uri)
            internal = bool(m and self.doc_path and m.group(1) == self.doc_path)
            ref = {"words": inline(x), "target": x.get("SectionRef") if internal else None, "uri": uri, "internal": internal}
            if ref not in out:
                out.append(ref)
        return out

    def amendments_own(self, e) -> list[dict]:
        """Notes on a container's own number and title, not on everything inside it."""
        own = [x for x in (e.find(f"{L}Number"), e.find(f"{L}Title"), e.find(f"{L}TitleBlock")) if x is not None]
        out: list[dict] = []
        for x in own:
            for a in self.amendments(x):
                if a not in out:
                    out.append(a)
        return out

    # ------------------------------------------------------------ sections

    def add(self, sec: dict) -> dict:
        if sec["id"] in self.by_id:
            self.issues.append(f"duplicate section id {sec['id']}")
        self.sections.append(sec)
        self.by_id[sec["id"]] = sec
        return sec

    def container(self, e, kind: str, parent: dict | None, path: list[str]) -> dict:
        num_el = e.find(f"{L}Number")
        title_el = e.find(f"{L}Title")
        if title_el is None:
            title_el = e.find(f"{L}TitleBlock/{L}Title")
        raw_num = inline(num_el) if num_el is not None else ""
        title = inline(title_el) if title_el is not None else None
        m = re.match(r"^(PART|CHAPTER|SCHEDULE)\s+(\S+)$", raw_num, flags=re.I)
        if m:
            number = m.group(2)
            head = heading(m.group(1).capitalize(), number, title)
        else:  # e.g. "CLASS 1" in Schedule 2
            number = raw_num or None
            head = heading(None, sentence(raw_num) if raw_num else None, title)
        sid = e.get("id") or f"{parent['id'] if parent else 'body'}-{kind}-{slugify(title or number or '')}"
        return self.add({
            "id": sid, "parent_id": parent["id"] if parent else None, "type": kind, "number": number, "title": title,
            "heading_path": [*path, head], "applies_to": extent(e), "status": status(e),
            "text": "", "amendments": self.amendments_own(e), "references": [], "url": e.get("DocumentURI"),
        })

    def provision(self, holder, parent: dict, path: list[str], kind: str = "regulation", suffix: str = "",
                  applies_to: str | None = None) -> dict | None:
        """A regulation (P1group/P1 in the Body) or a Schedule paragraph, with its numbered paragraphs."""
        p1 = holder if holder.tag in (f"{L}P1", f"{L}P") else holder.find(f"{L}P1")
        if p1 is None:
            p1 = holder.find(f"{L}P")  # "wrapper" paragraphs: a P1group holding an unnumbered P
        if p1 is not None and p1.get("id") is None and holder.get("id"):
            p1.set("id", holder.get("id"))
        if p1 is None:
            self.issues.append(f"{tag(holder)} without P1 under {parent['id']}")
            return None
        title_el = holder.find(f"{L}Title") if holder is not p1 else None
        title = inline(title_el) if title_el is not None else None
        num_el = p1.find(f"{L}Pnumber")
        number = inline(num_el) if num_el is not None else ""
        sid = (p1.get("id") or f"{parent['id']}-{number}") + suffix
        label = ("Section" if sid.startswith("section-") else "Regulation") if kind == "regulation" else "Paragraph"  # Acts have sections
        hp = [*path, heading(label, number, title)]
        st = status(p1)
        reg = self.add({
            "id": sid, "parent_id": parent["id"], "type": kind, "number": number, "title": title,
            "heading_path": hp, "applies_to": applies_to or extent(p1), "status": st,
            "text": "\n".join(lines(p1)), "amendments": self.amendments(holder), "references": self.references(p1),
            "url": p1.get("DocumentURI"),
        })
        for para_block in p1.findall(f"{L}P1para"):
            for p2 in para_block.findall(f"{L}P2"):
                num = p2.find(f"{L}Pnumber")
                n = inline(num) if num is not None else ""
                text = lines(p2)
                if text and n:
                    text[0] = f"({n}) {text[0]}"
                self.add({
                    "id": (p2.get("id") or f"{sid}-{n}") + suffix, "parent_id": sid, "type": "paragraph", "number": n,
                    "title": None, "heading_path": [*hp, f"({n})"], "applies_to": reg["applies_to"], "status": st,
                    "text": "\n".join(text), "amendments": self.amendments(p2), "references": self.references(p2),
                    "url": p2.get("DocumentURI") or reg["url"],
                })
            for odd in para_block:
                if tag(odd) in ("Tabular", "Figure"):
                    self.issues.append(f"{tag(odd)} inside {sid}: not parsed yet")
        self.collect_definitions(p1, sid)
        for x in (holder, p1):
            for v in (x.get("AltVersionRefs") or "").split():
                self.alt_owner[v] = sid
        return reg

    def walk(self, e, parent: dict | None, path: list[str], in_schedule: bool = False) -> None:
        for c in e:
            t = tag(c)
            if t in ("Part", "Chapter", "Pblock"):
                s = self.container(c, {"Part": "part", "Chapter": "chapter", "Pblock": "block"}[t], parent, path)
                self.walk(c, s, s["heading_path"], in_schedule)
            elif t in ("P1group", "P1"):
                self.provision(c, parent, path, "schedule-paragraph" if in_schedule else "regulation")
            elif t == "Schedule":
                s = self.container(c, "schedule", parent, path)
                body = c.find(f"{L}ScheduleBody")
                if body is not None:
                    if c.get("id") == "schedule-1":
                        self.schedule_1(body, s)
                    else:
                        self.walk(body, s, s["heading_path"], in_schedule=True)
            elif t == "Tabular" and parent is not None:
                self.table(c, parent, path)
            elif t == "P" and parent is not None:  # loose text in a Part, e.g. ". . ." for repealed paragraphs
                parent["text"] = "\n".join(x for x in [parent["text"], *lines(c)] if x)
            elif t in ("Number", "Title", "TitleBlock", "Reference", "SignedSection", ""):
                continue
            else:
                self.issues.append(f"unhandled <{t}> under {parent['id'] if parent else 'top level'}")

    def table(self, tab, parent: dict, path: list[str]) -> None:
        """A table in a Schedule other than Schedule 1: rows as text, cells joined by ' | '."""
        title_el = tab.find(f"{L}Title")
        title = inline(title_el) if title_el is not None else None
        rows = []
        for tr in tab.iter(f"{X}tr"):
            cells = [inline(c) for c in tr if c.tag in (f"{X}td", f"{X}th")]
            if any(cells):
                rows.append(" | ".join(cells))
        n = 1 + sum(1 for s in self.sections if s["parent_id"] == parent["id"] and s["type"] == "table")
        self.add({
            "id": f"{parent['id']}-table-{n}", "parent_id": parent["id"], "type": "table", "number": str(n),
            "title": title, "heading_path": [*path, title or f"Table {n}"], "applies_to": extent(tab),
            "status": status(tab), "text": "\n".join(rows), "amendments": self.amendments(tab),
            "references": self.references(tab), "url": parent.get("url"),
        })

    # ------------------------------------------------------------ Schedule 1: the requirements

    def schedule_1(self, body, sched: dict) -> None:
        parsed = [self.requirement_table(t) for t in body if tag(t) == "Tabular"]
        by_letter: dict[str, list[dict]] = {}
        for p in parsed:
            by_letter.setdefault(p["letter"], []).append(p)
        for letter, group in by_letter.items():
            labels: list[str | None] = [None] * len(group)
            source = None
            if len(group) == 2:
                labels, source = self.label_e_w(group)
            elif len(group) > 2:
                self.issues.append(f"schedule-1-part-{letter} appears {len(group)} times: model check")
            for p, lab in zip(group, labels):
                self.add_requirement_part(p, sched, lab, source)

    def requirement_table(self, tab) -> dict:
        """One Part of Schedule 1: letter, title, and requirements with text, limits and headings."""
        title_el = tab.find(f"{L}Title")
        title = inline(title_el) if title_el is not None else ""
        reqs: list[dict] = []
        cur: dict | None = None
        pending: str | None = None
        loose: list[str] = []
        for tr in tab.iter(f"{X}tr"):
            col = 0
            for cell in tr:
                if cell.tag not in (f"{X}td", f"{X}th"):
                    continue
                span = int(cell.get("colspan") or 1)
                is_th = cell.tag == f"{X}th"
                for text, bold in cell_paragraphs(cell):
                    m = CODE_RE.match(text)
                    if is_th and text in HEADER_CELLS:
                        continue
                    if col == 0 and m:
                        cur = {"code": m.group(1) + (m.group(2) or ""), "title": pending, "text": [text],
                               "limits": [], "els": [cell]}
                        pending = None
                        reqs.append(cur)
                    elif not title and re.match(r"^PART\s+[A-Z]+\b", text):
                        title = text
                    elif bold or (is_th and col == 0):
                        pending = text
                    elif col == 0:
                        if cur is not None:
                            cur["text"].append(text)
                            cur["els"].append(cell)
                        else:
                            loose.append(text)
                    elif cur is not None:
                        cur["limits"].append(text)
                        cur["els"].append(cell)
                col += span
        m = re.match(r"^PART\s+([A-Z]+)\s*(.*)$", title, flags=re.I)
        letter, ptitle = (m.group(1).upper(), m.group(2)) if m else ("?", title)
        if not reqs and loose:
            reqs.append({"code": None, "title": pending, "text": loose, "limits": [], "els": [tab]})
        return {"el": tab, "letter": letter, "title": sentence(ptitle) if ptitle else None, "reqs": reqs,
                "notes": self.amendments(tab), "key": content_key(inline(tab))}

    def label_e_w(self, group: list[dict]) -> tuple[list[str], str]:
        """Two copies of one Part: which is England's. A saved model fix decides; otherwise the code
        guesses from the amendment notes and asks for a model check."""
        letter = group[0]["letter"]
        saved = [self.fixes.get((p["key"], "applies_to")) for p in group]
        if all(saved):
            values = [f["value"] for f in saved]
            if sorted(values) == ["E", "W"]:
                return values, "model"
            self.issues.append(f"schedule-1-part-{letter}: saved fixes disagree ({values}); not used")

        def margin(p):
            text = " ".join(a["text"] for a in p["notes"] if a["type"] == "F")
            return len(re.findall(r"\(E\.", text)) - len(re.findall(r"\(W\.", text))

        a, b = margin(group[0]), margin(group[1])
        labels = ["E", "W"] if a >= b else ["W", "E"]
        self.issues.append(
            f"schedule-1-part-{letter}: two copies, code guessed {labels[0]} then {labels[1]} "
            f"from amendment notes (margins {a}, {b}); needs model check")
        for p, guess in zip(group, labels):
            self.checks.append({
                "kind": "applies_to", "key": p["key"], "part": letter, "guess": guess,
                "question": f"Schedule 1 Part {letter} is printed twice. Does this copy apply to England (E) or Wales (W)?",
                "codes": [r["code"] for r in p["reqs"]],
                "starts": p["el"].get("RestrictStartDate"),
                "evidence": [a["text"] for a in p["notes"] if a["type"] in ("F", "E")],
                "text": "\n".join(t for r in p["reqs"] for t in r["text"])[:1500],
            })
        return labels, "code-guess"

    def add_requirement_part(self, p: dict, sched: dict, label: str | None, source: str | None = None) -> None:
        suffix = "@W" if label == "W" else ""
        letter = p["letter"]
        pid = f"schedule-1-part-{letter}{suffix}"
        hp = [*sched["heading_path"], heading("Part", letter, p["title"])]
        part = self.add({
            "id": pid, "parent_id": sched["id"], "type": "schedule-part", "number": letter, "title": p["title"],
            "heading_path": hp, "applies_to": label or extent(p["el"]), "status": status(p["el"]),
            "text": "", "amendments": [], "references": [], "url": sched.get("url"),
        })
        if label:
            part["label_source"] = source or "code-guess"
            if suffix:
                part["alt_of"] = f"schedule-1-part-{letter}"
        for r in p["reqs"]:
            code = r["code"]
            code_source = None
            if not code:
                saved = self.fixes.get((p["key"], "requirement_code"))
                if saved:
                    code, code_source = saved["value"], "model"
                else:
                    self.issues.append(f"schedule-1-part-{letter}: no requirement code in the table; model check")
                    self.checks.append({
                        "kind": "requirement_code", "key": p["key"], "part": letter, "guess": None,
                        "question": f"Schedule 1 Part {letter} prints no requirement code. What is it (e.g. {letter}1)?",
                        "evidence": [a["text"] for a in p["notes"] if a["type"] in ("F", "E")],
                        "text": "\n".join(r["text"])[:1500],
                    })
            rid = f"schedule-1-{code}{suffix}" if code else f"schedule-1-{letter}-requirement{suffix}"
            notes: list[dict] = []
            refs: list[dict] = []
            for el in {id(e): e for e in r["els"]}.values():
                for a in self.amendments(el):
                    if a not in notes:
                        notes.append(a)
                for x in self.references(el):
                    if x not in refs:
                        refs.append(x)
            sec = self.add({
                "id": rid, "parent_id": pid, "type": "requirement", "number": code, "title": r["title"],
                "heading_path": [*hp, heading(None, code, r["title"]) or f"Part {letter}"],
                "applies_to": part["applies_to"], "status": part["status"], "text": "\n".join(r["text"]),
                "limits": "\n".join(r["limits"]), "amendments": notes, "references": refs, "url": sched.get("url"),
            })
            if suffix:
                sec["alt_of"] = rid[: -len(suffix)]
            if code_source:
                sec["code_source"] = code_source
            for el in {id(e): e for e in r["els"]}.values():
                self.collect_definitions(el, rid)

    # ------------------------------------------------------------ Wales copies and definitions

    def wales_versions(self) -> None:
        vs = self.root.find(f"{L}Versions")
        if vs is None:
            return
        for v in vs.findall(f"{L}Version"):
            owner_id = self.alt_owner.get(v.get("id"))
            holder = v.find(f"{L}P1group")
            if holder is None:
                holder = v.find(f"{L}P1")
            if owner_id is None or holder is None:
                self.issues.append(f"version block {v.get('id')} ({v.get('Description')}) not linked to a provision")
                continue
            owner = self.by_id[owner_id]
            parent = self.by_id[owner["parent_id"]]
            desc = v.get("Description") or "alt"
            alt = self.provision(holder, parent, parent["heading_path"], kind=owner["type"], suffix=f"@{desc}",
                                 applies_to=extent(holder) or desc)
            if alt is None:
                continue
            alt["alt_of"] = owner_id
            owner.setdefault("alt_versions", []).append(alt["id"])
            for s in self.sections:
                if s["parent_id"] == alt["id"]:
                    s["alt_of"] = s["id"].rsplit("@", 1)[0]

    def collect_definitions(self, scope, section_id: str) -> None:
        for term in scope.iter(f"{L}Term"):
            name = inline(term)
            holder = next((a for a in term.iterancestors() if tag(a) == "Text"), None)
            d = {
                "id": term.get("id") or f"term-{slugify(name, 80)}",
                "term": name,
                "text": inline(holder) if holder is not None else name,
                "section_id": section_id,
            }
            if d not in self.definitions:
                self.definitions.append(d)

    def parse(self) -> dict:
        body = self.root.find(f".//{L}Body")
        if body is None:
            self.issues.append("no Body element")
        else:
            self.walk(body, None, [self.title])
        schedules = self.root.find(f".//{L}Schedules")
        if schedules is not None:
            self.walk(schedules, None, [self.title])
        self.wales_versions()
        return {
            **{k: self.meta.get(k) for k in ("source_id", "version_id", "valid_from", "valid_to", "sha256")},
            "title": self.title,
            "parser": PARSER,
            "sections": self.sections,
            "definitions": self.definitions,
            "issues": self.issues,
            "checks": self.checks,
        }


def parse_legislation(data: bytes, meta: dict, fixes: list[dict] | None = None) -> dict:
    return Parser(data, meta, fixes).parse()


# ---------------------------------------------------------------- command line

def _records(source_id: str) -> list[dict]:
    return sorted((json.loads(p.read_text(encoding="utf-8")) for p in (CORPUS_DIR / "versions" / source_id).glob("*.json")),
                  key=lambda r: r["valid_from"])


def _title(source_id: str) -> str | None:
    import yaml

    doc = yaml.safe_load((CORPUS_DIR / "sources.yaml").read_text(encoding="utf-8"))
    s = next((s for s in doc["sources"] if s["id"] == source_id), None)
    return re.sub(r"\s*\(SI [^)]*\)\s*$", "", s["title"]) if s else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--current", action="store_true", help="the current version")
    ap.add_argument("--since", help="versions valid from this date (YYYY-MM-DD) onwards")
    a = ap.parse_args(argv)
    recs = _records(a.source)
    pick = [r for r in recs if (a.current and r["valid_to"] is None) or (a.since and r["valid_from"] >= a.since)]
    if not pick:
        print("No versions picked. Use --current and/or --since.")
        return 2
    root = CORPUS_DIR.parent
    title = _title(a.source)
    fixes = load_fixes(a.source)
    for r in pick:
        raw = root / r["raw_path"]
        if not raw.exists():
            print(f"missing raw file: {r['raw_path']}")
            continue
        tree = parse_legislation(raw.read_bytes(), {**r, "title": title}, fixes=fixes)
        out = CORPUS_DIR / "parsed" / a.source / f"{r['version_id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(tree, ensure_ascii=False, indent=1), encoding="utf-8")
        types: dict[str, int] = {}
        for s in tree["sections"]:
            types[s["type"]] = types.get(s["type"], 0) + 1
        print(f"{r['version_id']}: {types.get('regulation', 0)} regulations, {types.get('requirement', 0)} requirements, "
              f"{len(tree['sections'])} sections, {len(tree['definitions'])} definitions, "
              f"{len(tree['issues'])} issues, {len(tree['checks'])} model checks -> {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
