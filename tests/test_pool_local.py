"""Pool judge checks (evals/golden/pool_local.py, brief v2): quotes, verdict logic, planted lines, INVALID lines."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals" / "golden"))
import pool_local as P  # noqa: E402

ROW = {"id": "q-1", "section": "s:1", "question": "Q?", "question_scope": "contractor; UK; x",
       "rules": ["Rule one.", "Rule two."],
       "passage": "CIS > Verification\nWhere the subcontractor was verified in the last two tax years, the contractor\n"
                  "pays him on the same basis as before unless HMRC has told them otherwise."}


def judged(**over) -> dict:
    j = {"id": "q-1", "section": "s:1", "passage_scope": "contractors; UK", "scope_match": "yes",
         "rules": [{"n": 1, "states": "yes", "quote": "verified in the last two tax years"},
                   {"n": 2, "states": "no", "quote": ""}], "reason": "r", "verdict": "yes", "judge": "t"}
    j.update(over)
    return j


def test_a_good_yes_passes_and_spacing_and_curly_quotes_do_not_count():
    assert P.check_line(judged(), ROW, None) is None
    j = judged(rules=[{"n": 1, "states": "yes", "quote": "the  contractor pays him on the same basis"},
                      {"n": 2, "states": "no", "quote": ""}])
    assert P.check_line(j, ROW, None) is None
    assert P.norm("HMRC’s “notice” – x") == "hmrc's \"notice\" - x"


def test_a_quote_not_in_the_passage_is_invalid():
    j = judged(rules=[{"n": 1, "states": "yes", "quote": "verified in the previous two tax years"},
                      {"n": 2, "states": "no", "quote": ""}])
    assert "not found" in P.check_line(j, ROW, None)
    j = judged(rules=[{"n": 1, "states": "yes", "quote": ""}, {"n": 2, "states": "no", "quote": ""}])
    assert "not found" in P.check_line(j, ROW, None)


def test_the_verdict_must_follow_from_scope_and_rules():
    assert "does not follow" in P.check_line(judged(scope_match="no"), ROW, None)
    assert P.check_line(judged(scope_match="no", verdict="no"), ROW, None) is None
    none = [{"n": 1, "states": "no", "quote": ""}, {"n": 2, "states": "no", "quote": ""}]
    assert "does not follow" in P.check_line(judged(rules=none), ROW, None)
    assert P.check_line(judged(rules=none, verdict="no"), ROW, None) is None


def test_shape_errors_are_invalid():
    assert "one entry per rule" in P.check_line(judged(rules=judged()["rules"][:1]), ROW, None)
    assert "not yes/no" in P.check_line(judged(verdict="maybe"), ROW, None)
    assert "does not match" in P.check_line(judged(section="s:2"), ROW, None)


def test_a_planted_line_judged_wrong_is_flagged():
    assert "planted" in P.check_line(judged(), ROW, "no")
    assert P.check_line(judged(), ROW, "yes") is None


def _setup(tmp_path, lines, planted):
    d = tmp_path / "packets"
    d.mkdir()
    rows = [ROW, {**ROW, "section": "s:2"}, {**ROW, "id": "q-2"}]
    (d / "packet-000.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "judged-packet-000.jsonl").write_text("".join(json.dumps(j) + "\n" for j in lines))
    (d / "planted.json").write_text(json.dumps(planted))
    return d


def test_merge_keeps_good_lines_drops_planted_and_quotes_and_writes_invalid(tmp_path):
    lines = [judged(), judged(section="s:2", verdict="no", scope_match="no"),
             judged(id="q-2", rules=[{"n": 1, "states": "yes", "quote": "words not in it at all"},
                                     {"n": 2, "states": "no", "quote": ""}])]
    d = _setup(tmp_path, lines, {"q-1|s:2": "no"})
    to = tmp_path / "judgments.jsonl"
    assert P.main(["merge", "--judged", str(d / "judged-*.jsonl"), "--to", str(to)]) == 0
    got = P.read_jsonl(to)
    assert [(g["id"], g["section"], g["verdict"]) for g in got] == [("q-1", "s:1", "yes")]
    assert got[0]["rules_stated"] == [1] and got[0]["scope_match"] == "yes"
    assert "quote" not in json.dumps(got) and "HMRC" not in json.dumps(got)
    assert [r["id"] for r in P.read_jsonl(d / "invalid-packet-000.jsonl")] == ["q-2"]


def test_merge_skips_a_packet_with_a_failed_planted_line_or_wrong_line_count(tmp_path):
    lines = [judged(), judged(section="s:2"), judged(id="q-2", verdict="no", scope_match="no")]
    d = _setup(tmp_path, lines, {"q-1|s:2": "no"})
    to = tmp_path / "judgments.jsonl"
    P.main(["merge", "--judged", str(d / "judged-*.jsonl"), "--to", str(to)])
    assert P.read_jsonl(to) == []
    (d / "judged-packet-000.jsonl").write_text(json.dumps(judged()) + "\n")
    P.main(["merge", "--judged", str(d / "judged-*.jsonl"), "--to", str(to)])
    assert P.read_jsonl(to) == []
