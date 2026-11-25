"""Regression gate (evals/gate.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import gate as G  # noqa: E402


def base(cov):
    """Booleans stand for all rules covered (1.0) or none (0.0)."""
    return {"run": "b", "n": 8, "coverage": {q: float(v) for q, v in cov.items()}}


def test_same_run_passes():
    f = {f"q{i}": i % 3 != 0 for i in range(100)}
    assert G.check(base(f), dict(f), [])["fails"] == []


def test_real_loss_fails():
    old = {f"q{i}": True for i in range(100)}
    new = {q: i >= 20 for i, q in enumerate(old)}
    v = G.check(base(old), new, [])
    assert len(v["lost"]) == 20 and any("not luck" in x for x in v["fails"]) and any("score drops" in x for x in v["fails"])


def test_small_swap_passes_but_must_pass_loss_fails():
    old = {f"q{i}": i < 50 for i in range(100)}
    new = dict(old, q0=False, q60=True)
    assert G.check(base(old), new, [])["fails"] == []
    assert any("must-pass" in x for x in G.check(base(old), new, ["q0"])["fails"])


def test_missing_questions_fail():
    old = {"q1": True, "q2": False}
    assert any("not in the new run" in x for x in G.check(base(old), {"q1": True}, [])["fails"])


def test_must_pass_picks_found_questions_per_role():
    rows = {f"q{i}": {"role": "ab"[i % 2], "kind": "answerable"} for i in range(20)}
    b = base({q: int(q[1:]) < 16 for q in rows})
    ids = G.pick_must_pass(b, rows, per_role=3)
    assert len(ids) == 6 and all(b["coverage"][q] == 1 for q in ids)
    assert sorted(rows[q]["role"] for q in ids) == ["a"] * 3 + ["b"] * 3


def test_loss_from_one_document_is_not_called_real():
    old = {f"q{i}": True for i in range(100)}
    new = {q: i >= 12 for i, q in enumerate(old)}
    docs = {q: ("d0" if i < 12 else q) for i, q in enumerate(old)}
    v = G.check(dict(base(old), docs=docs), new, [])
    assert not any("not luck" in x for x in v["fails"])
    assert any("not luck" in x for x in G.check(base(old), new, [])["fails"])


def test_partial_coverage_counts_and_unjudged_passages_fail():
    old = {f"q{i}": 1.0 for i in range(10)}
    new = dict(old, q0=0.5, q1=0.5)
    v = G.check(base(old), new, [])
    assert v["lost"] == ["q0", "q1"] and v["score_new"] == 0.9 and any("score drops" in x for x in v["fails"])
    assert any("no pool verdict" in x for x in G.check(base(old), dict(old), [], unjudged=3)["fails"])


def test_coverage_map_skips_questions_without_rules(monkeypatch):
    monkeypatch.setattr(G.P, "rule_counts", lambda: {"q1": 2})
    monkeypatch.setattr(G.P, "rules_stated", lambda: {("q1", "a:1"): frozenset({2})})
    rows = {"q1": {"id": "q1", "expected": ["a:1"], "top5": ["a:1", "b:1"]},
            "q2": {"id": "q2", "expected": ["a:1"], "top5": ["a:1"]}}
    assert G.coverage_map(rows, 8) == ({"q1": 0.5}, 1)
