"""Answer-set judging: can a builder get a full answer from everything one search returned? (25 Nov 2026)

The pool judge (pool_local.py) grades one passage at a time. This judge grades the whole set a search returns for a
question, so it sees what the pool judge cannot: law found but no guidance, two rules needed and only one found.
That is the difference between mixed search and lanes. Judged locally by Claude Code subagents (no model on AWS).

    python evals/golden/answer_set.py packets --out DIR                  # sample, sets, packets, DIR/keys.json
    python evals/golden/answer_set.py merge --out DIR                    # DIR/judged-*.jsonl -> pooled/answer-sets-v2.jsonl
    python evals/golden/answer_set.py score                              # per set: grades, and agreement on the re-check

Fairness: every set has the same number of passages (8 by default): mixed top 8, lanes 2 each, fused top 8.
Blind: passages of a set are shuffled and lanes are flattened, so the judge cannot tell which run made it. The key
from item to (question, set) stays in DIR/keys.json. Packets hold corpus text, so DIR is in the scratchpad, never git.
answer-sets-v2.jsonl holds ids, set names, grades and short reasons only.
"""

from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals" / "golden"))
import build as B  # noqa: E402
from pool_judge import section_text  # noqa: E402

RESULTS = ROOT / "evals" / "results"
OUT = ROOT / "evals" / "golden" / "pooled" / "answer-sets-v2.jsonl"
SETS = ["mixed8=B1-v2-mixed-k20-dev-dev:top:8", "lanes2=B2-v2-lanes-dev-dev:lanes:2", "fused8=B3-v2-fused-k20-dev-dev:top:8",
        "lanesfused2=B4-v2-lanes-fused-dev-dev:lanes:2"]


def sample(questions: list[dict], n: int, seed: int) -> list[str]:
    """n dev questions with expected sections, spread evenly over roles (round robin), random within a role."""
    by_role = collections.defaultdict(list)
    for q in sorted(questions, key=lambda q: q["id"]):
        if q.get("split") == "dev" and q.get("expected_sections"):
            by_role[q["role"]].append(q["id"])
    rng = random.Random(seed)
    for ids in by_role.values():
        rng.shuffle(ids)
    out, roles = [], sorted(by_role)
    while len(out) < n and any(by_role.values()):
        for r in roles:
            if by_role[r] and len(out) < n:
                out.append(by_role[r].pop())
    return out


def set_keys(row: dict, mode: str, n: int) -> list[str]:
    if mode == "lanes":
        return list(dict.fromkeys(x[0] for lane in row["lanes"].values() for x in lane["reranked"][:n]))
    return [x[0] for x in row["reranked"][:n]]


def packets_by_question(items: list[dict], size: int, rng: random.Random) -> list[list[dict]]:
    """Packets of `size` items, never two items of the same question in one packet (a judge must not compare sets)."""
    rng.shuffle(items)
    packets: list[list[dict]] = []
    for it in items:
        home = next((p for p in packets if len(p) < size and all(x["question"] != it["question"] for x in p)), None)
        if home is None:
            home = []
            packets.append(home)
        home.append(it)
    return packets


def write(out: Path, name: str, packets: list[list[dict]]) -> None:
    for i, p in enumerate(packets):
        with open(out / f"{name}-{i:03d}.jsonl", "w", encoding="utf-8") as f:
            for it in p:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")


def kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(g) / n) * (b.count(g) / n) for g in (0, 1, 2))
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("packets")
    p.add_argument("--out", required=True)
    p.add_argument("--sets", nargs="+", default=SETS, help="name=RUNFILE:top|lanes:N")
    p.add_argument("--n", type=int, default=80)
    p.add_argument("--size", type=int, default=4, help="items per packet")
    p.add_argument("--recheck", type=float, default=0.10)
    p.add_argument("--seed", type=int, default=25)
    p.add_argument("--chars", type=int, default=3000, help="passage text cut")
    m = sub.add_parser("merge")
    m.add_argument("--out", required=True, help="the packets DIR (keys.json and judged-*.jsonl)")
    sub.add_parser("score")
    a = ap.parse_args(argv)
    questions = {q["id"]: q for q in map(json.loads, (ROOT / "evals/golden/questions.jsonl").read_text(encoding="utf-8").splitlines())}

    if a.cmd == "packets":
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        ids = sample(list(questions.values()), a.n, a.seed)
        index = B.section_index()
        items, keys = [], {}
        rng = random.Random(a.seed)
        for spec in a.sets:
            name, rest = spec.split("=", 1)
            run, mode, n = rest.split(":")
            rows = {r["id"]: r for r in map(json.loads, (RESULTS / f"{run}.jsonl").read_text(encoding="utf-8").splitlines())}
            for qid in ids:
                got = set_keys(rows[qid], mode, int(n))
                rng.shuffle(got)
                item = hashlib.sha1(f"{a.seed}:{qid}:{name}".encode()).hexdigest()[:10]
                keys[item] = {"id": qid, "set": name, "sections": got}
                q = questions[qid]
                items.append({"item": item, "question": q["question"], "reference_answer": q.get("reference_answer"),
                              "passages": [{"source": k, "text": section_text(index, k)[:a.chars]} for k in got]})
        (out / "keys.json").write_text(json.dumps(keys, indent=1))
        main_packets = packets_by_question(list(items), a.size, random.Random(a.seed))
        write(out, "set", main_packets)
        sample_items = random.Random(a.seed + 1).sample(items, round(len(items) * a.recheck))
        re_packets = packets_by_question(sample_items, a.size, random.Random(a.seed + 2))
        write(out, "recheck", re_packets)
        print(f"{len(ids)} questions x {len(a.sets)} sets = {len(items)} items in {len(main_packets)} packets; "
              f"re-check {len(sample_items)} items in {len(re_packets)} packets; in {out}")
        return 0

    if a.cmd == "merge":
        out = Path(a.out)
        keys = json.loads((out / "keys.json").read_text())
        seen = {(j["id"], j["set"], j["judge"]) for j in map(json.loads, OUT.read_text().splitlines())} if OUT.exists() else set()
        n = 0
        with open(OUT, "a", encoding="utf-8") as f:
            for path in sorted(glob.glob(str(out / "judged-*.jsonl"))):
                for line in Path(path).read_text(encoding="utf-8").splitlines():
                    j = json.loads(line)
                    k = keys.get(j.get("item"))
                    if not k or j.get("grade") not in (0, 1, 2) or (k["id"], k["set"], j.get("judge")) in seen:
                        continue
                    seen.add((k["id"], k["set"], j.get("judge")))
                    f.write(json.dumps({"id": k["id"], "set": k["set"], "grade": j["grade"],
                                        "missing": (j.get("missing") or "")[:300], "reason": (j.get("reason") or "")[:300],
                                        "judge": j.get("judge")}) + "\n")
                    n += 1
        print(f"merged {n} judgments into {OUT}")
        return 0

    rows = [json.loads(x) for x in OUT.read_text().splitlines()] if OUT.exists() else []
    primary = [r for r in rows if r["judge"] == "opus-a"]
    by_set = collections.defaultdict(list)
    for r in primary:
        by_set[r["set"]].append(r["grade"])
    for s, g in sorted(by_set.items()):
        print(f"{s:8} n={len(g):3}  full (2) {g.count(2) / len(g):.0%}  partly (1) {g.count(1) / len(g):.0%}  "
              f"none (0) {g.count(0) / len(g):.0%}  mean {sum(g) / len(g):.2f}")
    grades = {(r["id"], r["set"], r["judge"]): r["grade"] for r in rows}
    for other in sorted({r["judge"] for r in rows} - {"opus-a"}):
        pairs = [(grades[(i, s, "opus-a")], g) for (i, s, j), g in grades.items() if j == other and (i, s, "opus-a") in grades]
        if pairs:
            a_, b_ = zip(*pairs)
            print(f"opus-a vs {other}: n={len(pairs)}, same grade {sum(x == y for x, y in pairs) / len(pairs):.0%}, "
                  f"kappa {kappa(list(a_), list(b_))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
