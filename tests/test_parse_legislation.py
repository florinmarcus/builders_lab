"""Tests for the legislation XML parser (ADR 0010, design: architecture/design/regulations-corpus.md)."""

import json
import re
from pathlib import Path

import pytest

from system.rag.fixes import load_fixes
from system.rag.parse_legislation import parse_legislation

FIXTURE = Path(__file__).parent / "fixtures" / "legislation_mini.xml"
ROOT = Path(__file__).parent.parent
META = {"source_id": "demo", "version_id": "main@2026-11-06-abc", "valid_from": "2026-11-06",
        "valid_to": None, "sha256": "abc", "title": "The Demo Regulations 2010"}


@pytest.fixture(scope="module")
def tree():
    return parse_legislation(FIXTURE.read_bytes(), META)


def sec(tree, sid):
    found = [s for s in tree["sections"] if s["id"] == sid]
    assert len(found) == 1, f"{sid}: {len(found)} found"
    return found[0]


def test_tree_keeps_version_metadata(tree):
    for k, v in META.items():
        assert tree[k] == v
    assert tree["parser"].startswith("legislation-xml/")


def test_parts_chapters_and_regulations(tree):
    regs = [s for s in tree["sections"] if s["type"] == "regulation"]
    assert [s["number"] for s in regs if s["applies_to"] != "W"] == ["1", "2", "4", "5"]
    assert sec(tree, "part-2-chapter-1")["parent_id"] == "part-2"
    assert sec(tree, "regulation-4")["parent_id"] == "part-2-chapter-1"
    assert sec(tree, "regulation-1")["title"] == "Citation"


def test_breadcrumb(tree):
    assert sec(tree, "regulation-4")["heading_path"] == [
        "The Demo Regulations 2010", "Part 2 Control of building work", "Chapter 1 Duties", "Regulation 4 Requirements"]


def test_clean_text_with_numbers_and_no_markers(tree):
    r4 = sec(tree, "regulation-4")
    assert r4["text"] == (
        "(1) Building work shall comply with Schedule 1 and section 1 of the Building Act 1984.\n"
        "(2) Work under paragraph (1) includes—\n"
        "(a) new buildings; and\n"
        "(b) extensions.")
    for s in tree["sections"]:
        assert not re.search(r"\bF\d+\b|key-", s["text"]), s["id"]


def test_sub_paragraphs_are_sections_for_later_splitting(tree):
    p = sec(tree, "regulation-4-2")
    assert p["type"] == "paragraph" and p["parent_id"] == "regulation-4"
    assert p["text"].startswith("(2) Work under paragraph (1)")


def test_country_from_extent(tree):
    assert sec(tree, "regulation-1")["applies_to"] == "E+W"
    assert sec(tree, "regulation-4")["applies_to"] == "E"


def test_wales_copy_is_its_own_section_linked_to_england(tree):
    w = sec(tree, "regulation-4@W")
    assert w["applies_to"] == "W"
    assert w["alt_of"] == "regulation-4"
    assert w["text"] == "In Wales, building work shall comply with Schedule 1."
    assert w["parent_id"] == "part-2-chapter-1"
    assert sec(tree, "regulation-4")["alt_versions"] == ["regulation-4@W"]


def test_amendment_notes_as_metadata(tree):
    r4 = sec(tree, "regulation-4")
    notes = {a["id"]: a for a in r4["amendments"]}
    assert notes["key-f3"]["type"] == "F"
    assert "substituted (6.4.2024)" in notes["key-f3"]["text"]
    assert notes["key-f2"]["type"] == "E"
    # Notes are kept on the paragraph too, so a split chunk keeps them.
    assert [a["id"] for a in sec(tree, "regulation-4-2")["amendments"]] == ["key-f3"]


def test_repealed_status(tree):
    r5 = sec(tree, "regulation-5")
    assert r5["status"] == "repealed"
    assert r5["text"] == ". . ."


def test_references_internal_and_external(tree):
    refs = sec(tree, "regulation-4")["references"]
    assert {"words": "Schedule 1", "target": "schedule-1", "uri": "http://www.legislation.gov.uk/id/uksi/2010/9999/schedule/1",
            "internal": True} in refs
    assert {"words": "paragraph (1)", "target": "regulation-4-1",
            "uri": "http://www.legislation.gov.uk/id/uksi/2010/9999/regulation/4/1", "internal": True} in refs
    ext = [r for r in refs if not r["internal"]]
    assert ext == [{"words": "Building Act 1984", "target": None,
                    "uri": "http://www.legislation.gov.uk/id/ukpga/1984/55", "internal": False}]


def test_definitions_from_term_marks(tree):
    defs = {d["term"]: d for d in tree["definitions"]}
    assert set(defs) == {"the Act", "relevant building"}
    assert defs["the Act"]["text"] == "“the Act” means the Building Act 1984;"
    assert defs["the Act"]["section_id"] == "regulation-2"
    assert defs["relevant building"]["id"] == "term-relevant-building"


def test_url_points_to_the_section(tree):
    assert sec(tree, "regulation-1")["url"] == "http://www.legislation.gov.uk/uksi/2010/9999/regulation/1/2026-11-06"


def test_tree_is_json(tree):
    json.dumps(tree, ensure_ascii=False)


# ---------------------------------------------------------------- Schedules (step 2)

def reqs(tree):
    return {s["id"]: s for s in tree["sections"] if s["type"] == "requirement"}


def test_schedule_container_and_breadcrumb(tree):
    s1 = sec(tree, "schedule-1")
    assert s1["type"] == "schedule" and s1["number"] == "1" and s1["title"] == "Requirements"
    pb = sec(tree, "schedule-1-part-B")
    assert pb["type"] == "schedule-part" and pb["number"] == "B" and pb["parent_id"] == "schedule-1"
    assert sec(tree, "schedule-1-B1")["heading_path"] == [
        "The Demo Regulations 2010", "Schedule 1 Requirements", "Part B Fire safety", "B1 Means of warning and escape"]


def test_requirement_text_and_limits(tree):
    b1 = sec(tree, "schedule-1-B1")
    assert b1["number"] == "B1" and b1["title"] == "Means of warning and escape"
    assert b1["text"] == "B1.—(1) The building shall be designed for early warning of fire.\n(a) in all buildings; and"
    assert b1["limits"] == "Requirement B1 does not apply to prisons."


def test_bold_line_in_a_cell_is_a_heading_not_text(tree):
    b4 = sec(tree, "schedule-1-B4")
    assert b4["title"] == "External fire spread"
    assert b4["text"].startswith("B4.—(1)")
    assert "External fire spread" not in sec(tree, "schedule-1-B1")["text"]


def test_code_alone_and_sub_codes(tree):
    s1 = sec(tree, "schedule-1-S1")
    assert s1["text"] == "S1\n(1) A new residential building must have a charge point."
    m4 = sec(tree, "schedule-1-M4(1)@W")
    assert m4["title"] == "Category 1 - visitable dwelling"


def test_duplicate_part_labelled_by_notes(tree):
    eng, wal = sec(tree, "schedule-1-part-M"), sec(tree, "schedule-1-part-M@W")
    assert eng["applies_to"] == "E" and wal["applies_to"] == "W"
    assert sec(tree, "schedule-1-M1")["applies_to"] == "E"
    assert sec(tree, "schedule-1-M1@W")["applies_to"] == "W"
    assert sec(tree, "schedule-1-M1@W")["alt_of"] == "schedule-1-M1"
    for p in (eng, wal):
        assert p["label_source"] == "code-guess"
    assert any("schedule-1-part-M" in i and "model check" in i for i in tree["issues"])


def test_unduplicated_parts_keep_document_extent(tree):
    assert sec(tree, "schedule-1-B1")["applies_to"] == "E+W"
    assert "label_source" not in sec(tree, "schedule-1-part-B")


def test_part_without_code_is_flagged_not_guessed(tree):
    pt = sec(tree, "schedule-1-part-T")
    assert pt["title"] == "Toilet accommodation"
    t = [r for r in reqs(tree).values() if r["parent_id"] == "schedule-1-part-T"]
    assert len(t) == 1 and t[0]["number"] is None
    assert t[0]["text"] == "Toilet accommodation must consist of single-sex toilets."
    assert any("schedule-1-part-T" in i and "no requirement code" in i for i in tree["issues"])


def test_schedule_paragraphs_parts_and_wales_copy(tree):
    p = sec(tree, "schedule-2-part-1-paragraph-1")
    assert p["type"] == "schedule-paragraph" and p["applies_to"] == "E"
    assert p["heading_path"][-2:] == ["Class 1", "Paragraph 1 Buildings controlled elsewhere"]
    w = sec(tree, "schedule-2-part-1-paragraph-1@W")
    assert w["alt_of"] == p["id"] and w["text"] == "In Wales, a building subject to other law."
    assert not [i for i in tree["issues"] if i.startswith("version block")]


def test_repealed_schedule_marks_its_paragraphs(tree):
    assert sec(tree, "schedule-3")["status"] == "repealed"
    assert sec(tree, "schedule-3-paragraph-1")["status"] == "repealed"


def test_no_step_2_issue_left(tree):
    assert not [i for i in tree["issues"] if "step 2" in i]


# ---------------------------------------------------------------- saved fixes and model checks (step 3)

def test_checks_list_what_the_model_must_decide(tree):
    kinds = sorted((c["kind"], c["part"]) for c in tree["checks"])
    assert kinds == [("applies_to", "M"), ("applies_to", "M"), ("requirement_code", "T")]
    m = [c for c in tree["checks"] if c["kind"] == "applies_to"]
    assert {c["guess"] for c in m} == {"E", "W"}
    assert all(c["key"] and c["evidence"] for c in m)
    assert any("(W.)" in e for c in m for e in c["evidence"])
    t = next(c for c in tree["checks"] if c["kind"] == "requirement_code")
    assert t["text"].startswith("Toilet accommodation must consist")


def fixes_from(tree, m_values=("E", "W"), t_code="T1"):
    m = [c for c in tree["checks"] if c["kind"] == "applies_to"]
    t = next(c for c in tree["checks"] if c["kind"] == "requirement_code")
    out = [{"key": c["key"], "kind": "applies_to", "value": v, "reason": "test"} for c, v in zip(m, m_values)]
    out.append({"key": t["key"], "kind": "requirement_code", "value": t_code, "reason": "test"})
    return out


def test_saved_fixes_replace_guesses(tree):
    fixed = parse_legislation(FIXTURE.read_bytes(), META, fixes=fixes_from(tree))
    eng, wal = sec(fixed, "schedule-1-part-M"), sec(fixed, "schedule-1-part-M@W")
    assert (eng["applies_to"], wal["applies_to"]) == ("E", "W")
    assert eng["label_source"] == "model" == wal["label_source"]
    t1 = sec(fixed, "schedule-1-T1")
    assert t1["number"] == "T1" and t1["code_source"] == "model"
    assert t1["heading_path"][-1] == "T1"
    assert fixed["checks"] == [] and fixed["issues"] == []


def test_saved_fixes_can_flip_the_guess(tree):
    fixed = parse_legislation(FIXTURE.read_bytes(), META, fixes=fixes_from(tree, ("W", "E")))
    assert sec(fixed, "schedule-1-part-M")["applies_to"] == "E"
    # The copy that the code thought was England's is now the Wales copy.
    assert "Wales" in sec(fixed, "schedule-1-M1")["text"]


def test_fixes_that_disagree_are_not_used(tree):
    fixed = parse_legislation(FIXTURE.read_bytes(), META, fixes=fixes_from(tree, ("E", "E")))
    assert sec(fixed, "schedule-1-part-M")["label_source"] == "code-guess"
    assert any("disagree" in i for i in fixed["issues"])
    assert len([c for c in fixed["checks"] if c["kind"] == "applies_to"]) == 2


# ---------------------------------------------------------------- real files (skipped where raw files are missing)

def _current_br2010():
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "versions" / "br2010").glob("*.json")]
    cur = [r for r in recs if r["valid_to"] is None]
    if not cur or not (ROOT / cur[0]["raw_path"]).exists():
        pytest.skip("Building Regulations raw file not on this machine")
    r = cur[0]
    return parse_legislation((ROOT / r["raw_path"]).read_bytes(), {**r, "title": "The Building Regulations 2010"},
                             fixes=load_fixes("br2010"))


@pytest.fixture(scope="module")
def br2010():
    return _current_br2010()


def test_real_counts(br2010):
    regs = [s for s in br2010["sections"] if s["type"] == "regulation"]
    england_side = [s for s in regs if s["applies_to"] != "W"]
    wales = [s for s in regs if s["applies_to"] == "W"]
    assert len(england_side) == 170
    # 27 Wales version blocks: 26 regulations, plus Schedule 4 paragraph 1.
    assert len(wales) == 26
    assert all(w["alt_of"] for w in wales)
    assert next(s for s in br2010["sections"] if s["id"] == "schedule-4-paragraph-1@W")["applies_to"] == "W"
    assert not [i for i in br2010["issues"] if i.startswith("version block")]


def test_real_schedule_1(br2010):
    req = [s for s in br2010["sections"] if s["type"] == "requirement"]
    england = {s["number"] for s in req if s["applies_to"] != "W"}
    for code in ["A1", "A3", "B1", "B4", "B5", "G2A", "K1", "K5.1", "K5.4", "K6", "L2", "M4(1)", "M4(2)", "M4(3)", "O1", "Q1", "RA1", "RA2", "S1", "S6"]:
        assert code in england, code
    parts = [s for s in br2010["sections"] if s["type"] == "schedule-part" and s["parent_id"] == "schedule-1"]
    assert len(parts) == 22
    dup = [p for p in parts if p.get("label_source")]
    assert sorted(p["number"] for p in dup) == ["K", "K", "M", "M", "O", "O"]
    # Every duplicated Part has one England and one Wales copy.
    for letter in "KMO":
        assert sorted(p["applies_to"] for p in dup if p["number"] == letter) == ["E", "W"]
    # The first heading row ("Requirement | Limits on application") is never a requirement title.
    assert not [s for s in req if s["title"] and s["title"].startswith("Requirement")]
    b1 = next(s for s in req if s["number"] == "B1")
    assert b1["title"] == "Means of warning and escape" and b1["text"].startswith("B1.")


def test_real_no_requirement_text_left_in_headings(br2010):
    for s in br2010["sections"]:
        if s["type"] == "requirement" and s["number"] and s.get("code_source") != "model":
            assert s["text"].startswith(s["number"].split("(")[0]), s["id"]
    assert len([s for s in br2010["sections"] if s["type"] == "part" and s["parent_id"] is None]) == 15


def test_real_definitions(br2010):
    in_reg2 = [d for d in br2010["definitions"] if d["section_id"] == "regulation-2"]
    assert len(in_reg2) >= 90
    terms = {d["term"] for d in in_reg2}
    assert {"building", "building work"} <= terms


def test_real_text_is_clean(br2010):
    reg1 = next(s for s in br2010["sections"] if s["id"] == "regulation-1")
    assert reg1["text"].startswith("These Regulations may be cited as the Building Regulations 2010")
    for s in br2010["sections"]:
        assert "key-" not in s["text"], s["id"]


def test_real_all_checks_settled_by_saved_fixes(br2010):
    assert br2010["checks"] == []
    assert br2010["issues"] == []
    labelled = [s for s in br2010["sections"] if s["type"] == "schedule-part" and s.get("label_source")]
    assert labelled and all(s["label_source"] == "model" for s in labelled)
    assert next(s for s in br2010["sections"] if s["id"] == "schedule-1-T1")["code_source"] == "model"


# ---------------------------------------------------------------- tables inside provisions, equation versions (S2)

TABLE_FIXTURE = Path(__file__).parent / "fixtures" / "legislation_table.xml"


@pytest.fixture(scope="module")
def table_tree():
    meta = {**META, "source_id": "demo-hazard", "title": "The Demo Hazard Regulations 2005"}
    return parse_legislation(TABLE_FIXTURE.read_bytes(), meta)


def test_table_inside_a_regulation_is_text_and_a_table_section(table_tree):
    reg = sec(table_tree, "regulation-7")
    assert reg["text"] == ("The hazard band is given by the following table—\nScore | Band\n5,000 or more | A\n"
                           "2,000 to 4,999 | B\nBands A to C are category 1 hazards.")
    tables = [s for s in table_tree["sections"] if s["type"] == "table" and s["parent_id"] == "regulation-7"]
    assert len(tables) == 1 and tables[0]["title"] == "Hazard bands"
    assert tables[0]["text"].splitlines()[1] == "5,000 or more | A"
    assert not [i for i in table_tree["issues"] if "Tabular" in i]


def test_equation_image_versions_are_skipped_quietly(table_tree):
    assert not [i for i in table_tree["issues"] if "version block" in i]
    assert [s["number"] for s in table_tree["sections"] if s["type"] == "regulation"] == ["7", "8"]


def test_a_schedule_1_that_is_not_a_requirements_table_is_an_ordinary_table(table_tree):
    assert not table_tree["checks"]
    assert not [s for s in table_tree["sections"] if s["type"] in ("requirement", "schedule-part")]
    t = [s for s in table_tree["sections"] if s["type"] == "table" and s["parent_id"] == "schedule-1"]
    assert len(t) == 1 and "1961 c. 34 | The Demo Factories Act 1961" in t[0]["text"]
