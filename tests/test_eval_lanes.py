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


def test_paired_sign_test_and_compare():
    import paired as PT
    assert PT.sign_test(0, 0) == 1.0
    assert PT.sign_test(10, 10) == 1.0
    assert PT.sign_test(20, 0) < 0.001
    r = PT.compare([True] * 30 + [False] * 10, [True] * 20 + [False] * 20)
    assert r["diff"] == 0.25 and r["only_a"] == 10 and r["only_b"] == 0 and r["ci95"][0] > 0
