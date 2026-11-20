"""Parse legislation.gov.uk XML (one point-in-time version) into a document tree.

    python -m system.rag.parse_legislation --source br2010 --current
    python -m system.rag.parse_legislation --source br2010 --since 2026-01-01

Design: architecture/design/regulations-corpus.md, ADR 0010. The tree is written to
corpus/parsed/<source_id>/<version_id>.json (not in git; rebuilt from raw files).

Tree:
    source_id, version_id, valid_from, valid_to, sha256, title, parser
    sections:    id, parent_id, type (part, chapter, block, regulation, paragraph),
                 number, title, heading_path, applies_to (E, W, E+W, ...), status,
                 text (clean, numbered lines, no amendment markers), amendments
                 (id, type, text), references (words, target, uri, internal), url,
                 alt_of / alt_versions (Wales copies of England-only provisions)
    definitions: id, term, text, section_id
    issues:      what this parser did not handle, for the model check or a later step

Step 1 covers the Body (Parts, Chapters, regulations). Schedules come in step 2.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from lxml import etree

from system.rag.corpus import CORPUS_DIR, slugify

PARSER = "legislation-xml/0.1"
NS = "http://www.legislation.gov.uk/namespaces/legislation"
L = f"{{{NS}}}"
P_LEVELS = {f"{L}P{n}" for n in range(2, 8)} | {f"{L}P"}
SKIP_INLINE = {f"{L}Pnumber", f"{L}CommentaryRef", f"{L}FootnoteRef"}
DOC_PATH_RE = re.compile(r"legislation\.gov\.uk/(?:id/)?([a-z]+/\d{4}/\d+)")
KEEP_NOTE_TYPES = {"F", "E", "C", "I", "X"}  # M notes are only citations of the enabling law


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


def heading(kind: str, number: str | None, title: str | None) -> str:
    return " ".join(p for p in [kind, number, title] if p)


class Parser:
    def __init__(self, data: bytes, meta: dict):
        self.root = etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True))
        self.meta = meta
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

    # ------------------------------------------------------------ sections

    def add(self, sec: dict) -> dict:
        if sec["id"] in self.by_id:
            self.issues.append(f"duplicate section id {sec['id']}")
        self.sections.append(sec)
        self.by_id[sec["id"]] = sec
        return sec

    def container(self, e, kind: str, parent: dict | None, path: list[str]) -> dict:
        num_el, title_el = e.find(f"{L}Number"), e.find(f"{L}Title")
        number = re.sub(r"^(PART|CHAPTER)\s+", "", inline(num_el), flags=re.I) if num_el is not None else None
        title = inline(title_el) if title_el is not None else None
        label = {"part": "Part", "chapter": "Chapter"}.get(kind)
        sid = e.get("id") or f"{parent['id'] if parent else 'body'}-{kind}-{slugify(title or number or '')}"
        return self.add({
            "id": sid, "parent_id": parent["id"] if parent else None, "type": kind, "number": number, "title": title,
            "heading_path": [*path, heading(label, number, title) if label else (title or "")],
            "applies_to": extent(e), "status": "repealed" if e.get("Status") == "Repealed" else "in_force",
            "text": "", "amendments": self.amendments_own(e), "references": [], "url": e.get("DocumentURI"),
        })

    def amendments_own(self, e) -> list[dict]:
        """Notes on a container's own number and title, not on everything inside it."""
        own = [x for x in (e.find(f"{L}Number"), e.find(f"{L}Title")) if x is not None]
        out: list[dict] = []
        for x in own:
            for a in self.amendments(x):
                if a not in out:
                    out.append(a)
        return out

    def regulation(self, group, parent: dict, path: list[str], suffix: str = "", applies_to: str | None = None) -> dict | None:
        p1 = group.find(f"{L}P1")
        if p1 is None:
            self.issues.append(f"P1group without P1 under {parent['id']}")
            return None
        title_el = group.find(f"{L}Title")
        title = inline(title_el) if title_el is not None else None
        num_el = p1.find(f"{L}Pnumber")
        number = inline(num_el) if num_el is not None else ""
        sid = (p1.get("id") or f"regulation-{number}") + suffix
        hp = [*path, heading("Regulation", number, title)]
        status = "repealed" if "Repealed" in (p1.get("Status"), group.get("Status")) else "in_force"
        reg = self.add({
            "id": sid, "parent_id": parent["id"], "type": "regulation", "number": number, "title": title,
            "heading_path": hp, "applies_to": applies_to or extent(p1), "status": status,
            "text": "\n".join(lines(p1)), "amendments": self.amendments(group), "references": self.references(p1),
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
                    "title": None, "heading_path": [*hp, f"({n})"], "applies_to": reg["applies_to"], "status": status,
                    "text": "\n".join(text), "amendments": self.amendments(p2), "references": self.references(p2),
                    "url": p2.get("DocumentURI") or reg["url"],
                })
            for odd in para_block:
                if tag(odd) in ("Tabular", "Figure"):
                    self.issues.append(f"{tag(odd)} inside {sid}: not parsed yet")
        self.collect_definitions(p1, sid)
        for v in (group.get("AltVersionRefs") or "").split():
            self.alt_owner[v] = sid
        return reg

    def walk(self, e, parent: dict | None, path: list[str]) -> None:
        for c in e:
            t = tag(c)
            if t == "Part":
                s = self.container(c, "part", parent, path)
                self.walk(c, s, s["heading_path"])
            elif t == "Chapter":
                s = self.container(c, "chapter", parent, path)
                self.walk(c, s, s["heading_path"])
            elif t == "Pblock":
                s = self.container(c, "block", parent, path)
                self.walk(c, s, s["heading_path"])
            elif t == "P1group":
                self.regulation(c, parent, path)
            elif t in ("Number", "Title", "SignedSection", ""):
                continue
            else:
                self.issues.append(f"unhandled <{t}> under {parent['id'] if parent else 'Body'}")

    def wales_versions(self) -> None:
        vs = self.root.find(f"{L}Versions")
        if vs is None:
            return
        for v in vs.findall(f"{L}Version"):
            owner_id = self.alt_owner.get(v.get("id"))
            group = v.find(f"{L}P1group")
            if owner_id is None or group is None:
                self.issues.append(f"version block {v.get('id')} ({v.get('Description')}) not linked to a regulation: step 2")
                continue
            owner = self.by_id[owner_id]
            parent = self.by_id[owner["parent_id"]]
            desc = v.get("Description") or "alt"
            alt = self.regulation(group, parent, parent["heading_path"], suffix=f"@{desc}", applies_to=extent(group) or desc)
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
            self.definitions.append({
                "id": term.get("id") or f"term-{slugify(name, 80)}",
                "term": name,
                "text": inline(holder) if holder is not None else name,
                "section_id": section_id,
            })

    def parse(self) -> dict:
        body = self.root.find(f".//{L}Body")
        if body is None:
            self.issues.append("no Body element")
        else:
            self.walk(body, None, [self.title])
        self.wales_versions()
        if self.root.find(f".//{L}Schedules") is not None and len(self.root.find(f".//{L}Schedules")):
            self.issues.append("Schedules not parsed yet: step 2")
        return {
            **{k: self.meta.get(k) for k in ("source_id", "version_id", "valid_from", "valid_to", "sha256")},
            "title": self.title,
            "parser": PARSER,
            "sections": self.sections,
            "definitions": self.definitions,
            "issues": self.issues,
        }


def parse_legislation(data: bytes, meta: dict) -> dict:
    return Parser(data, meta).parse()


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
    for r in pick:
        raw = root / r["raw_path"]
        if not raw.exists():
            print(f"missing raw file: {r['raw_path']}")
            continue
        tree = parse_legislation(raw.read_bytes(), {**r, "title": title})
        out = CORPUS_DIR / "parsed" / a.source / f"{r['version_id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(tree, ensure_ascii=False, indent=1), encoding="utf-8")
        regs = sum(1 for s in tree["sections"] if s["type"] == "regulation")
        print(f"{r['version_id']}: {len(tree['sections'])} sections, {regs} regulations, "
              f"{len(tree['definitions'])} definitions, {len(tree['issues'])} issues -> {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
