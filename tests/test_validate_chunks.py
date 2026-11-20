"""Chunk validation (system/rag/validate_chunks.py, corpus/OVERNIGHT-PLAN.md S3)."""

import json

from system.rag import validate_chunks as V


def chunk(**kw):
    base = {"id": "demo:v1:para-1", "source_id": "demo", "version_id": "v1", "section_id": "para-1",
            "text": "Fire doors should be FD30.", "embed_text": "Doc › Para 1\nFire doors should be FD30.",
            "heading_path": ["Doc", "Para 1"], "url": "https://example.org", "valid_from": "2026-01-01",
            "legal_weight": "guidance", "kind": "guidance", "chunk_type": "paragraph"}
    base.update(kw)
    return base


def test_a_good_chunk_has_no_problems():
    errors, warnings = V.check_chunk(chunk())
    assert errors == [] and warnings == []


def test_missing_fields_and_empty_text_are_errors():
    errors, _ = V.check_chunk(chunk(text="", url=None, heading_path=[]))
    assert any("text" in e for e in errors) and any("url" in e for e in errors) and any("heading_path" in e for e in errors)


def test_page_furniture_left_in_text_is_an_error():
    for junk in ("O N L I N E V E R S I O N", "Asbestos: The survey guide Page 10 of 73", "■■ bullet"):
        errors, _ = V.check_chunk(chunk(text=f"Fire doors. {junk}"))
        assert errors, junk


def test_too_long_for_one_embedding_is_an_error_and_long_is_a_warning():
    errors, _ = V.check_chunk(chunk(text="word " * 6000))
    assert any("too long" in e for e in errors)
    errors, warnings = V.check_chunk(chunk(text="word " * 900))
    assert not errors and any("long" in w for w in warnings)


def test_tiny_chunks_are_warnings():
    _, warnings = V.check_chunk(chunk(text="See above."))
    assert any("short" in w for w in warnings)


def test_duplicate_ids_across_files_are_errors(tmp_path):
    d = tmp_path / "chunks" / "demo"
    d.mkdir(parents=True)
    (d / "v1.jsonl").write_text(json.dumps(chunk()) + "\n" + json.dumps(chunk()) + "\n", encoding="utf-8")
    report = V.validate(tmp_path / "chunks")
    assert report["chunks"] == 2 and any("duplicate id" in e for e in report["errors"])
