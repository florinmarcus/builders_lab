"""Paired test between two runs on the same dev questions: is a difference in "found" real or noise? (25 Nov 2026)

    python evals/paired.py B1-v2-mixed-k20-dev-dev B2-v2-lanes-dev-dev --n 8

"Found": some expected section in the first n passages (lanes: n/4 per lane, flattened). Counts the questions only
one run found, an exact sign test (McNemar) on them, and a bootstrap 95% interval for the difference.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"


def found(row: dict, n: int) -> bool:
    if row.get("lanes"):
        per = n // len(row["lanes"])
        keys = list(dict.fromkeys(x[0] for lane in row["lanes"].values() for x in lane["reranked"][:per]))
        return M.recall_at(row["expected"], keys, len(keys) or 1) > 0
    return M.recall_at(row["expected"], row["top5"], n) > 0


def sign_test(b: int, c: int) -> float:
    """Two-sided exact p for b against c discordant questions."""
    if b + c == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(b + c, i) for i in range(min(b, c) + 1)) / 2 ** (b + c))


def compare(a: list[bool], b: list[bool], seed: int = 1, draws: int = 2000) -> dict:
    d = [int(x) - int(y) for x, y in zip(a, b)]
    rng = random.Random(seed)
    boots = sorted(sum(d[rng.randrange(len(d))] for _ in d) / len(d) for _ in range(draws))
    only_a, only_b = d.count(1), d.count(-1)
    return {"diff": round(sum(d) / len(d), 3), "only_a": only_a, "only_b": only_b, "p": round(sign_test(only_a, only_b), 3),
            "ci95": [round(boots[int(draws * 0.025)], 3), round(boots[int(draws * 0.975) - 1], 3)]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--n", type=int, default=8)
    a = ap.parse_args(argv)
    load = lambda f: {r["id"]: r for r in map(json.loads, (RESULTS / f"{f}.jsonl").read_text().splitlines()) if r.get("expected")}  # noqa: E731
    ra, rb = load(a.run_a), load(a.run_b)
    ids = sorted(set(ra) & set(rb))
    print(json.dumps({"questions": len(ids), "n": a.n, **compare([found(ra[q], a.n) for q in ids], [found(rb[q], a.n) for q in ids])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
