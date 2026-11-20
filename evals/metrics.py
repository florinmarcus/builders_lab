"""Retrieval metrics (agentic-rag-lab method, research/methods/agentic-rag-lab-lessons.md section 2).

Scoring uses section keys ("<source_id>:<section_id>"), never chunk text, so any chunker can be scored
against the same labels. A question counts as found if ANY expected section is in the list.
"""

from __future__ import annotations

import math


def section_key(source_id: str, section_id: str) -> str:
    """A table row chunk (#row-3) or a split part (#part-2) belongs to its section."""
    return f"{source_id}:{section_id.split('#')[0]}"


def touches(expected: str, got: str) -> bool:
    """A hit if the retrieved section is the expected one, a part of it or the section it belongs to
    ("touches the section"): car2012:regulation-7 and car2012:regulation-7-1 touch; para-1 and para-12 do not."""
    if expected == got:
        return True
    es, _, ex = expected.partition(":")
    gs, _, gx = got.partition(":")
    return es == gs and (gx.startswith(ex + "-") or ex.startswith(gx + "-"))


def _hit(expected: list[str], g: str) -> bool:
    return any(touches(e, g) for e in expected)


def recall_at(expected: list[str], got: list[str], k: int) -> float:
    return 1.0 if any(_hit(expected, g) for g in got[:k]) else 0.0


def reciprocal_rank(expected: list[str], got: list[str], k: int = 5) -> float:
    for i, g in enumerate(got[:k], start=1):
        if _hit(expected, g):
            return 1.0 / i
    return 0.0


def ndcg_at(expected: list[str], got: list[str], k: int = 5) -> float:
    """Graded: the first expected section has grade 2, the others grade 1."""
    grade = {e: (2 if i == 0 else 1) for i, e in enumerate(expected)}
    used: set[str] = set()
    dcg = 0.0
    for i, g in enumerate(got[:k], start=1):
        for e in expected:
            if e not in used and touches(e, g):
                used.add(e)
                dcg += grade[e] / math.log2(i + 1)
                break
    ideal = sorted(grade.values(), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 1) for i, g in enumerate(ideal, start=1))
    return dcg / idcg if idcg else 0.0


def all_at(expected: list[str], got: list[str], k: int = 5) -> float:
    """Every expected section in the top k: the multi-rule score."""
    return 1.0 if expected and all(any(touches(e, g) for g in got[:k]) for e in expected) else 0.0


def mcnemar(a: list[bool], b: list[bool]) -> dict:
    """Question-by-question comparison of two runs on the same questions. (b-c)^2/(b+c); above 4 is clear."""
    both = sum(1 for x, y in zip(a, b) if x and y)
    only_a = sum(1 for x, y in zip(a, b) if x and not y)
    only_b = sum(1 for x, y in zip(a, b) if y and not x)
    neither = sum(1 for x, y in zip(a, b) if not x and not y)
    stat = (only_a - only_b) ** 2 / (only_a + only_b) if only_a + only_b else 0.0
    return {"both": both, "only_a": only_a, "only_b": only_b, "neither": neither, "chi2": round(stat, 2)}


def summarise(rows: list[dict]) -> dict:
    """Means over rows that have expected sections. Each row: expected, candidates, top5, kind, multi_rule."""
    scored = [r for r in rows if r.get("expected")]
    if not scored:
        return {"questions": 0}
    mean = lambda f: round(sum(f(r) for r in scored) / len(scored), 4)  # noqa: E731
    out = {
        "questions": len(scored),
        "recall@50": mean(lambda r: recall_at(r["expected"], r["candidates"], 50)),
        "recall@5": mean(lambda r: recall_at(r["expected"], r["top5"], 5)),
        "recall@5_before_rerank": mean(lambda r: recall_at(r["expected"], r["candidates"], 5)),
        "mrr@5": mean(lambda r: reciprocal_rank(r["expected"], r["top5"])),
        "ndcg@5": mean(lambda r: ndcg_at(r["expected"], r["top5"])),
    }
    multi = [r for r in scored if r.get("multi_rule") and len(r["expected"]) > 1]
    if multi:
        out["all@5_multi"] = round(sum(all_at(r["expected"], r["top5"]) for r in multi) / len(multi), 4)
    by_kind: dict[str, list] = {}
    for r in scored:
        by_kind.setdefault(r.get("kind", "?"), []).append(recall_at(r["expected"], r["top5"], 5))
    out["recall@5_by_kind"] = {k: round(sum(v) / len(v), 4) for k, v in sorted(by_kind.items())}
    by_role: dict[str, list] = {}
    for r in scored:
        by_role.setdefault(r.get("role", "?"), []).append(recall_at(r["expected"], r["top5"], 5))
    out["recall@5_by_role"] = {k: round(sum(v) / len(v), 4) for k, v in sorted(by_role.items())}
    lat = sorted(r.get("latency_ms", 0) for r in scored)
    out["latency_p50_ms"] = lat[len(lat) // 2]
    out["latency_p95_ms"] = lat[min(len(lat) - 1, int(len(lat) * 0.95))]
    return out
