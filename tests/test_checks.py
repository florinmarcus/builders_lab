"""Tests for the model-check step (system/rag/checks.py): every saved fix passes the rules, packets carry
fixed instructions and family templates, and save refuses answers that break the rules."""

import json

import pytest

from system.rag import checks
from system.rag.checks import family, lint, lint_fixes, packets


def test_every_saved_fix_file_passes_the_rules():
    assert lint() == []


def table_fix(target, columns, rows, sentences, heads=None, key="0123456789abcdef"):
    v = {"columns": columns, "rows": rows, "sentences": sentences}
    if heads is not None:
        v["heading_rows"] = heads
    return {"key": key, "kind": "table", "target": target, "value": v, "reason": "r", "evidence": "e",
            "by": "test", "date": "2026-11-20", "confidence": "high"}


def test_family_is_the_title_before_for():
    assert family("Priority assessment algorithm for the boiler room") == "priority assessment algorithm"
    assert family("Material assessment algorithm") is None


def test_rows_need_one_sentence_each_except_heading_rows():
    rows = [["Loose insulation", "", ""], ["Loose fill", "Lofts", "Pure"]]
    assert lint_fixes("x", [table_fix("table-1: T", ["A", "B", "C"], rows, ["One.", "Two."])])  # heading not listed
    assert lint_fixes("x", [table_fix("table-1: T", ["A", "B", "C"], rows, ["Loose fill is in lofts."], [0])]) == []
    bad = lint_fixes("x", [table_fix("table-1: T", ["A", "B"], rows, ["S."], [0])])
    assert any("2 cells" in b for b in bad)


def test_one_family_one_layout():
    a = table_fix("table-4: Algorithm for the boiler room", ["Factor", "Sub-factor", "Score"], [["N", "M", "1"]],
                  ["S."], key="0123456789abcdef")
    b = table_fix("table-9: Algorithm for the warehouse", ["Factor", "Score"], [["N: M", "1"]], ["S."],
                  key="fedcba9876543210")
    assert any("columns differ" in p for p in lint_fixes("x", [a, b]))


TREE = {"version_id": "main@1", "sections": [
    {"id": "table-4", "type": "table", "title": "Algorithm for the boiler room", "text": "", "labels": []},
    {"id": "table-5", "type": "table", "title": "Algorithm for the classroom", "text": "", "labels": []},
    {"id": "figure-1", "type": "figure", "title": "A pipe", "text": "", "labels": []},
], "checks": [
    {"kind": "table", "section_id": "table-4", "key": "aaaaaaaaaaaaaaaa", "images": ["p1.png"]},
    {"kind": "table", "section_id": "table-5", "key": "bbbbbbbbbbbbbbbb", "images": ["p2.png"]},
    {"kind": "figure", "section_id": "figure-1", "key": "cccccccccccccccc", "images": ["f1.png"]},
]}


def test_first_table_of_a_new_family_goes_alone():
    ps, held = packets("x", [TREE], [])
    assert [p["target"] for p in ps] == ["table-4: Algorithm for the boiler room", "figure-1: A pipe"]
    assert ps[0]["first_of_family"] == "algorithm" and held == ["table-5: Algorithm for the classroom"]
    assert ps[0]["instructions"] == checks.INSTRUCTIONS["table"] and ps[1]["kind"] == "figure_description"


def test_later_tables_get_the_saved_one_as_template():
    saved = table_fix("table-4: Algorithm for the boiler room", ["Factor", "Score"], [["N", "1"]], ["S."],
                      key="aaaaaaaaaaaaaaaa")
    ps, held = packets("x", [TREE], [saved])
    t5 = next(p for p in ps if p["key"] == "bbbbbbbbbbbbbbbb")
    assert t5["template"]["columns"] == ["Factor", "Score"] and held == []


def test_save_checks_answers_against_packets_and_rules(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    (corpus / "parsed" / "x" / "checks").mkdir(parents=True)
    (corpus / "fixes").mkdir()
    monkeypatch.setattr(checks, "CORPUS_DIR", corpus)
    monkeypatch.setattr(checks, "ROOT", tmp_path)
    monkeypatch.setattr(checks, "fixes_path", lambda sid: corpus / "fixes" / f"{sid}.json")
    saved = table_fix("table-4: Algorithm for the boiler room", ["Factor", "Score"], [["N", "1"]], ["S."],
                      key="aaaaaaaaaaaaaaaa")
    ps, _ = packets("x", [TREE], [saved])
    for i, p in enumerate(ps):
        (corpus / "parsed" / "x" / "checks" / f"{i}.json").write_text(json.dumps(p))
    answers = tmp_path / "a.jsonl"
    answers.write_text("\n".join(json.dumps(a) for a in [
        {"key": "bbbbbbbbbbbbbbbb", "kind": "table", "confidence": "high", "reason": "r", "evidence": "e",
         "value": {"columns": ["Factor", "Sub", "Score"], "rows": [["N", "M", "1"]], "sentences": ["S."]}},
        {"key": "cccccccccccccccc", "kind": "figure_description", "reason": "r", "evidence": "e",
         "value": "Photo of a lagged pipe in a boiler room. The lagging is white."},
        {"key": "dddddddddddddddd", "kind": "figure_description", "value": "Not an open check at all."},
    ]))
    assert checks.save("x", answers, by="test", today="2026-11-20") == 1  # two rejected
    doc = json.loads((corpus / "fixes" / "x.json").read_text())
    assert [f["key"] for f in doc["fixes"]] == ["cccccccccccccccc"]
    assert doc["fixes"][0]["target"] == "figure-1: A pipe" and doc["fixes"][0]["by"] == "test"


@pytest.mark.parametrize("value,ok", [("E", True), ("W", True), ("England", False)])
def test_applies_to_values(value, ok):
    f = {"key": "0123456789abcdef", "kind": "applies_to", "target": "Part K", "value": value, "reason": "r",
         "by": "t", "date": "2026-11-20"}
    assert (lint_fixes("x", [f]) == []) is ok


def test_single_column_rows_are_not_headings_and_abbreviations_do_not_end_sentences():
    one = table_fix("requirement-b4-box-2: R", ["Text"], [["7.(1) Materials ..."], ["(2) Every ..."]], ["S1.", "S2."])
    assert lint_fixes("x", [one]) == []
    f = {"key": "0123456789abcdef", "kind": "figure_description", "target": "diagram-12.1: D", "reason": "r",
         "by": "t", "date": "2026-11-20", "value": "Plan of rooflights, max. area 5m2 each. Spacing min. 3m apart."}
    assert lint_fixes("x", [f]) == []
