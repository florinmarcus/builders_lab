"""Tests for the chunker (system/rag/chunk.py): hand-made trees for each rule, and checks on the real parsed
trees where they exist on this machine (corpus/parsed/ is not in git)."""

import json
from pathlib import Path

import pytest

from system.rag import chunk as ch
from system.rag.chunk import chunk_tree, find_refs, legal_weight, split_paragraphs

ROOT = Path(__file__).parent.parent


def sec(sid, type_, text="", parent=None, **kw):
    return {"id": sid, "type": type_, "text": text, "parent_id": parent, "number": kw.pop("number", None),
            "title": kw.pop("title", None), "heading_path": kw.pop("path", ["Doc", sid]), **kw}


def tree(sections, **kw):
    return {"source_id": kw.get("source_id", "demo"), "version_id": "main@1", "valid_from": "2026-01-01",
            "valid_to": None, "title": "Doc", "sections": sections, "definitions": kw.get("definitions", []),
            "checks": [], "image_display": kw.get("image_display", True)}


GUIDE = {"id": "demo", "title": "Demo guide", "kind": "approved-document", "nation": "england"}
LAW = {"id": "demo-law", "title": "Demo Regulations", "kind": "legislation", "nation": "england-wales"}
RECORD = {"fetched_url": "https://example.org/doc.pdf", "edition_date": "2026-01-01"}


def by_suffix(chunks):
    return {c["id"].split(":")[-1]: c for c in chunks}


def test_legal_weight_from_kind():
    assert legal_weight(LAW) == "law" and legal_weight(GUIDE) == "statutory-guidance"
    assert legal_weight({"id": "hse-l143", "kind": "hse-guidance"}) == "approved-code"
    assert legal_weight({"id": "hse-hsg264", "kind": "hse-guidance"}) == "guidance"
    assert legal_weight({"id": "x", "kind": "guidance", "legal_weight": "law"}) == "law"


def test_guidance_paragraph_chunk_has_filters_breadcrumb_page_link_and_terms():
    t = tree([sec("section-2", "chapter", title="Section 2"),
              sec("para-2.5", "paragraph", "Every storey should have an alarm (see paragraph 2.6 and Diagram 2.1a).",
                  "section-2", number="2.5", path=["Doc", "Section 2", "Paragraph 2.5"], printed_page="13",
                  file_page=25, marked_terms=["storey"]),
              sec("para-2.6", "paragraph", "Second.", "section-2", file_page=25),
              sec("diagram-2.1", "figure", "Means of escape", number="2.1", title="Means of escape",
                  labels=["Fd"], description="A plan of a house.", kind_label="diagram", file_page=24),
              sec("definition-storey", "definition", "A floor level.", title="Storey")],
             definitions=[{"term": "Storey", "section_id": "definition-storey"}])
    chunks, splits = chunk_tree(t, GUIDE, RECORD)
    C = by_suffix(chunks)
    p = C["para-2.5"]
    assert p["chunk_type"] == "paragraph" and p["legal_weight"] == "statutory-guidance" and p["applies_to"] == "E"
    assert p["url"] == "https://example.org/doc.pdf#page=25" and p["printed_page"] == "13"
    assert p["embed_text"].startswith("Doc › Section 2 › Paragraph 2.5\nEvery storey")
    assert p["terms"] == ["definition-storey"]
    assert {r["to_section"] for r in p["references"]} == {"para-2.6", "diagram-2.1"}
    assert "section-2" not in C  # chapters are breadcrumb only
    assert C["diagram-2.1"]["text"] == "Diagram 2.1: Means of escape\nA plan of a house.\nLabels: Fd"
    assert C["definition-storey"]["text"] == "Storey: A floor level." and splits == []


def test_table_gives_a_whole_chunk_and_one_per_row_sentence_skipping_heading_rows():
    t = tree([sec("table-3.1", "table", "raw", number="3.1", title="Travel distance", columns=["Escape", "Max"],
                  grid=[["One direction", ""], ["Flats", "7.5m"], ["Houses", "9m"]], heading_rows=[0],
                  row_sentences=["Flats allow 7.5m.", "Houses allow 9m."])])
    C = by_suffix(chunk_tree(t, GUIDE, RECORD)[0])
    assert C["table-3.1"]["text"].startswith("Table 3.1 Travel distance\nEscape | Max\nOne direction | ")
    assert C["table-3.1#row-1"]["row"] == {"Escape": "Flats", "Max": "7.5m"}
    assert C["table-3.1#row-2"]["text"] == "Houses allow 9m." and C["table-3.1#row-2"]["chunk_type"] == "table-row"


def test_long_paragraph_is_split_at_list_items_and_reported(monkeypatch):
    monkeypatch.setattr(ch, "MAX_CHARS", 40)
    text = "Lead in to the list.\na. First item is here.\nb. Second item is here.\nc. Third."
    assert split_paragraphs(text, 40) == ["Lead in to the list.", "a. First item is here.",
                                          "b. Second item is here.\nc. Third."]
    chunks, splits = chunk_tree(tree([sec("para-1.1", "paragraph", text)]), GUIDE, RECORD)
    assert [c["id"].split(":")[-1] for c in chunks] == ["para-1.1#part-1", "para-1.1#part-2", "para-1.1#part-3"]
    assert splits == ["para-1.1: 77 characters, split into 3 parts"]


def test_dated_copies_resolve_to_the_copy_with_matching_dates():
    ids = {"para-b1-until-2029-09-01", "para-b1-from-2029-09-02", "table-c1-until-2029-09-01", "table-c1-from-2029-09-02"}
    new = find_refs("See paragraph B1 and Table C1.", "x", ids, {"valid_from": "2029-09-02"})
    assert [r["to_section"] for r in new] == ["para-b1-from-2029-09-02", "table-c1-from-2029-09-02"]
    old = find_refs("See paragraph B1.", "x", ids, {"valid_to": "2029-09-01"})
    assert old[0]["to_section"] == "para-b1-until-2029-09-01"


def test_references_to_the_building_regulations_and_unresolved_ones():
    refs = find_refs("Requirement B1 applies; see requirement B4 and regulation 7(2). Table 9.9 is missing.", "x",
                     {"table-3.1"}, {}, regs_in="br2010")
    assert {"words": "requirement B4", "to_source": "br2010", "to_section": "schedule-1-B4", "resolved": False} in refs
    assert any(r.get("to_section") == "regulation-7" and r.get("to_source") == "br2010" for r in refs)
    assert {"words": "Table 9.9", "to_section": None, "resolved": False} in refs


def test_legislation_regulations_split_when_long_and_regulation_2_gives_definitions(monkeypatch):
    monkeypatch.setattr(ch, "MAX_CHARS", 50)
    base = {"applies_to": "E+W", "url": "https://legislation/reg"}
    t = tree([sec("regulation-2", "regulation", "Interpretation (1) In these Regulations ...", title="Interpretation", **base),
              sec("regulation-3", "regulation", "Short rule.", title="Meaning", **base),
              sec("regulation-4", "regulation", "(1) A long rule that goes on. (2) And on and on and on and on.", **base),
              sec("regulation-4-1", "paragraph", "(1) A long rule that goes on.", "regulation-4", **base),
              sec("regulation-4-2", "paragraph", "(2) And on and on and on and on.", "regulation-4", **base),
              sec("schedule-1-B1", "requirement", "B1. Means of warning and escape ...", limits="Not prisons.", **base)],
             definitions=[{"term": "the Act", "text": "“the Act” means the Building Act 1984;", "section_id": "regulation-2"},
                          {"term": "designer", "text": "“designer” means any person who—", "section_id": "regulation-2"}])
    t["sections"][0]["text"] = ("(1) In these Regulations—\n“the Act” means the Building Act 1984;\n“designer” means any person "
                                "who—\ncarries out design work, or\narranges for it;\n“dwelling” includes a flat;")
    chunks, splits = chunk_tree(t, LAW, {})
    C = by_suffix(chunks)
    assert C["regulation-3"]["chunk_type"] == "regulation" and C["regulation-3"]["legal_weight"] == "law"
    assert "regulation-4" not in C and C["regulation-4-2"]["chunk_type"] == "clause"
    assert splits == ["regulation-4: 62 characters, split into 2 paragraphs"]
    assert C["regulation-2-term-the-act"]["text"].startswith("“the Act” means") and "regulation-2" not in C
    assert C["regulation-2-term-designer"]["text"] == "“designer” means any person who—\ncarries out design work, or\narranges for it;"
    assert C["schedule-1-B1"]["text"].endswith("Limits on application: Not prisons.")
    assert C["schedule-1-B1"]["applies_to"] == "E+W" and C["schedule-1-B1"]["url"] == "https://legislation/reg"


def test_figures_keep_the_image_display_flag():
    t = tree([sec("diagram-1.1", "figure", "D", number="1.1", title="D", image_path="corpus/x.png")], image_display=False)
    c = chunk_tree(t, GUIDE, RECORD)[0][0]
    assert c["image_path"] == "corpus/x.png" and c["image_display"] is False


# ---------------------------------------------------------------- real trees

def _real():
    trees = sorted((ROOT / "corpus" / "parsed").glob("*/*.json"))
    if not trees:
        pytest.skip("no parsed trees on this machine")
    sources = ch.load_sources()
    out = []
    for p in trees:
        t = json.loads(p.read_text(encoding="utf-8"))
        out.append(chunk_tree(t, sources.get(p.parent.name, {"id": p.parent.name}),
                              ch.version_record(p.parent.name, t["version_id"]))[0])
    return [c for cs in out for c in cs]


@pytest.fixture(scope="module")
def real_chunks():
    return _real()


def test_real_chunks_have_unique_ids_and_every_filter_field(real_chunks):
    ids = [c["id"] for c in real_chunks]
    assert len(ids) == len(set(ids))
    for c in real_chunks:
        for f in ("source_id", "kind", "legal_weight", "version_id", "valid_from", "section_id", "url", "text", "embed_text"):
            assert c.get(f), (c["id"], f)
        assert c["applies_to"], c["id"]


def test_real_chunks_have_no_page_furniture(real_chunks):
    for c in real_chunks:
        for bad in ("O N L I N E", "ONLINE VERSION", "Approved Document B Volume 1, 2019 edition Building",
                    "Health and Safety\nExecutive", "Page 1 of"):
            assert bad not in c["text"], (c["id"], bad)


# ---------------------------------------------------------------- safety net for giant chunks (overnight S3)

def test_a_giant_clause_is_split_into_parts_with_the_breadcrumb():
    big = "\n".join(f"(a{i}) " + "word " * 60 for i in range(80))  # about 24,000 characters in one paragraph
    t = tree([sec("regulation-6", "regulation", "(1) " + big, number="6", title="Amendments"),
              sec("regulation-6-1", "paragraph", "(1) " + big, parent="regulation-6", number="1")])
    chunks, _ = chunk_tree(t, LAW, RECORD)
    assert all(len(c["text"]) <= ch.HARD_MAX for c in chunks)
    parts = [c for c in chunks if "#part-" in c["id"]]
    assert len(parts) >= 8 and all(c["embed_text"].startswith("Doc ›") for c in parts)
    assert len({c["id"] for c in chunks}) == len(chunks)


def test_a_giant_table_keeps_its_title_and_header_on_every_part():
    rows = "\n".join(f"Item {i} | " + "detail " * 40 for i in range(120))
    t = tree([sec("schedule-3-table-1", "table", "Contract | Detail\n" + rows, title="Exempted contracts")])
    chunks, _ = chunk_tree(t, LAW, RECORD)
    parts = [c for c in chunks if "#part-" in c["id"]]
    assert len(parts) >= 3
    assert all(c["text"].splitlines()[0] == "Contract | Detail" for c in parts)


def test_control_characters_are_removed():
    t = tree([sec("para-1", "paragraph", "Fire doors\x07 should be FD30.")])
    chunks, _ = chunk_tree(t, GUIDE, RECORD)
    assert chunks[0]["text"] == "Fire doors should be FD30."
