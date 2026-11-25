"""Pooled relevance judging, judged locally in Claude Code (25 Nov 2026; replaces the Bedrock judge in pool_judge.py).

The rule since ADR 0017: no model on AWS. So the judge is a Claude Code subagent, and this file only does the plain
parts: build the pool, write judging packets, read the judgments back.

    python evals/golden/pool_local.py packets --runs B1-v2-mixed-dev B2-v2-lanes-dev --k 10 --out DIR
    python evals/golden/pool_local.py merge --judged DIR/judged-*.jsonl     # -> pooled/judgments-v2.jsonl

The pool: every section in any run's re-ranked top k (k=10, and every lane's top k) for a dev question with
expected sections, that does not already touch an expected section. Holdout questions are never pooled. Packets
hold the question, the reference answer and the section text (corpus text: they stay in the scratchpad, never in
git). The judge grades blind (it does not know which run found a section), with the same scale as pool_judge.py:
2 = the section itself states the answer or the rule the reference answer rests on; 1 = related or partial;
0 = not relevant. judgments-v2.jsonl holds ids, section keys, grades and a one-sentence reason (no corpus text).
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "evals" / "golden"))
import build as B  # noqa: E402
import metrics as M  # noqa: E402
from pool_judge import SYSTEM, section_text  # noqa: E402,F401  (same scale and section text as before)

RESULTS = ROOT / "evals" / "results"
OUT = ROOT / "evals" / "golden" / "pooled" / "judgments-v2.jsonl"


def keys_of(row: dict, k: int) -> list[str]:
    out = [x[0] for x in (row.get("reranked") or [])[:k]]
    for lane in (row.get("lanes") or {}).values():
        out += [x[0] for x in (lane.get("reranked") or [])[:k]]
    return list(dict.fromkeys(out))


def pool(questions: dict, runs: list[str], k: int, done: set) -> list[tuple[str, str]]:
    pairs = []
    for run in runs:
        for line in (RESULTS / f"{run}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            q = questions.get(r["id"])
            if not q or q.get("split") != "dev" or not q.get("expected_sections"):
                continue
            for key in keys_of(r, k):
                if (r["id"], key) in done or any(M.touches(e, key) for e in q["expected_sections"]):
                    continue
                done.add((r["id"], key))
                pairs.append((r["id"], key))
    return pairs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("packets")
    p.add_argument("--runs", nargs="+", required=True)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--out", required=True)
    p.add_argument("--size", type=int, default=40, help="pairs per packet")
    m = sub.add_parser("merge")
    m.add_argument("--judged", nargs="+", required=True)
    a = ap.parse_args(argv)
    questions = {q["id"]: q for q in map(json.loads, (ROOT / "evals/golden/questions.jsonl").read_text(encoding="utf-8").splitlines())}
    if a.cmd == "packets":
        done = {(j["id"], j["section"]) for j in map(json.loads, OUT.read_text().splitlines())} if OUT.exists() else set()
        pairs = pool(questions, a.runs, a.k, done)
        index = B.section_index()
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        rows = []
        for qid, key in sorted(pairs):
            q = questions[qid]
            rows.append({"id": qid, "section": key, "question": q["question"], "reference_answer": q.get("reference_answer"),
                         "passage": section_text(index, key)[:6000]})
        for i in range(0, len(rows), a.size):
            with open(out / f"packet-{i // a.size:03d}.jsonl", "w", encoding="utf-8") as f:
                for r in rows[i:i + a.size]:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{len(rows)} pairs from {len(a.runs)} runs, {len({r['id'] for r in rows})} questions, "
              f"{(len(rows) + a.size - 1) // a.size} packets in {out}")
        return 0
    seen = {(j["id"], j["section"]) for j in map(json.loads, OUT.read_text().splitlines())} if OUT.exists() else set()
    n = 0
    with open(OUT, "a", encoding="utf-8") as f:
        for path in sorted({p for g in a.judged for p in glob.glob(g)}):
            for line in Path(path).read_text(encoding="utf-8").splitlines():
                j = json.loads(line)
                if j.get("grade") not in (0, 1, 2) or (j["id"], j["section"]) in seen:
                    continue
                seen.add((j["id"], j["section"]))
                f.write(json.dumps({"id": j["id"], "section": j["section"], "grade": j["grade"],
                                    "reason": j.get("reason", "")[:300], "judge": j.get("judge", "claude-local")}) + "\n")
                n += 1
    print(f"merged {n} judgments into {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
