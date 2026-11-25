"""C1: Opus from memory (no tools) against Opus with the live regulations connector (25 Nov 2026).

    python evals/closed_book.py sample  --n 60 --out DIR   # stratified dev sample, batches for the answer agents
    python evals/closed_book.py packets --out DIR          # blind judge packets (answers shuffled as X / Y)
    python evals/closed_book.py score   --out DIR          # unblind, score, paired test -> DIR/summary.json

The answers and the judging are done by Opus 5.5 agents in a Claude Code session (Bedrock Opus is not allowed for
the eval user). Agent A gets no tools; agent B gets search_regulations and lookup_terms on the live server. One
Opus judge marks both answers to a question side by side, without knowing which agent wrote which. DIR holds the
answers and packets: keep it out of git (answers can quote corpus passages). Dev questions only, never the holdout.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evals" / "golden" / "questions.jsonl"
RULES = ROOT / "evals" / "golden" / "pooled" / "rules.jsonl"
SEED = 20261125
MIX = {"answerable": 0.70, "negative": 0.14, "out_of_scope": 0.10, "underspecified": 0.06}
BATCH = 15


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sample(n: int, out: Path) -> None:
    qs = [q for q in load(GOLDEN) if q["split"] == "dev"]
    rnd = random.Random(SEED)
    picked = []
    for kind, share in MIX.items():
        pool = sorted((q for q in qs if q["kind"] == kind), key=lambda q: q["id"])
        picked += rnd.sample(pool, round(n * share))
    rnd.shuffle(picked)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sample.json").write_text(json.dumps([q["id"] for q in picked], indent=1))
    for i in range(0, len(picked), BATCH):
        batch = [{"id": q["id"], "question": q["question"]} for q in picked[i:i + BATCH]]
        (out / f"batch-{i // BATCH + 1:02d}.json").write_text(json.dumps(batch, indent=1, ensure_ascii=False))
    print(f"{len(picked)} questions:", dict(collections.Counter(q["kind"] for q in picked)))


def answers(out: Path, agent: str) -> dict[str, str]:
    got = {}
    for f in sorted(out.glob(f"answers-{agent}-*.json")):
        for a in json.loads(f.read_text()):
            got[a["id"]] = a["answer"]
    return got


def packets(out: Path) -> None:
    ids = json.loads((out / "sample.json").read_text())
    qs = {q["id"]: q for q in load(GOLDEN)}
    rules = {r["id"]: r["rules"] for r in load(RULES)}
    a, b = answers(out, "A"), answers(out, "B")
    missing = [i for i in ids if i not in a or i not in b]
    if missing:
        raise SystemExit(f"answers missing for {len(missing)} questions: {missing[:5]}")
    rnd = random.Random(SEED + 1)
    key, items = {}, []
    for i in ids:
        flip = rnd.random() < 0.5
        key[i] = {"X": "B" if flip else "A", "Y": "A" if flip else "B"}
        q = qs[i]
        items.append({"id": i, "kind": q["kind"], "question": q["question"], "reference_answer": q["reference_answer"],
                      "rules": rules.get(i, []), "X": b[i] if flip else a[i], "Y": a[i] if flip else b[i]})
    (out / "key.json").write_text(json.dumps(key, indent=1))
    for n in range(0, len(items), BATCH):
        (out / f"judge-in-{n // BATCH + 1:02d}.json").write_text(json.dumps(items[n:n + BATCH], indent=1,
                                                                              ensure_ascii=False))
    print(f"{len(items)} judge items in {math.ceil(len(items) / BATCH)} packets")


def passed(v: dict) -> bool:
    return v["correctness"] >= 4 and not v["serious_error"]


def mcnemar(only_a: int, only_b: int) -> float:
    """Exact two-sided McNemar p value (binomial on the discordant pairs)."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    k = min(only_a, only_b)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def score(out: Path) -> None:
    key = json.loads((out / "key.json").read_text())
    qs = {q["id"]: q for q in load(GOLDEN)}
    rules = {r["id"]: r["rules"] for r in load(RULES)}
    rows = []
    for f in sorted(out.glob("judge-out-*.json")):
        for j in json.loads(f.read_text()):
            for label in ("X", "Y"):
                v = j[label]
                n_rules = len(rules.get(j["id"], []))
                stated = {r for r in v.get("rules_stated", []) if 1 <= r <= n_rules}
                rows.append({"id": j["id"], "kind": qs[j["id"]]["kind"], "agent": key[j["id"]][label],
                             "correctness": v["correctness"], "serious_error": bool(v["serious_error"]),
                             "wrong_claims": len(v.get("wrong_claims") or []),
                             "made_up_source": v.get("made_up_source") is True,
                             "rule_coverage": len(stated) / n_rules if n_rules else None, "pass": passed(v)})
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["id"]][r["agent"]] = r

    def stats(agent: str, kind: str | None = None) -> dict:
        rs = [r for r in rows if r["agent"] == agent and (kind is None or r["kind"] == kind)]
        cov = [r["rule_coverage"] for r in rs if r["rule_coverage"] is not None]
        return {"n": len(rs), "pass": round(sum(r["pass"] for r in rs) / len(rs), 2),
                "correctness": round(sum(r["correctness"] for r in rs) / len(rs), 2),
                "rule_coverage": round(sum(cov) / len(cov), 2) if cov else None,
                "serious_errors": sum(r["serious_error"] for r in rs),
                "wrong_claims": sum(r["wrong_claims"] for r in rs),
                "made_up_sources": sum(r["made_up_source"] for r in rs)}

    pairs = [p for p in by.values() if "A" in p and "B" in p]
    only_a = sum(p["A"]["pass"] and not p["B"]["pass"] for p in pairs)
    only_b = sum(p["B"]["pass"] and not p["A"]["pass"] for p in pairs)
    summary = {"questions": len(pairs),
               "A_memory": stats("A"), "B_connector": stats("B"),
               "by_kind": {k: {"A": stats("A", k), "B": stats("B", k)} for k in MIX if any(r["kind"] == k for r in rows)},
               "paired_pass": {"only_A": only_a, "only_B": only_b, "both": sum(p["A"]["pass"] and p["B"]["pass"]
                                                                                for p in pairs),
                               "mcnemar_p": round(mcnemar(only_a, only_b), 4)}}
    (out / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", choices=["sample", "packets", "score"])
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    {"sample": lambda: sample(args.n, args.out), "packets": lambda: packets(args.out),
     "score": lambda: score(args.out)}[args.step]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
