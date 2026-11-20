"""Answer eval helpers (evals/judge.py): judge JSON parsing, code checks, summary. No model calls."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import judge as J  # noqa: E402

GOOD = ('Some preamble {"correctness_reason": "matches", "correctness": 5, "grounding_reason": "cited", '
        '"grounding": 4, "completeness_reason": "misses one point", "completeness": 3} trailing')


def test_parse_judge_takes_strict_json_and_rejects_bad_scores():
    j = J.parse_judge(GOOD)
    assert j["correctness"] == 5 and j["completeness"] == 3
    assert J.parse_judge(GOOD.replace('"grounding": 4', '"grounding": 7')) is None
    assert J.parse_judge(GOOD.replace('"grounding": 4', '"grounding": "4"')) is None
    assert J.parse_judge('{"correctness": 5}') is None
    assert J.parse_judge("no json here") is None


def test_code_checks():
    assert J.declined("NOT IN SOURCES: the passages do not cover skips")
    assert J.asked_back("CLARIFY: is the building over 11 m?")
    assert J.bad_citations("Use FD30S doors [1][2]. Check closers [6].", 5) == [6]
    assert J.bad_citations("No citations", 0) == []


def test_pass_needs_correct_and_grounded():
    j = J.parse_judge(GOOD)
    assert J.passed(j) is True
    assert J.passed({**j, "grounding": 3}) is False
    assert J.passed(None) is None


def test_summary_by_kind_and_unjudged():
    j = J.parse_judge(GOOD)
    rows = [{"kind": "answerable", "judge": j, "declined": False, "asked_back": False, "bad_citations": []},
            {"kind": "out_of_scope", "judge": {**j, "correctness": 2}, "declined": True, "asked_back": False, "bad_citations": [7]},
            {"kind": "answerable", "judge": None, "declined": False, "asked_back": False, "bad_citations": []}]
    s = J.summarise(rows)
    assert s["judged"] == 2 and s["unjudged"] == 1 and s["pass_rate"] == 0.5
    assert s["by_kind"]["out_of_scope"]["declined"] == 1.0 and s["bad_citation_rows"] == 1
