"""Library map and outside references (experiment M1, 25 Nov 2026).

Two questions, plain code only, no model:
1. Library map: one line per document in scope (title, kind, chapter headings). How big is it?
2. Outside references: which documents do our chunks cite that we do not hold? Is the citation binding
   ("to BS 5839", "in accordance with ...") or a plain mention ("see ...")? How many of the 60 tune questions have an
   expected section whose chunk cites a document we do not hold ("touched but not complete")?

    python evals/experiments/library-map/build.py --out DIR

Reads corpus/chunks (not in git) and corpus/sources.yaml. Writes to DIR: library-map.md (kept out of git, built from
document headings), outside-refs.csv and tune-outside.jsonl (names and counts only, no corpus text) and prints a
summary. The binding test is a guess by wording; see M1-library-map.md for how well it holds up.
"""
import argparse
import collections
import csv
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))
from system.rag.corpus import version_in_scope  # noqa: E402
from metrics import touches  # noqa: E402

# Outside documents, by pattern. Each match is normalised to a name ("BS EN 13501", "IET On-Site Guide").
PATTERNS = [
    ("standard", re.compile(r"\b((?:BS|PD)(?:\s?EN)?(?:\s?ISO)?(?:\s?IEC)?\s?\d{3,5}|PAS\s?\d{2,4}|"
                            r"(?<!BS )(?<!BS EN )EN\s?ISO\s?\d{3,5}|(?<!BS )(?<!PD )EN\s\d{3,5})")),
    ("iet", re.compile(r"\b(IET\s+(?:On-?Site Guide|Guidance Note\s?\d?|Wiring Regulations)|On-?Site Guide)", re.I)),
    ("nhbc", re.compile(r"\b(NHBC Standards?)\b")),
    ("manufacturer", re.compile(r"\b(manufacturer(?:'|’)?s?(?:'|’)?\s+(?:instructions|guidance|recommendations))", re.I)),
    ("hse-code", re.compile(r"\b(HSG\s?\d{2,3}|INDG\s?\d{2,4}|L\s?\d{3})\b")),
]
# How a citation is used. "list": a reading list, glossary or standards appendix (no detail is handed over).
# "mention": "see ...", "for more information" (the detail here may be enough). "binding": anything else in body text,
# such as "tested to BS 476-22", "should comply with BS 5839-1", "the recommendations in BS 5839-1 should be followed".
# A guess by wording, checked by hand on a sample (M1-library-map.md).
LIST_HEAD = re.compile(r"(standards|documents|publications) referred to|further reading|bibliography|references|"
                       r"glossary|useful (contacts|links)|other (documents|publications)", re.I)
LIST_LINE = re.compile(r"^[-\d.:/]*\s*(?:\(\d{4}\)|:\d{4}(?:\+A\d:\d{4})?)?\s+[A-Z][\w ,'()-]{8,}?\[\d{4}")
MENTION_BEFORE = re.compile(r"\b(see|cf\.?|refer to|more information|further (information|guidance|details))\b[^.;]*$",
                            re.I)
MENTION_AFTER = re.compile(r"^[-\d.:/A-Z]*\s*(?:\S+\s){0,3}?for (further|more|additional) (information|guidance|"
                           r"details?|advice)", re.I)


def use(text, m, heading_path):
    if LIST_HEAD.search(" ".join(heading_path or [])) or LIST_LINE.match(text[m.end():m.end() + 160]):
        return "list"
    if MENTION_BEFORE.search(text[max(0, m.start() - 60):m.start()]) or MENTION_AFTER.match(text[m.end():m.end() + 60]):
        return "mention"
    return "binding"


def norm(kind, m):
    s = re.sub(r"\s+", " ", m).strip()
    if kind == "standard":
        s = re.sub(r"^(BS|PD|PAS|EN)\s?", r"\1 ", s)
        s = re.sub(r"\b(EN|ISO|IEC)\s?(\d)", r"\1 \2", s)
    if kind == "hse-code":
        s = s.replace(" ", "")
    if kind == "iet":
        s = "IET " + re.sub(r"^IET\s+", "", s, flags=re.I).replace("Onsite", "On-Site").replace("On Site", "On-Site")
    if kind == "manufacturer":
        s = "manufacturer's instructions"
    return s


def source_names(S):
    """name -> (source id, mode, status) for outside documents we list in sources.yaml."""
    out = {}
    for s in S:
        text = f"{s.get('title', '')} {s['id']}"
        for kind, pat in PATTERNS:
            for m in pat.findall(text):
                out.setdefault(norm(kind, m), (s["id"], s["mode"], s.get("status", "current")))
        if s["id"].startswith("hse-"):  # hse-hsg248 -> HSG248, hse-l143 -> L143
            code = s["id"][4:].upper()
            if re.fullmatch(r"(HSG\d+|INDG\d+|L\d{3})", code):
                out.setdefault(code, (s["id"], s["mode"], s.get("status", "current")))
    return out


def chunks():
    for f in sorted((ROOT / "corpus/chunks").glob("*/*.jsonl")):
        if f.parent.name.startswith("_"):
            continue
        first = json.loads(f.open().readline())
        if not version_in_scope(first["source_id"], first["version_id"]):
            continue
        for line in f.open():
            yield json.loads(line)


def refs_in(text, heading_path=()):
    """[(kind, name, use)] for each outside citation in the text; use is list, mention or binding."""
    return [(kind, norm(kind, m.group(1)), use(text, m, heading_path))
            for kind, pat in PATTERNS for m in pat.finditer(text)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    S = yaml.safe_load((ROOT / "corpus/sources.yaml").read_text())["sources"]
    listed = source_names(S)
    held_ids = {s["id"] for s in S if s["mode"] == "ingest"}

    docs = {}                                   # version id -> (source, title, kind, chapters)
    by_chunk = {}                               # "source:section" chunk key -> refs
    tally = collections.defaultdict(lambda: {"kind": "", "chunks": 0, "binding": 0, "listed_only": 0, "docs": set()})
    n = 0
    for c in chunks():
        n += 1
        d = docs.setdefault(c["version_id"], (c["source_id"], c["source_title"], c["kind"], []))
        hp = c.get("heading_path") or []
        if len(hp) > 1 and hp[1] not in d[3] and hp[1] != "Text":
            d[3].append(hp[1])
        R = [r for r in refs_in(c["text"], hp) if listed.get(r[1], ("", "", ""))[0] not in held_ids]
        if R:
            by_chunk.setdefault(f"{c['source_id']}:{c['section_id']}", []).extend(R)
        for name in {nm for _, nm, _ in R}:
            t = tally[name]
            uses = {u for k, nm, u in R if nm == name}
            t["kind"] = next(k for k, nm, _ in R if nm == name)
            t["chunks"] += 1
            t["binding"] += "binding" in uses
            t["listed_only"] += uses == {"list"}
            t["docs"].add(c["source_id"])

    # 1. Library map
    lines = [f"- {s} ({k}): {t}" + (f" | {'; '.join(ch[:12])}" + (" ..." if len(ch) > 12 else "") if ch else "")
             for s, t, k, ch in sorted(docs.values())]
    (out / "library-map.md").write_text("\n".join(lines) + "\n")
    short = [f"- {s} ({k}): {t}" for s, t, k, _ in sorted(set((s, t, k, ()) for s, t, k, _ in docs.values()))]
    print(f"chunks in scope {n}, document versions {len(docs)}")
    print(f"library map with chapters: {len(lines)} lines, ~{sum(map(len, lines)) // 4} tokens; "
          f"titles only (one per source and title): {len(short)} lines, ~{sum(map(len, short)) // 4} tokens")

    # 2. Outside references
    with open(out / "outside-refs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "kind", "chunks", "binding_chunks", "list_only_chunks", "documents", "in_sources_yaml", "mode", "status"])
        for name, t in sorted(tally.items(), key=lambda kv: -kv[1]["chunks"]):
            sid, mode, status = listed.get(name, ("", "", ""))
            w.writerow([name, t["kind"], t["chunks"], t["binding"], t["listed_only"], len(t["docs"]), sid, mode, status])
    hit = sum(1 for _ in by_chunk)
    bind = sum(1 for R in by_chunk.values() if any(u == "binding" for _, _, u in R))
    lst = sum(1 for R in by_chunk.values() if all(u == "list" for _, _, u in R))
    kinds = collections.Counter(t["kind"] for t in tally.values())
    print(f"chunks citing an outside document: {hit} ({100 * hit / n:.1f}%), binding: {bind} ({100 * bind / n:.1f}%), "
          f"reading lists only: {lst}")
    print(f"distinct outside documents: {len(tally)} {dict(kinds)}; "
          f"listed in sources.yaml: {sum(1 for x in tally if x in listed)}")
    print("most cited (chunks, binding, documents, listed as):")
    for name, t in sorted(tally.items(), key=lambda kv: -kv[1]["chunks"])[:20]:
        sid, mode, status = listed.get(name, ("-", "", ""))
        print(f"  {name:28} {t['chunks']:5} {t['binding']:5} {len(t['docs']):3}  {sid} {mode} {status}")

    # 3. Tune questions whose expected sections cite an outside document
    split = json.loads((ROOT / "evals/experiments/decomposer/split.json").read_text())
    q = {}
    for f in (ROOT / "evals/golden/labelled").glob("*.jsonl"):
        for line in f.open():
            r = json.loads(line)
            q[r["id"]] = r
    labels = {json.loads(l)["id"]: json.loads(l).get("label", json.loads(l).get("kind"))
              for l in (ROOT / "evals/golden/questions.jsonl").open()}
    by_src = collections.defaultdict(list)
    for k in by_chunk:
        by_src[k.split(":")[0]].append(k)
    rows, count = [], collections.Counter()
    for qid in split["tune"]:
        found = {}
        for e in q.get(qid, {}).get("expected_sections", []):
            for k in by_src.get(e.split(":")[0], []):
                if touches(e, k):
                    for kind, name, u in by_chunk[k]:
                        found[name] = found.get(name, False) or u == "binding"
        lab = labels.get(qid)
        rows.append({"id": qid, "label": lab, "outside": sorted(found), "binding": sorted(x for x, b in found.items() if b)})
        count[(lab, "binding" if any(found.values()) else "mention" if found else "none")] += 1
    with open(out / "tune-outside.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("tune questions by label and outside citation in their expected sections:")
    for lab in sorted({l for l, _ in count}, key=str):
        print(f"  {lab:15} " + ", ".join(f"{w} {count[(lab, w)]}" for w in ("binding", "mention", "none")))


if __name__ == "__main__":
    main()
