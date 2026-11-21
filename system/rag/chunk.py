"""Turn parsed document trees into search chunks (ADR 0010, design: architecture/design/regulations-corpus.md).

    python -m system.rag.chunk                       # every parsed tree under corpus/parsed/
    python -m system.rag.chunk --source adb          # one source

Reads corpus/parsed/<source>/<version>.json and writes corpus/chunks/<source>/<version>.jsonl (not in git,
rebuilt from the trees) and corpus/chunk-report.md (in git: counts, splits, unresolved references).

Chunk units (design "Chunk units"):
- legislation: one chunk per regulation; a long regulation is split at its numbered paragraphs (1), (2),
  and every split is listed in the report. Regulation 2 gives one chunk per defined term. One chunk per
  Schedule 1 requirement (with its limits on application), per schedule paragraph and per table.
- guidance PDFs (Approved Documents, HSE): one chunk per numbered paragraph, box, note, text block,
  requirement box and key term. A long paragraph is split at its list items, and listed in the report.
- tables: one chunk for the whole table and one per row sentence (from the saved model fixes).
- figures: one chunk with caption, labels and the model's description.
Headings and chapters give no chunks; they are the breadcrumb.

Every chunk carries its filter fields (source, kind, legal weight, version, dates, applies_to, breadcrumb,
section, printed page, url), the text, and embed_text (breadcrumb + text). Cross-references found in the
text are resolved to section ids of the same document where possible; the rest are kept as unresolved.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from system.rag.corpus import CORPUS_DIR

ROOT = CORPUS_DIR.parent
MAX_CHARS = 2500  # above this a regulation or paragraph is split (about 600 tokens)
HARD_MAX = 6000   # safety net: anything still longer is cut at line breaks into MAX_CHARS parts (overnight S3)
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
SQUARE_BULLET = re.compile(r"[■▪]+")                 # HSE list markers left by the PDF parser (safety net)
PRINT_FOOTER = re.compile(r"\s*\bPage \d+ of \d+\b")  # "Published by HSE 08/11 Page 141 of 141"
SKIP_TYPES = {"part", "chapter", "appendix", "schedule", "schedule-part", "heading", "block", "back-matter",
              "references"}
NATION = {"england": "E", "england-wales": "E+W", "gb": "E+W+S", "uk": "E+W+S+NI"}
WEIGHT = {"legislation": "law", "approved-document": "statutory-guidance", "contract": "contract",
          "standard": "standard"}


def legal_weight(src: dict) -> str:
    """law, statutory-guidance, approved-code or guidance. A source can set legal_weight itself."""
    if src.get("legal_weight"):
        return src["legal_weight"]
    if src.get("kind") == "hse-guidance" and re.match(r"^hse-l\d+", src.get("id", "")):
        return "approved-code"  # HSE "L" books: approved codes of practice
    return WEIGHT.get(src.get("kind"), "guidance")


# ---------------------------------------------------------------- references

REF_PATTERNS = [  # (regex, id prefix); group 1 is the number. A letter after a number ("Diagram 5.2a") is a part.
    (re.compile(r"\bparagraphs? (\d+\.\d+|[A-G]\d+)[a-z]?\b"), "para-"),
    (re.compile(r"\bDiagram ([A-Z]?\d+(?:\.\d+)?)[a-z]?\b"), "diagram-"),
    (re.compile(r"\bTable ([A-Z]?\d+(?:\.\d+)?)[a-z]?\b"), "table-"),
    (re.compile(r"\bFigure (\d+)\b"), "figure-"),
    (re.compile(r"\bSection (\d+)\b(?!\.\d)"), "section-"),
    (re.compile(r"\bAppendix ([A-G]|\d+)\b"), "appendix-"),
    (re.compile(r"\bparagraph (\d+)\b(?![.\d])"), "para-"),
    (re.compile(r"\bregulation (\d+[A-Z]?)\b"), "regulation-"),
    (re.compile(r"\brequirement ([A-S]\d+(?:\(\d+\))?)\b"), "requirement:"),
]


def find_refs(text: str, own_id: str, ids: set[str], chunk: dict, regs_in: str | None = None) -> list[dict]:
    """Cross-references in the text. Resolved to a section id in the same document where one exists; a dated
    copy (-until-/-from-) is preferred when it matches the chunk's own dates."""
    out, seen = [], set()
    for rx, prefix in REF_PATTERNS:
        for m in rx.finditer(text):
            words, num = m.group(0), m.group(1)
            if prefix == "requirement:":  # Schedule 1 of the Building Regulations, another document
                key = ("br2010", f"schedule-1-{num.split('(')[0]}")
                if key not in seen:
                    seen.add(key)
                    out.append({"words": words, "to_source": "br2010", "to_section": key[1], "resolved": False})
                continue
            if prefix == "regulation-" and regs_in:  # an Approved Document's "regulation 7" is the Building Regulations'
                key = (regs_in, f"regulation-{num}")
                if key not in seen:
                    seen.add(key)
                    out.append({"words": words, "to_source": regs_in, "to_section": key[1], "resolved": False})
                continue
            base = prefix + num.lower()
            cands = [i for i in ids if (lo := i.lower()) == base or lo.startswith(base + "-until-")
                     or lo.startswith(base + "-from-")]
            if chunk.get("valid_to"):
                cands = [c for c in cands if "-until-" in c] or cands
            elif chunk.get("valid_from"):
                cands = [c for c in cands if "-from-" in c] or cands
            else:
                cands = [c for c in cands if c.lower() == base] or cands
            target = sorted(cands)[0] if cands else None
            if target == own_id or (target or words) in seen:
                continue
            seen.add(target or words)
            out.append({"words": words, "to_section": target, "resolved": bool(target)})
    return out


# ---------------------------------------------------------------- splitting

def split_paragraphs(text: str, limit: int | None = None) -> list[str]:
    """Split long guidance text at list items (a., b., i.) or line breaks, keeping the lead-in with the first
    part. Short text is returned whole."""
    limit = limit or MAX_CHARS
    if len(text) <= limit:
        return [text]
    lines = text.split("\n")
    parts, cur = [], ""
    for ln in lines:
        if cur and len(cur) + len(ln) + 1 > limit:
            parts.append(cur)
            cur = ln
        else:
            cur = f"{cur}\n{ln}" if cur else ln
    if cur:
        parts.append(cur)
    return parts


def hard_split(text: str, limit: int) -> list[str]:
    """split_paragraphs, then cut any part still over the limit at the last space before it (one huge line)."""
    out = []
    for part in split_paragraphs(text, limit):
        while len(part) > limit:
            cut = part.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            out.append(part[:cut].rstrip())
            part = part[cut:].lstrip()
        if part:
            out.append(part)
    return out


# ---------------------------------------------------------------- chunks

class Chunker:
    def __init__(self, tree: dict, src: dict, record: dict):
        self.tree, self.src, self.record = tree, src, record
        self.sections = tree["sections"]
        self.by_id = {s["id"]: s for s in self.sections}
        self.ids = set(self.by_id)
        self.terms = {d["term"].lower(): d for d in tree.get("definitions", [])}
        self.chunks: list[dict] = []
        self.used_ids: dict[str, int] = {}
        self.splits: list[str] = []
        self.legislation = src.get("kind") == "legislation"

    def base(self, s: dict) -> dict:
        valid_from = s.get("valid_from") or self.tree.get("valid_from")
        if self.src.get("amending") and self.record.get("edition_date"):
            # An amending instrument is news from the day it is made: findable then, with its in-force date kept.
            valid_from = min(valid_from or self.record["edition_date"], self.record["edition_date"])
        valid_to = s.get("valid_to") or self.tree.get("valid_to")
        applies = s.get("applies_to") or NATION.get(self.src.get("nation", ""), None)
        if s.get("url"):
            url = s["url"]
        else:
            page = s.get("file_page")
            url = (self.record.get("fetched_url") or self.src.get("url", "")) + (f"#page={page}" if page else "")
        return {
            "source_id": self.tree["source_id"], "source_title": self.src.get("title") or self.tree.get("title"),
            "kind": self.src.get("kind"),
            # L143 marks each passage: the regulation itself (law), the Approved Code of Practice, or guidance.
            "legal_weight": {"regulation": "law", "acop": "approved-code", "guidance": "guidance"}.get(
                s.get("status"), legal_weight(self.src)),
            "version_id": self.tree["version_id"], "edition_date": self.record.get("edition_date") or valid_from,
            "valid_from": valid_from, "valid_to": valid_to, "applies_to": applies,
            "in_force": self.tree.get("valid_from") if self.src.get("amending") else None,
            "section_id": s["id"], "section_number": s.get("number"), "section_title": s.get("title"),
            "heading_path": s.get("heading_path") or [], "printed_page": s.get("printed_page"), "url": url,
        }

    def add(self, s: dict, chunk_type: str, text: str, suffix: str = "", **extra) -> None:
        text = PRINT_FOOTER.sub("", SQUARE_BULLET.sub("•", CONTROL.sub("", text))).strip()
        if not text:
            return
        if len(text) > HARD_MAX:  # a giant clause or table that the structure did not split
            lines = text.split("\n")
            keep = lines[:1] if chunk_type in ("table", "requirement") and len(lines) > 2 else []
            body = "\n".join(lines[len(keep):])
            parts = hard_split(body, MAX_CHARS - sum(len(k) + 1 for k in keep))
            self.splits.append(f"{s['id']}{suffix}: {len(text)} characters, cut into {len(parts)} parts (safety net)")
            for i, p in enumerate(parts, start=1):
                self.add(s, chunk_type, "\n".join(keep + [p]), f"{suffix}#part-{i}", **extra)
            return
        c = self.base(s)
        path = [p for p in c["heading_path"] if p]
        if path and len(path[0]) > 60 and "," in path[0]:  # "Approved Document B ... volume 1: Dwellings, 2019 edition ..."
            path[0] = path[0].split(",")[0]
        crumbs = " › ".join(path)
        cid = f"{c['source_id']}:{c['version_id']}:{s['id']}{suffix}"
        n = self.used_ids[cid] = self.used_ids.get(cid, 0) + 1
        if n > 1:  # the parser gave two sections one id (e.g. two notes on one page)
            cid = f"{cid}~{n}"
        c.update({"id": cid, "chunk_type": chunk_type,
                  "text": text, "embed_text": f"{crumbs}\n{text}" if crumbs else text, **extra})
        c["references"] = find_refs(text, s["id"], self.ids, c,
                                    "br2010" if self.src.get("kind") == "approved-document" else None)
        used = [self.terms[t.lower()]["section_id"] if "section_id" in self.terms.get(t.lower(), {}) else None
                for t in s.get("marked_terms", [])]
        c["terms"] = sorted({u for u in used if u})
        self.chunks.append(c)

    def run(self) -> list[dict]:
        for s in self.sections:
            t = s["type"]
            if t in SKIP_TYPES:
                continue
            if self.legislation:
                self.legislation_section(s)
            else:
                self.guidance_section(s)
        if self.legislation:
            self.legislation_definitions()
        return self.chunks

    # -------------------------------------------------- legislation

    def legislation_section(self, s: dict) -> None:
        t = s["type"]
        if t == "regulation":
            if s["id"] == "regulation-2" and (s.get("title") or "").lower().startswith("interpretation"):
                return  # one chunk per defined term instead (legislation_definitions)
            kids = [k for k in self.sections if k["parent_id"] == s["id"] and k["type"] == "paragraph"]
            if len(s["text"]) > MAX_CHARS and kids:
                self.splits.append(f"{s['id']}: {len(s['text'])} characters, split into {len(kids)} paragraphs")
                for k in kids:
                    self.add(k, "clause", k["text"], parent_title=s.get("title"))
            else:
                self.add(s, "regulation", s["text"])
        elif t == "requirement":
            text = s["text"] + (f"\nLimits on application: {s['limits']}" if s.get("limits") else "")
            self.add(s, "requirement", text)
        elif t in ("schedule-paragraph", "table"):
            self.add(s, "table" if t == "table" else "paragraph", s["text"])
        # paragraphs inside regulations are chunked only when their regulation is split

    def legislation_definitions(self) -> None:
        reg2 = self.by_id.get("regulation-2")
        if not reg2 or not (reg2.get("title") or "").lower().startswith("interpretation"):
            return  # amending instruments: regulation 2 is the amendment, chunked as a regulation
        seen: Counter = Counter()
        for d in self.tree.get("definitions", []):
            if d.get("section_id") != "regulation-2":
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", d["term"].lower()).strip("-")
            seen[slug] += 1  # some terms are defined twice (e.g. under regulation 11D and 11U)
            fake = {**reg2, "id": f"regulation-2-term-{slug}" + (f"-{seen[slug]}" if seen[slug] > 1 else "")}
            self.add(fake, "definition", self.full_definition(d["text"], reg2["text"]), term=d["term"])

    @staticmethod
    def full_definition(text: str, reg_text: str) -> str:
        """Some parsed definitions stop at "means—" and lose their list. Take the definition from the regulation's
        own text, up to the next quoted term at the start of a line."""
        if not text.rstrip().endswith(("—", ":")):
            return text
        i = reg_text.find(text.rstrip())
        if i < 0:
            return text
        m = re.search(r"\n[“\"]", reg_text[i + len(text.rstrip()):])
        return reg_text[i:i + len(text.rstrip()) + (m.start() if m else len(reg_text))].strip()

    # -------------------------------------------------- guidance PDFs

    def guidance_section(self, s: dict) -> None:
        t = s["type"]
        if t in ("paragraph", "text", "note", "box", "definition"):
            parts = split_paragraphs(s["text"])
            if len(parts) > 1:
                self.splits.append(f"{s['id']}: {len(s['text'])} characters, split into {len(parts)} parts")
            ctype = {"text": "paragraph", "note": "note", "box": "box", "definition": "definition"}.get(t, "paragraph")
            for i, p in enumerate(parts, start=1):
                lead = s["title"] + ": " if t == "definition" else ""
                self.add(s, ctype, lead + p, f"#part-{i}" if len(parts) > 1 else "",
                         **({"term": s["title"]} if t == "definition" else {}))
        elif t in ("table", "requirement"):
            self.table(s)
        elif t == "figure":
            self.figure(s)

    def table(self, s: dict) -> None:
        cols, rows = s.get("columns") or [], s.get("grid") or []
        title = s.get("title") or ""
        label = f"Table {s['number']} {title}".strip() if s.get("number") else title
        if cols and rows:
            body = "\n".join(" | ".join(r) for r in [cols] + rows)
        else:
            body = s.get("text", "")
        ctype = "requirement" if s["type"] == "requirement" else "table"
        self.add(s, ctype, f"{label}\n{body}" if label else body)
        heads = set(s.get("heading_rows") or [])
        data_rows = [r for i, r in enumerate(rows) if i not in heads]
        for i, sentence in enumerate(s.get("row_sentences") or [], start=1):
            row = data_rows[i - 1] if i - 1 < len(data_rows) else None
            self.add(s, "table-row", sentence, f"#row-{i}", row=dict(zip(cols, row)) if row and cols else None)

    def figure(self, s: dict) -> None:
        kind = s.get("kind_label", "figure").title()
        parts = [f"{kind} {s.get('number')}: {s.get('title') or ''}".strip()]
        if s.get("description"):
            parts.append(s["description"])
        if s.get("labels"):
            parts.append("Labels: " + "; ".join(s["labels"]))
        self.add(s, "figure", "\n".join(parts), image_path=s.get("image_path"),
                 image_display=bool(self.tree.get("image_display", True)))


# ---------------------------------------------------------------- files

def load_sources() -> dict[str, dict]:
    import yaml

    doc = yaml.safe_load((CORPUS_DIR / "sources.yaml").read_text(encoding="utf-8"))
    return {s["id"]: s for s in doc["sources"]}


def version_record(source_id: str, version_id: str) -> dict:
    for p in (CORPUS_DIR / "versions" / source_id).glob("*.json"):
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("version_id") == version_id:
            return r
    return {}


def chunk_tree(tree: dict, src: dict, record: dict) -> tuple[list[dict], list[str]]:
    c = Chunker(tree, src, record)
    return c.run(), c.splits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", nargs="*")
    a = ap.parse_args(argv)
    sources = load_sources()
    trees = sorted((CORPUS_DIR / "parsed").glob("*/*.json"))
    report = ["# Chunk report", "", "Made by `python -m system.rag.chunk` from the parsed trees (not in git). "
              "Rebuilt on every run.", ""]
    for path in trees:
        sid = path.parent.name
        if a.source and sid not in a.source:
            continue
        tree = json.loads(path.read_text(encoding="utf-8"))
        if tree.get("checks"):
            print(f"{path.relative_to(ROOT)}: {len(tree['checks'])} model checks open; chunked anyway, listed in report")
        chunks, splits = chunk_tree(tree, sources.get(sid, {"id": sid}), version_record(sid, tree["version_id"]))
        out = CORPUS_DIR / "chunks" / sid / f"{tree['version_id']}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks), encoding="utf-8")
        types = Counter(c["chunk_type"] for c in chunks)
        refs = [r for c in chunks for r in c["references"]]
        unresolved = Counter(r["words"] for r in refs if not r["resolved"] and "to_source" not in r)
        sizes = sorted(len(c["text"]) for c in chunks)
        print(f"{sid} {tree['version_id']}: {len(chunks)} chunks {dict(types)} -> {out.relative_to(ROOT)}")
        report += [f"## {sid} `{tree['version_id']}`", "",
                   f"- Chunks: {len(chunks)} ({', '.join(f'{k} {v}' for k, v in types.most_common())}).",
                   f"- Text length: median {sizes[len(sizes) // 2] if sizes else 0}, longest {sizes[-1] if sizes else 0} characters.",
                   f"- Open model checks in the tree: {len(tree.get('checks', []))}.",
                   f"- Cross-references: {len(refs)}, resolved in this document {sum(r['resolved'] for r in refs)}, "
                   f"to another document {sum(1 for r in refs if 'to_source' in r)}, unresolved {sum(unresolved.values())}.",
                   f"- Splits ({len(splits)}):" if splits else "- Splits: none."]
        report += [f"  - {x}" for x in splits]
        if unresolved:
            report.append("- Unresolved references (most common): " +
                          ", ".join(f"\"{w}\" ×{n}" for w, n in unresolved.most_common(15)) + ".")
        report.append("")
    if not a.source:
        (CORPUS_DIR / "chunk-report.md").write_text("\n".join(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
