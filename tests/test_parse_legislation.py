"""Tests for the legislation XML parser (ADR 0010, design: architecture/design/regulations-corpus.md)."""

import json
import re
from pathlib import Path

import pytest

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


# ---------------------------------------------------------------- real files (skipped where raw files are missing)

def _current_br2010():
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "versions" / "br2010").glob("*.json")]
    cur = [r for r in recs if r["valid_to"] is None]
    if not cur or not (ROOT / cur[0]["raw_path"]).exists():
        pytest.skip("Building Regulations raw file not on this machine")
    r = cur[0]
    return parse_legislation((ROOT / r["raw_path"]).read_bytes(), {**r, "title": "The Building Regulations 2010"})


@pytest.fixture(scope="module")
def br2010():
    return _current_br2010()


def test_real_counts(br2010):
    regs = [s for s in br2010["sections"] if s["type"] == "regulation"]
    england_side = [s for s in regs if s["applies_to"] != "W"]
    wales = [s for s in regs if s["applies_to"] == "W"]
    assert len(england_side) == 170
    # 27 Wales version blocks: 26 regulations, plus Schedule 4 paragraph 1 (Schedules come in step 2).
    assert len(wales) == 26
    assert all(w["alt_of"] for w in wales)
    unlinked = [i for i in br2010["issues"] if i.startswith("version block")]
    assert len(unlinked) == 1 and "v10020" in unlinked[0]
    assert len([s for s in br2010["sections"] if s["type"] == "part"]) == 15


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
