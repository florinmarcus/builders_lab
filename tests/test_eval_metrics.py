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


def test_merge_interleaves_candidates_and_keeps_best_score_per_section():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
    import retrieval as R
    a = (["s:1", "s:2", "s:3"], [["s:1", 0.2, "c1"], ["s:2", 0.1, "c2"]])
    b = (["s:4", "s:1"], [["s:4", 0.5, "c4"], ["s:1", 0.3, "c1b"]])
    cands, rr = R.merge([a, b])
    assert cands == ["s:1", "s:4", "s:2", "s:3"]
    assert [x[0] for x in rr] == ["s:4", "s:1", "s:2"] and rr[1][2] == "c1b"
    assert R.merge([a]) == (a[0], a[1])


def test_lanes_of_finds_the_lane_of_a_parent_or_a_part():
    import retrieval as R
    keys = {"car2012:regulation-20": {"law"}, "hse-l143:para-12": {"acop"}, "hse-l143:regulation-5-1": {"law"}}
    assert R.lanes_of("car2012:regulation-20-4", keys) == ["law"]  # a part of a whole-regulation chunk
    assert R.lanes_of("hse-l143:para-12", keys) == ["acop"]
    assert R.lanes_of("hse-l143:regulation-5", keys) == ["law"]
    assert R.lanes_of("missing:x", keys) == []


def test_lane_scores_check_each_label_in_its_own_lane():
    import retrieval as R
    lane = lambda top: {"candidates": top, "reranked": [[k, 0.5, "c"] for k in top]}  # noqa: E731
    rows = [{"expected": ["a:law-1", "b:para-1"], "expected_lanes": {"a:law-1": ["law"], "b:para-1": ["guidance"]},
             "lanes": {"law": lane(["a:law-1"]), "approved-document": lane([]), "acop": lane([]),
                       "guidance": lane(["b:other", "b:x", "b:para-1"])}}]
    s = R.lane_scores(rows, 2)
    assert s["law"]["recall@2"] == 1.0 and s["guidance"]["recall@2"] == 0.0 and s["guidance"]["recall@5"] == 1.0
    assert s["approved-document"]["questions"] == 0
    assert s["any"] == 1.0 and s["every_lane"] == 0.0


def test_summarise_counts_accepted_sections_as_found_but_not_for_ndcg():
    row = {"expected": ["law:s-1"], "accepted": ["guide:p-3"], "candidates": ["guide:p-3"], "top5": ["guide:p-3"]}
    s = M.summarise([row])
    assert s["recall@5"] == 1.0 and s["mrr@5"] == 1.0 and s["ndcg@5"] == 0.0 and s["with_accepted"] == 1
