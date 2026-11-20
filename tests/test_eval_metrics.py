"""Retrieval metrics (evals/metrics.py)."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import metrics as M  # noqa: E402


def test_section_key_folds_rows_and_parts_into_their_section():
    assert M.section_key("adb", "table-c1#row-3") == "adb:table-c1"
    assert M.section_key("car2012", "regulation-7") == "car2012:regulation-7"


def test_recall_mrr_ndcg_all():
    exp = ["a", "b"]
    assert M.recall_at(exp, ["x", "b", "y"], 5) == 1.0 and M.recall_at(exp, ["x", "y"], 5) == 0.0
    assert M.recall_at(exp, ["x", "y", "z", "w", "v", "a"], 5) == 0.0  # 6th place is outside the top 5
    assert M.reciprocal_rank(exp, ["x", "b"]) == 0.5
    assert math.isclose(M.ndcg_at(exp, ["a", "b"]), 1.0)
    assert M.ndcg_at(exp, ["b", "a"]) < 1.0  # the first expected section is worth more
    assert M.all_at(exp, ["a", "x", "b"]) == 1.0 and M.all_at(exp, ["a", "x"]) == 0.0


def test_mcnemar_counts_and_statistic():
    r = M.mcnemar([True, True, False, False, True], [True, False, True, False, False])
    assert (r["both"], r["only_a"], r["only_b"], r["neither"]) == (1, 2, 1, 1)
    assert r["chi2"] == round((2 - 1) ** 2 / 3, 2)


def test_summarise_skips_questions_without_sections_and_breaks_down_by_kind():
    rows = [
        {"expected": ["a"], "candidates": ["x", "a"], "top5": ["a"], "kind": "answerable", "role": "asbestos", "latency_ms": 100},
        {"expected": ["b"], "candidates": ["x"], "top5": ["x"], "kind": "negative", "role": "money", "latency_ms": 300},
        {"expected": [], "candidates": [], "top5": [], "kind": "out_of_scope"},
    ]
    s = M.summarise(rows)
    assert s["questions"] == 2 and s["recall@5"] == 0.5 and s["recall@50"] == 0.5
    assert s["recall@5_by_kind"] == {"answerable": 1.0, "negative": 0.0}
    assert s["recall@5_before_rerank"] == 0.5  # "a" is 2nd among the candidates


def test_touches_the_section_rule():
    assert M.touches("car2012:regulation-7", "car2012:regulation-7-1")      # a clause of the regulation
    assert M.touches("car2012:regulation-7-1", "car2012:regulation-7")      # the regulation holding the clause
    assert not M.touches("adb:para-1", "adb:para-12")
    assert not M.touches("car2012:regulation-7", "cdm2015:regulation-7")
    assert M.recall_at(["car2012:regulation-7"], ["x:y", "car2012:regulation-7-2"], 5) == 1.0


def test_in_corpus_needs_every_expected_source_loaded():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
    import retrieval as R
    assert R.in_corpus(["car2012:regulation-8", "hse-l143:para-1"], {"car2012", "hse-l143"})
    assert not R.in_corpus(["car2012:regulation-8", "hse-l143:para-1"], {"car2012"})
    assert not R.in_corpus([], {"car2012"})


def test_floor_keeps_rerank_order_and_drops_low_scores():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
    import retrieval as R
    rr = [["a:1", 0.9, "c1"], ["a:2", 0.01, "c2"], ["a:3", 0.002, "c3"]]
    assert R.apply_floor(rr, 0.05) == (["a:1"], [0.9], ["c1"])
    assert R.apply_floor(rr, 0.0)[0] == ["a:1", "a:2", "a:3"]
    assert R.apply_floor([["a:1", None, "c1"]], 0.05)[0] == ["a:1"]  # no re-rank: nothing to drop
