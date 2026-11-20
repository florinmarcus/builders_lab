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
    monkeypatch.setattr(S, "_vectors", None)  # never reuse vectors cached from the real corpus
    # Never call Bedrock from tests: CI has no AWS credentials, and each call costs money.
    # The stand-in keeps the order it was given.
    monkeypatch.setattr(S, "rerank", lambda question, texts, n: [(i, 1.0) for i in range(min(n, len(texts)))])
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


# ---------------------------------------------------------------- hybrid: vectors, RRF, re-rank (fake models)

def test_rrf_adds_one_over_k_plus_rank():
    a = [("x", {}), ("y", {})]
    b = [("y", {}), ("z", {})]
    out = S.rrf(a, b, k=60)
    assert [c for c, _, _ in out] == ["y", "x", "z"]
    assert out[0][2] == pytest.approx(1 / 62 + 1 / 61)


@pytest.fixture
def vectors(index, monkeypatch):
    np = pytest.importorskip("numpy")
    vec_dir = index / "vectors" / "demo"
    vec_dir.mkdir(parents=True)
    ids = ["a", "b", "c", "d", "e"]
    mat = np.eye(5, dtype=np.float32)  # chunk i points along axis i
    np.save(vec_dir / "v1.npy", mat)
    (vec_dir / "v1.ids.json").write_text(json.dumps([{"id": i, "fp": i} for i in ids]))
    monkeypatch.setattr(S, "_vectors", None)
    yield
    S._vectors = None


def fake_embed(axis):
    return lambda text: ([1.0 if i == axis else 0.0 for i in range(5)], 3)


def test_vector_mode_finds_a_paraphrase_keywords_miss(vectors):
    # "money due" shares no word with chunk e ("payment notice"), but its vector points at e
    assert S.search("money due", datetime.date(2027, 1, 1), mode="keyword", use_rerank=False) == []
    got = S.search("money due", datetime.date(2027, 1, 1), mode="vector", use_rerank=False, embed=fake_embed(4))
    assert got[0]["chunk_id"] == "e"


def test_hybrid_keeps_filters_and_reranks(vectors):
    calls = {}

    def fake_rerank(question, texts, n):
        calls["texts"] = texts
        return [(len(texts) - 1, 0.9), (0, 0.5)]  # put the last candidate first

    got = S.search("fire doorsets", datetime.date(2027, 1, 1), mode="hybrid", embed=fake_embed(3),
                   use_rerank=True, rerank_fn=fake_rerank)
    ids = [p["chunk_id"] for p in got]
    assert "d" not in ids and "c" not in ids  # Wales-only and not yet in force, from either list
    assert got[0]["score"] == 0.9 and len(got) == 2
    assert all("›" in t for t in calls["texts"])  # the re-ranker sees breadcrumb + text


def test_no_vectors_falls_back_to_keywords(index, monkeypatch):
    monkeypatch.setattr(S, "_vectors", None)
    got = S.search("fire doorsets FD30", datetime.date(2027, 1, 1), mode="hybrid", use_rerank=False)
    assert got[0]["chunk_id"] == "a"
