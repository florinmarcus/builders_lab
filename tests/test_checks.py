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
    assert lint_fixes("x", [table_fix("table-1: T", ["A", "B", "C"], rows, ["One."])])  # count must match
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


def test_sentence_rules_allow_closing_brackets_and_list_numbers():
    from system.rag.checks import _lint_table, _sentence_count
    v = {"columns": ["Term", "Meaning"], "rows": [["a", "b"], ["c", "d"]], "heading_rows": [],
         "sentences": ["Term a means b (see the glossary.)", "Term c means ‘d.’"]}
    assert _lint_table(v) == []
    v["sentences"][1] = "Term c means d"
    assert _lint_table(v) == ["every sentence must end with a full stop"]
    sign = ("A fire action notice with three steps: 1. Operate nearest fire alarm. 2. Leave building by the "
            "nearest exit. 3. Report to the assembly point. A red box gives two rules.")
    assert _sentence_count(sign) == 4  # the list numbers do not end sentences


def test_listed_table_is_not_bound_by_its_title_family():
    from system.rag.checks import lint_fixes, table_family

    def fix(target, cols):
        return {"key": target[:16].ljust(16, "0"), "kind": "table", "target": target,
                "value": {"columns": cols, "rows": [["a"] * len(cols)], "heading_rows": [], "sentences": ["A row."]}}
    t11 = fix("table-11: Minimum dimensions for access fittings and inspection chambers", ["Type", "Size", "Depth"])
    t12 = fix("table-12: Minimum dimensions for manholes", ["Type", "Size of largest pipe"])
    assert table_family("adh", t12["target"]) is None and table_family("adh", t11["target"]) == "minimum dimensions"
    assert not any("same family" in p for p in lint_fixes("adh", [t11, t12]))
    assert any("same family" in p for p in lint_fixes("other", [t11, t12]))  # elsewhere the rule still binds


def test_checks_are_worked_only_for_versions_in_scope(tmp_path, monkeypatch):
    """ADR 0016: export, review and crop checks read current_trees, which leaves out versions superseded before 2025."""
    corpus = tmp_path / "corpus"
    (corpus / "parsed" / "x").mkdir(parents=True)
    (corpus / "versions" / "x").mkdir(parents=True)
    for vid, vt in (("a@2006", "2019-08-30"), ("a@2022", "2025-03-02"), ("a@2026", None)):
        (corpus / "parsed" / "x" / f"{vid}.json").write_text(json.dumps({**TREE, "version_id": vid}))
        (corpus / "versions" / "x" / f"{vid}.json").write_text(json.dumps(
            {"source_id": "x", "part": "a", "version_id": vid, "valid_from": "2006-01-01", "valid_to": vt}))
    monkeypatch.setattr(checks, "CORPUS_DIR", corpus)
    assert [t["version_id"] for t in checks.current_trees("x")] == ["a@2022", "a@2026"]


def test_redo_reads_the_fix_file_without_the_named_fixes_and_save_replaces_them(tmp_path, monkeypatch):
    """CORPUS_REDO: a saved fix is done again without a hand edit. The old fix of the same family does not bind the
    new answer's columns while it is itself being redone."""
    from system.rag import fixes as F

    corpus = tmp_path / "corpus"
    (corpus / "parsed" / "x" / "checks").mkdir(parents=True)
    (corpus / "fixes").mkdir()
    for mod in (checks, F):
        monkeypatch.setattr(mod, "CORPUS_DIR", corpus)
    monkeypatch.setattr(checks, "ROOT", tmp_path)
    monkeypatch.setattr(checks, "fixes_path", lambda sid: corpus / "fixes" / f"{sid}.json")
    old4 = table_fix("table-4: Algorithm for the boiler room", ["Factor", "Score"], [["N", "1"]], ["S."], key="a" * 16)
    old5 = table_fix("table-5: Algorithm for the classroom", ["Factor", "Score"], [["N", "1"]], ["S."], key="b" * 16)
    (corpus / "fixes" / "x.json").write_text(json.dumps({"source_id": "x", "fixes": [old4, old5]}))
    assert len(F.load_fixes("x")) == 2
    monkeypatch.setenv("CORPUS_REDO", "aaaaaaaaaaaaaaaa, bbbbbbbbbbbbbbbb")
    assert F.redo_keys() == {"a" * 16, "b" * 16} and F.load_fixes("x") == []
    ps, held = packets("x", [TREE], F.load_fixes("x"))  # both tables come back; the first of the family goes alone
    assert "template" not in ps[0] and held == ["table-5: Algorithm for the classroom"]
    (corpus / "parsed" / "x" / "checks" / "0.json").write_text(json.dumps(ps[0]))
    answers = tmp_path / "a.jsonl"
    answers.write_text(json.dumps({"key": "a" * 16, "kind": "table", "reason": "r", "evidence": "e", "value": {
        "columns": ["Factor", "Group: Score"], "rows": [["N", "1"]], "sentences": ["S."]}}))
    assert checks.save("x", answers, by="redo", today="2026-11-23") == 0  # not refused for differing from old table-5
    saved = {f["key"]: f for f in json.loads((corpus / "fixes" / "x.json").read_text())["fixes"]}
    assert saved["a" * 16]["value"]["columns"] == ["Factor", "Group: Score"] and saved["a" * 16]["by"] == "redo"
    assert saved["b" * 16]["by"] == "test"  # still there until its own new answer is saved
    monkeypatch.delenv("CORPUS_REDO")
    assert len(F.load_fixes("x")) == 2


def test_table_instructions_ask_for_group_headings_in_the_column_names():
    assert "join them from the top down" in checks.INSTRUCTIONS["table"] and "lowest header row" not in checks.INSTRUCTIONS["table"]
