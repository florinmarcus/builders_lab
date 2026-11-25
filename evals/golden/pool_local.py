"""Pooled relevance judging: which retrieved passages also answer a dev question (25 Nov 2026, brief v2).

Labels written by one labeller are narrow: a GOV.UK booklet can answer a party wall question as well as the Act the
labeller chose. The pool is every passage in a run's top k for a dev question that does not already touch an expected
section. A judge decides each passage against the question's stored scope and rules (pooled/rules.jsonl, written once
per question with RULES-BRIEF.md): scope first, then each rule yes/no with a word-for-word quote, then the verdict
(POOL-JUDGE-BRIEF.md). "yes" becomes "also_acceptable" in questions.jsonl (build.py), and "found" counts it like an
expected section.

Checks in code (merge), after the published UK government judges (evals/knowledge/notes/uk-government-ai-evals/):
- every packet holds two planted lines with a known verdict (a labelled section, high confidence: yes; a section
  labelled for a question from another role: no). A packet with a planted "no" judged "yes", or a planted line
  INVALID for any other reason, is not merged. A planted "yes" judged "no" (with a valid line) does not fail the
  packet: in the first run about a quarter of labelled sections only cross-referred or were general, and separate
  judges agreed, so it is listed as a label to check (S116) and the run's planted-yes hit rate is printed;
- every "yes" rule must quote the passage word for word (spacing, quote marks and dashes aside); a verdict that is
  not "scope_match yes and at least one rule yes with a found quote" is INVALID. INVALID lines are never counted as
  yes or no: they go to DIR/invalid-*.jsonl, to be judged again;
- a judged file that does not match its packet line by line is INVALID as a whole.

No model on AWS (ADR 0017): the judge is a Claude Code subagent. This file does the plain parts: build the pool,
write packets, read the verdicts back.

    python evals/golden/pool_local.py packets --runs B1-v2-mixed-k20-dev-dev B3-v2-fused-k20-dev-dev --k 8 \\
        --sample 60 --out DIR                                                 # DIR/packet-*.jsonl, DIR/recheck-*.jsonl
    python evals/golden/pool_local.py merge --judged DIR/judged-packet-*.jsonl              # -> pooled/judgments.jsonl
    python evals/golden/pool_local.py merge --judged DIR/judged-recheck-*.jsonl --to evals/golden/pooled/recheck.jsonl

A judged file DIR/judged-<name>.jsonl is checked against DIR/<name>.jsonl (the packet) and DIR/planted.json.

--sample N picks N dev questions at random (seeded), so a first pass measures the whole set, not just misses.
Holdout questions are never pooled. Packets hold the question, the reference answer and the passage text (corpus
text: they stay in the scratchpad, never in git). The judge does not know which run found a passage.
judgments.jsonl holds ids, section keys, the verdict, the rules stated, the scope check, a one-sentence reason and
the judge name. Quotes are checked and dropped: no corpus text in git.
"""

from __future__ import annotations

import argparse
import glob
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "evals" / "golden"))
import build as B  # noqa: E402
import metrics as M  # noqa: E402

RESULTS = ROOT / "evals" / "results"
OUT = ROOT / "evals" / "golden" / "pooled" / "judgments.jsonl"
RULES = ROOT / "evals" / "golden" / "pooled" / "rules.jsonl"
VERDICTS = ("yes", "no")
_SAME = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-",
                       "\u00a0": " "})


def norm(text: str) -> str:
    """Text for the quote check: spacing, curly quotes and dashes do not count."""
    return re.sub(r"\s+", " ", (text or "").translate(_SAME)).strip().lower()


def check_line(j: dict, packet_row: dict, planted: str | None) -> str | None:
    """Why a judged line is INVALID, or None. planted: the known verdict of a planted line."""
    if (j.get("id"), j.get("section")) != (packet_row["id"], packet_row["section"]):
        return "line does not match its packet"
    if j.get("verdict") not in VERDICTS or j.get("scope_match") not in VERDICTS:
        return "verdict or scope_match not yes/no"
    rules = j.get("rules")
    if not isinstance(rules, list) or len(rules) != len(packet_row["rules"]):
        return "one entry per rule expected"
    passage = norm(packet_row["passage"])
    stated = []
    for r in rules:
        if not isinstance(r, dict) or r.get("states") not in VERDICTS:
            return "rule entry without states yes/no"
        if r["states"] == "yes":
            q = norm(r.get("quote", ""))
            if len(q) < 10 or q not in passage:
                return f"quote for rule {r.get('n')} not found in the passage"
            stated.append(r.get("n"))
    if j["verdict"] != ("yes" if j["scope_match"] == "yes" and stated else "no"):
        return "verdict does not follow from scope_match and rules"
    if planted and j["verdict"] != planted:
        return f"planted line judged {j['verdict']}, known {planted}"
    return None


def section_text(index: dict, key: str) -> str:
    """A section's own text, or (for a heading) the text of its children, with its breadcrumb."""
    s = index.get(key)
    if not s:
        return ""
    text = s.get("text") or ""
    if len(text) < 200:
        src = key.split(":")[0]
        kids = [v.get("text") or "" for k, v in index.items() if k.startswith(f"{src}:") and v.get("parent_id") == s["id"]]
        text = (text + "\n" + "\n".join(kids)).strip()
    return " > ".join(s.get("heading_path") or []) + "\n" + text


def keys_of(row: dict, k: int) -> list[str]:
    """The passages a run showed: its first k (lanes: every lane's first k)."""
    out = list((row.get("top5") or [x[0] for x in row.get("reranked") or []])[:k])
    for lane in (row.get("lanes") or {}).values():
        out += [x[0] for x in (lane.get("reranked") or [])[:k]]
    return list(dict.fromkeys(out))


def dev_ids(questions: dict) -> list[str]:
    return sorted(q for q, v in questions.items() if v.get("split") == "dev" and v.get("expected_sections"))


def pool(questions: dict, runs: list[str], k: int, ids: set[str], done: set) -> list[tuple[str, str]]:
    pairs = []
    for run in runs:
        for line in (RESULTS / f"{run}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            q = questions.get(r["id"])
            if r["id"] not in ids or not q:
                continue
            for key in keys_of(r, k):
                if (r["id"], key) in done or any(M.touches(e, key) for e in q["expected_sections"]):
                    continue
                done.add((r["id"], key))
                pairs.append((r["id"], key))
    return pairs


def write(out: Path, name: str, rows: list[dict], size: int) -> None:
    for i in range(0, len(rows), size):
        with open(out / f"{name}-{i // size:03d}.jsonl", "w", encoding="utf-8") as f:
            for r in rows[i:i + size]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("packets")
    p.add_argument("--runs", nargs="+", required=True)
    p.add_argument("--k", type=int, default=8)
    p.add_argument("--sample", type=int, help="this many random dev questions (default: all dev questions)")
    p.add_argument("--out", required=True)
    p.add_argument("--size", type=int, default=20, help="pairs per packet")
    p.add_argument("--recheck", type=float, default=0.10, help="share of pairs judged again, in other batches")
    p.add_argument("--seed", type=int, default=25)
    m = sub.add_parser("merge")
    m.add_argument("--judged", nargs="+", required=True)
    m.add_argument("--to", default=str(OUT), help="judgments.jsonl (primary judge) or recheck.jsonl")
    a = ap.parse_args(argv)
    questions = {q["id"]: q for q in read_jsonl(ROOT / "evals/golden/questions.jsonl")}
    if a.cmd == "packets":
        ids = dev_ids(questions)
        if a.sample:
            ids = sorted(random.Random(a.seed).sample(ids, a.sample))
        done = {(j["id"], j["section"]) for j in read_jsonl(OUT)}
        pairs = pool(questions, a.runs, a.k, set(ids), done)
        index = B.section_index()
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "questions.txt").write_text("\n".join(ids) + "\n")
        random.Random(a.seed).shuffle(pairs)  # mixed across questions: no batch holds one question's passages in a row
        rules = {r["id"]: r for r in read_jsonl(RULES)}
        missing = sorted({q for q, _ in pairs} - set(rules))
        if missing:
            sys.exit(f"no rules for {len(missing)} questions (write them with RULES-BRIEF.md first): {missing[:5]}")

        def row(qid: str, key: str) -> dict:
            return {"id": qid, "section": key, "question": questions[qid]["question"],
                    "question_scope": rules[qid]["scope"], "rules": rules[qid]["rules"],
                    "passage": section_text(index, key)[:6000]}

        rows = [row(qid, key) for qid, key in pairs]
        sample = random.Random(a.seed + 1).sample(rows, round(len(rows) * a.recheck))  # reshuffled: other neighbours
        rng = random.Random(a.seed + 2)
        planted: dict[str, str] = {}

        real = set(pairs)

        def plant(chunk: list[dict]) -> list[dict]:
            """Two lines with a known verdict, at random places: a high-confidence labelled section (yes) and a
            section labelled for a question from another role (no). Never a pair that is judged for real, never a
            section with almost no text."""
            def pick_yes():
                while True:
                    q = rng.choice([q for q in ids if q in rules and questions[q].get("label_confidence") == "high"])
                    k = rng.choice(questions[q]["expected_sections"])
                    if (q, k) not in real and len(section_text(index, k)) >= 300:
                        return q, k

            def pick_no():
                while True:
                    q = rng.choice([q for q in ids if q in rules])
                    o = rng.choice([x for x in questions if questions[x].get("role") != questions[q].get("role")
                                    and questions[x].get("expected_sections")])
                    k = rng.choice(questions[o]["expected_sections"])
                    if (q, k) not in real and k not in questions[q].get("expected_sections", []) \
                            and k not in questions[q].get("also_acceptable", []):
                        return q, k

            chunk = list(chunk)
            for (q, k), v in ((pick_yes(), "yes"), (pick_no(), "no")):
                planted[f"{q}|{k}"] = v
                chunk.insert(rng.randrange(len(chunk) + 1), row(q, k))
            return chunk

        for name, rs in (("packet", rows), ("recheck", sample)):
            write(out, name, [r for i in range(0, len(rs), a.size) for r in plant(rs[i:i + a.size])], a.size + 2)
        (out / "planted.json").write_text(json.dumps(planted, indent=0))
        print(f"{len(rows)} pairs from {len(a.runs)} runs, {len({r['id'] for r in rows})} of {len(ids)} questions, "
              f"{(len(rows) + a.size - 1) // a.size} packets of {a.size} + 2 planted; re-check {len(sample)} pairs; in {out}")
        return 0
    to = Path(a.to)
    seen = {(j["id"], j["section"], j.get("judge")) for j in read_jsonl(to)}
    n = 0
    report: dict[str, list] = {"invalid_lines": [], "failed_packets": [], "planted": [], "planted_yes_missed": []}
    with open(to, "a", encoding="utf-8") as f:
        for path in sorted({p for g in a.judged for p in glob.glob(g)}):
            path = Path(path)
            packet = read_jsonl(path.with_name(path.name.removeprefix("judged-")))
            planted = json.loads((path.parent / "planted.json").read_text()) if (path.parent / "planted.json").exists() else {}
            judged = read_jsonl(path)
            if len(judged) != len(packet):
                report["failed_packets"].append((path.name, f"{len(judged)} lines for {len(packet)}"))
                continue
            why = [check_line(j, p, planted.get(f"{p['id']}|{p['section']}")) for j, p in zip(judged, packet)]
            bad_plant = []
            for j, p, w in zip(judged, packet, why):
                known = planted.get(f"{p['id']}|{p['section']}")
                if known is None:
                    continue
                report["planted"].append((known, w is None))
                if w == "planted line judged no, known yes":  # the label may be weak: listed, packet kept
                    report["planted_yes_missed"].append((path.name, p["id"], p["section"], (j.get("reason") or "")[:200]))
                elif w:
                    bad_plant.append(w)
            if bad_plant:
                report["failed_packets"].append((path.name, bad_plant[0]))
                continue
            invalid = []
            for j, p, w in zip(judged, packet, why):
                if f"{p['id']}|{p['section']}" in planted:
                    continue
                if w:
                    invalid.append(p)
                    report["invalid_lines"].append((path.name, p["id"], p["section"], w))
                    continue
                key = (j["id"], j["section"], j.get("judge"))
                if key in seen:
                    continue
                seen.add(key)
                f.write(json.dumps({"id": j["id"], "section": j["section"], "verdict": j["verdict"],
                                    "scope_match": j["scope_match"],
                                    "rules_stated": [r.get("n") for r in j["rules"] if r["states"] == "yes"],
                                    "passage_scope": (j.get("passage_scope") or "")[:200],
                                    "reason": (j.get("reason") or "")[:300], "judge": j.get("judge", "claude-local")}) + "\n")
                n += 1
            if invalid:
                with open(path.parent / f"invalid-{path.name.removeprefix('judged-')}", "w", encoding="utf-8") as g:
                    for p in invalid:
                        g.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"merged {n} verdicts into {to}; {len(report['invalid_lines'])} INVALID lines; "
          f"{len(report['failed_packets'])} packets failed")
    for x in report["failed_packets"] + report["invalid_lines"]:
        print("  ", *x)
    for kind in ("yes", "no"):
        got = [ok for k, ok in report["planted"] if k == kind]
        if got:
            print(f"planted {kind}: {sum(got)}/{len(got)} judged as known")
    if report["planted_yes_missed"]:
        print("planted yes judged no (check these labels, S116):")
        for x in report["planted_yes_missed"]:
            print("  ", *x)
    return 0

if __name__ == "__main__":
    sys.exit(main())
