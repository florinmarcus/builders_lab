"""Regression gate (evals/gate.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import gate as G  # noqa: E402


def base(found):
    return {"run": "b", "n": 8, "found": found}


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
    assert len(ids) == 6 and all(b["found"][q] for q in ids)
    assert sorted(rows[q]["role"] for q in ids) == ["a"] * 3 + ["b"] * 3


def test_loss_from_one_document_is_not_called_real():
    old = {f"q{i}": True for i in range(100)}
    new = {q: i >= 12 for i, q in enumerate(old)}
    docs = {q: ("d0" if i < 12 else q) for i, q in enumerate(old)}
    v = G.check(dict(base(old), docs=docs), new, [])
    assert not any("not luck" in x for x in v["fails"])
    assert any("not luck" in x for x in G.check(base(old), new, [])["fails"])
