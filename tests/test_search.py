"""Tests for keyword search (system/rag/search.py) on a small hand-made chunk set."""

import datetime
import json

import pytest

from system.rag import search as S


def chunk(cid, text, path, **kw):
    base = {"id": cid, "text": text, "embed_text": " › ".join(path) + "\n" + text, "heading_path": path,
            "source_id": kw.get("source_id", "adb"), "source_title": kw.get("source_title", "Approved Document B"),
            "legal_weight": kw.get("legal_weight", "statutory-guidance"), "kind": "approved-document",
            "version_id": "v1", "edition_date": "2026-09-30", "valid_from": kw.get("valid_from", "2026-09-30"),
            "valid_to": kw.get("valid_to"), "applies_to": kw.get("applies_to", "E"),
            "section_id": kw.get("section_id", cid), "section_number": None, "section_title": None,
            "printed_page": "13", "url": "https://example.org#page=25", "chunk_type": "paragraph"}
    return base


@pytest.fixture
def index(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    (corpus / "chunks" / "demo").mkdir(parents=True)
    rows = [
        chunk("a", "Fire doorsets should be FD30 between the stair and the flat.", ["AD B", "Section 3", "Paragraph 3.22"]),
        chunk("b", "Old appendix text on fire doorsets.", ["AD B", "Appendix C", "Paragraph C1"],
              section_id="para-c1-until", valid_to="2029-09-01"),
        chunk("c", "New appendix text on fire doorsets.", ["AD B", "Appendix C", "Paragraph C1"],
              section_id="para-c1-from", valid_from="2029-09-02"),
        chunk("d", "Wales only rule about fire doorsets.", ["Regs", "Regulation 6"], applies_to="W",
              source_id="br2010", legal_weight="law"),
        chunk("e", "A payment notice must be given within five days.", ["Act", "Section 110A", "(3)"],
              source_id="hgcra", legal_weight="law", section_id="section-110A-3"),
    ]
    (corpus / "chunks" / "demo" / "v1.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(S, "CORPUS_DIR", corpus)
    monkeypatch.setenv("RAG_INDEX", str(tmp_path / "idx.sqlite"))
    assert S.build() == 5
    return corpus


def test_passages_follow_the_server_contract(index):
    p = S.search("fire doorsets FD30", datetime.date(2027, 1, 1))[0]
    assert p["section"] == "Paragraph 3.22" and p["edition_date"] == "2026-09-30" and p["url"]
    assert {"text", "source", "section", "edition_date", "url", "legal_weight", "chunk_id"} <= set(p)


def test_codes_match_whole(index):
    assert S.search("what is FD30", datetime.date(2027, 1, 1))[0]["chunk_id"] == "a"


def test_dates_pick_the_copy_in_force_and_country_defaults_to_england(index):
    ids = [p["chunk_id"] for p in S.search("appendix fire doorsets", datetime.date(2027, 1, 1))]
    assert "b" in ids and "c" not in ids and "d" not in ids
    later = [p["chunk_id"] for p in S.search("appendix fire doorsets", datetime.date(2030, 1, 1))]
    assert "c" in later and "b" not in later
    assert "d" in [p["chunk_id"] for p in S.search("fire doorsets", datetime.date(2027, 1, 1), country="W")]


def test_a_bare_clause_number_shows_its_section(index):
    p = S.search("payment notice days", datetime.date(2027, 1, 1))[0]
    assert p["section"] == "Section 110A (3)" and p["legal_weight"] == "law"


def test_no_words_no_results_and_missing_index_is_an_error(index, tmp_path, monkeypatch):
    assert S.search("the and of") == []
    monkeypatch.setenv("RAG_INDEX", str(tmp_path / "missing.sqlite"))
    with pytest.raises(FileNotFoundError):
        S.search("fire")
