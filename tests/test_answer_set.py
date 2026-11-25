"""answer_set.py: the plain parts of answer-set judging (sample, sets, packets, agreement)."""
import importlib.util
import random
from pathlib import Path

spec = importlib.util.spec_from_file_location("answer_set", Path(__file__).resolve().parents[1] / "evals/golden/answer_set.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


def test_sample_spreads_over_roles_and_skips_holdout():
    qs = [{"id": f"{r}-{i}", "role": r, "split": "dev", "expected_sections": ["x:1"]} for r in "abc" for i in range(10)]
    qs += [{"id": "h-1", "role": "a", "split": "holdout", "expected_sections": ["x:1"]},
           {"id": "n-1", "role": "a", "split": "dev", "expected_sections": []}]
    got = A.sample(qs, 9, 1)
    assert len(got) == 9 and {g.split("-")[0] for g in got} == {"a", "b", "c"}
    assert "h-1" not in got and "n-1" not in got
    assert got == A.sample(qs, 9, 1)


def test_set_keys_same_size_for_mixed_and_lanes():
    row = {"reranked": [[f"m:{i}", 1, ""] for i in range(20)],
           "lanes": {ln: {"reranked": [[f"{ln}:{i}", 1, ""] for i in range(5)]} for ln in ("law", "ad", "acop", "g")}}
    assert len(A.set_keys(row, "top", 8)) == 8 == len(A.set_keys(row, "lanes", 2))


def test_packets_never_hold_one_question_twice():
    items = [{"item": f"{q}{s}", "question": q} for q in "abcdefgh" for s in range(3)]
    packets = A.packets_by_question(items, 4, random.Random(3))
    assert sum(map(len, packets)) == 24
    assert all(len({x["question"] for x in p}) == len(p) for p in packets)


def test_kappa():
    assert A.kappa([0, 1, 2, 2], [0, 1, 2, 2]) == 1.0
    assert A.kappa([0, 1, 2, 2], [2, 2, 0, 1]) < 0
