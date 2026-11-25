"""Paired test between runs on the same dev questions: is a difference in "found" real or noise? (25 Nov 2026)

    python evals/paired.py B1-v2-mixed-k20-dev-dev B3-v2-fused-k20-dev-dev B6-v2-fused-plainrr-dev-dev --n 8

"Found": in the first n passages (lanes: n/4 per lane, flattened) there is an expected section or a section the
pool judge accepted for that question ("also_acceptable" in golden questions.jsonl, dev only; see
evals/experiments/L1-pooled-labels.md). This is the only meaning of "found"; gate.py uses it too.

Questions from one source document move together (93 documents for 299 dev questions), so the test works on
documents, not questions (evals/knowledge/eval-practice-assessment.md, topic 3):
- p: paired permutation test that flips the sign of each document's summed difference at random;
- ci95: paired bootstrap of the difference that resamples whole documents.
With more than two runs every pair is compared and p_holm is the Holm-corrected p (topic 6): read p_holm.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
QUESTIONS = HERE / "golden" / "questions.jsonl"


@lru_cache(maxsize=1)
def acceptable() -> dict[str, tuple[str, ...]]:
    """Sections the pool judge accepted per question (dev only)."""
    if not QUESTIONS.exists():
        return {}
    rows = map(json.loads, QUESTIONS.read_text(encoding="utf-8").splitlines())
    return {q["id"]: tuple(q.get("also_acceptable") or ()) for q in rows}


def found(row: dict, n: int) -> bool:
    ok = list(row["expected"]) + list(acceptable().get(row["id"], ()))
    if row.get("lanes") and row.get("lane_merge", "slots") == "slots":
        per = n // len(row["lanes"])
        keys = list(dict.fromkeys(x[0] for lane in row["lanes"].values() for x in lane["reranked"][:per]))
        return M.recall_at(ok, keys, len(keys) or 1) > 0
    return M.recall_at(ok, row["top5"], n) > 0


def doc(row: dict) -> str:
    """The cluster: the source document of the first expected section."""
    return row["expected"][0].split(":")[0]


def compare(a: list[bool], b: list[bool], docs: list[str] | None = None, seed: int = 1, draws: int = 10000) -> dict:
    """a minus b, question by question, tested by document (docs=None: each question its own document)."""
    d = [int(x) - int(y) for x, y in zip(a, b)]
    n = len(d)
    groups: dict[str, list[int]] = {}
    for i, x in enumerate(d):
        groups.setdefault(docs[i] if docs else str(i), []).append(x)
    sums = [sum(g) for g in groups.values()]
    sizes = [len(g) for g in groups.values()]
    obs = abs(sum(sums))
    rng = random.Random(seed)
    nz = [s for s in sums if s]
    extreme = sum(abs(sum(s if rng.random() < 0.5 else -s for s in nz)) >= obs for _ in range(draws)) if obs else draws
    k = len(sums)
    boots = []
    for _ in range(draws):
        pick = [rng.randrange(k) for _ in range(k)]
        boots.append(sum(sums[j] for j in pick) / sum(sizes[j] for j in pick))
    boots.sort()
    return {"diff": round(sum(d) / n, 3), "only_a": d.count(1), "only_b": d.count(-1), "documents": k,
            "p": round((extreme + 1) / (draws + 1), 4),
            "ci95": [round(boots[int(draws * 0.025)], 3), round(boots[int(draws * 0.975) - 1], 3)]}


def holm(ps: list[float]) -> list[float]:
    """Holm step-down adjusted p values, same order as given."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = round(run, 4)
    return out


def load(run: str) -> dict[str, dict]:
    return {r["id"]: r for r in map(json.loads, (RESULTS / f"{run}.jsonl").read_text(encoding="utf-8").splitlines())
            if r.get("expected")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="two or more run names (results file without .jsonl)")
    ap.add_argument("--n", type=int, default=8)
    a = ap.parse_args(argv)
    if len(a.runs) < 2:
        ap.error("give at least two runs")
    rows = {r: load(r) for r in a.runs}
    ids = sorted(set.intersection(*(set(v) for v in rows.values())))
    docs = [doc(rows[a.runs[0]][q]) for q in ids]
    out = []
    for x, y in itertools.combinations(a.runs, 2):
        r = compare([found(rows[x][q], a.n) for q in ids], [found(rows[y][q], a.n) for q in ids], docs)
        out.append({"a": x, "b": y, "questions": len(ids), "n": a.n, **r})
    for o, ph in zip(out, holm([o["p"] for o in out])):
        o["p_holm"] = ph
        print(json.dumps(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
