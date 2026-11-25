"""B4: agent queries in every lane (evals/retrieval.py lanes_search with extra)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import retrieval as R  # noqa: E402

from system.rag import pgsearch as P  # noqa: E402


class FakeSearch:
    LANES = {"law": ["law"], "guidance": ["guidance"]}
    rrf = staticmethod(P.rrf)
    one_per_section = staticmethod(P.one_per_section)

    def __init__(self):
        self.reranked_with = []

    def embed_question(self, q):
        return [len(q)]

    def candidates(self, q, url=None, n=None, weights=None, vector=None):
        lane = weights[0]
        if q.startswith("rewrite"):
            return [{"id": f"{lane}-r", "source_id": lane, "section_id": "r", "embed_text": "r"}]
        return [{"id": f"{lane}-q", "source_id": lane, "section_id": "q", "embed_text": "q"}]

    def rerank(self, q, texts, k):
        self.reranked_with.append(q)
        return [(i, 1.0 - i / 10) for i in range(min(k, len(texts)))]


def test_lanes_without_extra_unchanged():
    s = FakeSearch()
    out = R.lanes_search("question", s, "", 50, True)
    assert out["law"]["candidates"] == ["law:q"]


def test_lanes_with_extra_fuse_per_lane_and_rerank_on_question():
    s = FakeSearch()
    out = R.lanes_search("question", s, "", 50, True, ["rewrite one"])
    for lane in ("law", "guidance"):
        assert sorted(out[lane]["candidates"]) == [f"{lane}:q", f"{lane}:r"]
    assert s.reranked_with == ["question", "question"]


def test_paired_compare_by_document_and_holm():
    import paired as PT
    r = PT.compare([True] * 30 + [False] * 10, [True] * 20 + [False] * 20)
    assert r["diff"] == 0.25 and r["only_a"] == 10 and r["only_b"] == 0 and r["ci95"][0] > 0 and r["p"] < 0.01
    # the same 10 gains, all from one document: no longer convincing
    docs = ["d0"] * 10 + [f"d{i}" for i in range(1, 31)]
    a = [True] * 10 + [True] * 20 + [False] * 10
    b = [False] * 10 + [True] * 20 + [False] * 10
    one = PT.compare(a, b, docs)
    assert one["documents"] == 31 and one["p"] > 0.4
    assert PT.compare([True] * 5, [True] * 5)["p"] == 1.0
    assert PT.holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]


def test_doc_is_the_source_of_the_first_expected_section():
    import paired as PT
    assert PT.doc({"id": "q1", "expected": ["law:s-1", "other:s-2"], "top5": []}) == "law"


def test_rule_coverage_counts_rules_stated_by_the_shown_passages(monkeypatch):
    import paired as PT
    monkeypatch.setattr(PT, "rule_counts", lambda: {"q1": 3})
    monkeypatch.setattr(PT, "rules_stated", lambda: {("q1", "a:1"): frozenset({1}), ("q1", "b:1"): frozenset({1, 3}),
                                                     ("q1", "c:1"): frozenset({2})})
    row = {"id": "q1", "expected": ["a:1"], "top5": ["a:1", "b:1", "x:9", "c:1"]}
    assert PT.coverage(row, 3) == (2 / 3, 1)  # rules 1 and 3; x:9 has no verdict
    assert PT.coverage(row, 4) == (1.0, 1)
    assert PT.coverage(dict(row, id="q2"), 8) is None
    r = PT.compare([1.0, 2 / 3, 0.0], [1 / 3, 2 / 3, 1 / 3])
    assert (r["only_a"], r["only_b"]) == (1, 1) and abs(r["diff"] - 1 / 9) < 0.01
