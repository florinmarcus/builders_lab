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

"Rule coverage" (--metric coverage, 25 Nov 2026): the share of a question's rules (golden/pooled/rules.jsonl) that
the first n passages state between them, by the pool judge's rule-by-rule verdicts (golden/pooled/judgments.jsonl).
Two of three rules covered scores 0.67. It is nugget recall (TREC RAG) or context recall (RAGAS) under our name. Only
questions with rules count; a shown passage with no verdict states no rule and is reported as unjudged. It replaces
"found" once every dev question has rules (S153).
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
RULES = HERE / "golden" / "pooled" / "rules.jsonl"
JUDGMENTS = HERE / "golden" / "pooled" / "judgments.jsonl"


@lru_cache(maxsize=1)
def acceptable() -> dict[str, tuple[str, ...]]:
    """Sections the pool judge accepted per question (dev only)."""
    if not QUESTIONS.exists():
        return {}
    rows = map(json.loads, QUESTIONS.read_text(encoding="utf-8").splitlines())
    return {q["id"]: tuple(q.get("also_acceptable") or ()) for q in rows}


def shown(row: dict, n: int) -> list[str]:
    """The first n passages a run showed (lanes: n/4 per lane, flattened)."""
    if row.get("lanes") and row.get("lane_merge", "slots") == "slots":
        per = n // len(row["lanes"])
        return list(dict.fromkeys(x[0] for lane in row["lanes"].values() for x in lane["reranked"][:per]))
    return list(row["top5"][:n])


def found(row: dict, n: int) -> bool:
    ok = list(row["expected"]) + list(acceptable().get(row["id"], ()))
    keys = shown(row, n)
    return M.recall_at(ok, keys, len(keys) or 1) > 0


@lru_cache(maxsize=1)
def rule_counts() -> dict[str, int]:
    """Number of rules per question (dev questions that have rules)."""
    if not RULES.exists():
        return {}
    return {r["id"]: len(r["rules"]) for r in map(json.loads, RULES.read_text(encoding="utf-8").splitlines())}


@lru_cache(maxsize=1)
def rules_stated() -> dict[tuple[str, str], frozenset]:
    """(question, section) -> the rule numbers the primary pool judge says the passage states (in scope only)."""
    if not JUDGMENTS.exists():
        return {}
    out = {}
    for j in map(json.loads, JUDGMENTS.read_text(encoding="utf-8").splitlines()):
        out[(j["id"], j["section"])] = frozenset(j.get("rules_stated") or []) if j.get("scope_match") == "yes" \
            else frozenset()
    return out


def coverage(row: dict, n: int) -> tuple[float, int] | None:
    """(share of the question's rules stated by the first n passages, passages shown with no verdict), or None if
    the question has no rules."""
    total = rule_counts().get(row["id"])
    if not total:
        return None
    verdicts = rules_stated()
    keys = shown(row, n)
    got = set().union(*(verdicts.get((row["id"], k), frozenset()) for k in keys))
    return len(got & set(range(1, total + 1))) / total, sum((row["id"], k) not in verdicts for k in keys)


def doc(row: dict) -> str:
    """The cluster: the source document of the first expected section."""
    return row["expected"][0].split(":")[0]


def compare(a: list[float], b: list[float], docs: list[str] | None = None, seed: int = 1, draws: int = 10000) -> dict:
    """a minus b, question by question (found as 0/1, or rule coverage), tested by document (docs=None: each
    question its own document)."""
    d = [float(x) - float(y) for x, y in zip(a, b)]
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
    return {"diff": round(sum(d) / n, 3), "only_a": sum(x > 0 for x in d), "only_b": sum(x < 0 for x in d), "documents": k,
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
    ap.add_argument("--metric", choices=("found", "coverage"), default="found",
                    help="coverage: rule coverage, on the questions that have rules")
    a = ap.parse_args(argv)
    if len(a.runs) < 2:
        ap.error("give at least two runs")
    rows = {r: load(r) for r in a.runs}
    ids = sorted(set.intersection(*(set(v) for v in rows.values())))
    if a.metric == "coverage":
        ids = [q for q in ids if q in rule_counts()]
        score = {r: {q: coverage(rows[r][q], a.n) for q in ids} for r in a.runs}
        for r in a.runs:
            unjudged = sum(c[1] for c in score[r].values())
            print(json.dumps({"run": r, "questions": len(ids), "n": a.n,
                              "coverage": round(sum(c[0] for c in score[r].values()) / max(len(ids), 1), 3),
                              "all_rules": sum(c[0] == 1 for c in score[r].values()), "unjudged_passages": unjudged}))
        value = lambda r, q: score[r][q][0]  # noqa: E731
    else:
        value = lambda r, q: found(rows[r][q], a.n)  # noqa: E731
    docs = [doc(rows[a.runs[0]][q]) for q in ids]
    out = []
    for x, y in itertools.combinations(a.runs, 2):
        r = compare([value(x, q) for q in ids], [value(y, q) for q in ids], docs)
        out.append({"a": x, "b": y, "metric": a.metric, "questions": len(ids), "n": a.n, **r})
    for o, ph in zip(out, holm([o["p"] for o in out])):
        o["p_holm"] = ph
        print(json.dumps(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
