"""Pooled relevance judging: which retrieved passages also answer a dev question (25 Nov 2026).

Labels written by one labeller are narrow: a GOV.UK booklet can answer a party wall question as well as the Act the
labeller chose. The pool is every passage in a run's top k for a dev question that does not already touch an expected
section. A judge decides each passage with one yes/no question (POOL-JUDGE-BRIEF.md). "yes" becomes
"also_acceptable" in questions.jsonl (build.py), and "found" counts it like an expected section.

No model on AWS (ADR 0017): the judge is a Claude Code subagent. This file does the plain parts: build the pool,
write packets, read the verdicts back.

    python evals/golden/pool_local.py packets --runs B1-v2-mixed-k20-dev-dev B3-v2-fused-k20-dev-dev --k 8 \\
        --sample 60 --out DIR                                                 # DIR/packet-*.jsonl, DIR/recheck-*.jsonl
    python evals/golden/pool_local.py merge --judged DIR/judged-packet-*.jsonl              # -> pooled/judgments.jsonl
    python evals/golden/pool_local.py merge --judged DIR/judged-recheck-*.jsonl --to evals/golden/pooled/recheck.jsonl

--sample N picks N dev questions at random (seeded), so a first pass measures the whole set, not just misses.
Holdout questions are never pooled. Packets hold the question, the reference answer and the passage text (corpus
text: they stay in the scratchpad, never in git). The judge does not know which run found a passage.
judgments.jsonl holds ids, section keys, the verdict, a one-sentence reason and the judge name (no corpus text).
"""

from __future__ import annotations

import argparse
import glob
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "evals" / "golden"))
import build as B  # noqa: E402
import metrics as M  # noqa: E402

RESULTS = ROOT / "evals" / "results"
OUT = ROOT / "evals" / "golden" / "pooled" / "judgments.jsonl"
VERDICTS = ("yes", "no")


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
        rows = [{"id": qid, "section": key, "question": questions[qid]["question"],
                 "reference_answer": questions[qid].get("reference_answer"), "passage": section_text(index, key)[:6000]}
                for qid, key in pairs]
        write(out, "packet", rows, a.size)
        sample = random.Random(a.seed + 1).sample(rows, round(len(rows) * a.recheck))  # reshuffled: other neighbours
        write(out, "recheck", sample, a.size)
        print(f"{len(rows)} pairs from {len(a.runs)} runs, {len({r['id'] for r in rows})} of {len(ids)} questions, "
              f"{(len(rows) + a.size - 1) // a.size} packets; re-check {len(sample)} pairs; in {out}")
        return 0
    to = Path(a.to)
    seen = {(j["id"], j["section"], j.get("judge")) for j in read_jsonl(to)}
    n = bad = 0
    with open(to, "a", encoding="utf-8") as f:
        for path in sorted({p for g in a.judged for p in glob.glob(g)}):
            for j in read_jsonl(Path(path)):
                if j.get("verdict") not in VERDICTS:
                    bad += 1
                    continue
                if (j["id"], j["section"], j.get("judge")) in seen:
                    continue
                seen.add((j["id"], j["section"], j.get("judge")))
                f.write(json.dumps({"id": j["id"], "section": j["section"], "verdict": j["verdict"],
                                    "reason": j.get("reason", "")[:300], "judge": j.get("judge", "claude-local")}) + "\n")
                n += 1
    print(f"merged {n} verdicts into {to}" + (f"; {bad} lines without a yes/no verdict skipped" if bad else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
