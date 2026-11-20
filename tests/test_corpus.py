"""Offline tests for the corpus catalogue and version store."""

import json
from pathlib import Path

import pytest

from system.rag.corpus import (
    Fetched,
    Store,
    check_chain,
    load_sources,
    part_key,
    sha256,
    validate_sources,
)

SRC = {"id": "demo", "mode": "ingest", "licence": "OGL-3.0"}


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "corpus")


def leg(d: str, body: bytes) -> Fetched:
    return Fetched("main", "Demo Regs", body, "application/xml", f"https://x/{d}", d, d, "point_in_time", True)


def doc(d: str, body: bytes, part: str = "main") -> Fetched:
    return Fetched(part, "Demo guide", body, "application/pdf", "https://x/demo.pdf", d, d, "published")


def test_hash_and_raw_file(store):
    rec = store.add(SRC, doc("2024-01-01", b"v1"))
    raw = store.rel_base / rec["raw_path"]
    assert raw.read_bytes() == b"v1"
    assert rec["sha256"] == sha256(b"v1")
    assert rec["raw_path"].startswith("corpus/raw/demo/main/")
    assert rec["valid_to"] is None


def test_same_content_adds_nothing(store):
    assert store.add(SRC, doc("2024-01-01", b"v1"))
    assert store.add(SRC, doc("2024-01-01", b"v1")) is None
    assert len(store.records("demo")) == 1


def test_new_hash_closes_old_version(store):
    old = store.add(SRC, doc("2024-01-01", b"v1"))
    new = store.add(SRC, doc("2025-06-01", b"v2"))
    recs = store.records("demo")
    assert len(recs) == 2
    assert recs[0]["version_id"] == old["version_id"]
    assert recs[0]["valid_to"] == "2025-06-01"
    assert recs[1]["valid_to"] is None
    assert check_chain(recs) == []
    # The old raw file is kept.
    assert (store.rel_base / old["raw_path"]).read_bytes() == b"v1"
    assert new["raw_path"] != old["raw_path"]


def test_new_version_with_same_publish_date_starts_today(store):
    store.add(SRC, doc("2024-01-01", b"v1"))
    new = store.add(SRC, doc("2024-01-01", b"v2"))
    assert new["valid_from"] > "2024-01-01"
    assert new["valid_from_basis"] == "first_seen"
    assert check_chain(store.records("demo")) == []


def test_second_change_on_same_day_keeps_chain(store):
    store.add(SRC, doc("2024-01-01", b"v1"))
    store.add(SRC, doc("2024-01-01", b"v2"))
    store.add(SRC, doc("2024-01-01", b"v3"))
    recs = store.records("demo")
    assert len(recs) == 3
    assert check_chain(recs) == []


def test_html_change_detection_ignores_markup_noise(store):
    a = b'<html><body><div id="x1">Asbestos rules</div><script>t=1</script></body></html>'
    b = b'<html><body><div id="x2">Asbestos rules</div><script>t=2</script></body></html>'
    c = b'<html><body><div id="x2">Asbestos rules changed</div></body></html>'
    page = lambda body: Fetched("main", "Page", body, "text/html", "https://x/p", None, "2024-01-01", "first_seen")
    assert store.add(SRC, page(a))
    assert store.add(SRC, page(b)) is None
    assert store.add(SRC, page(c))


def test_parts_have_separate_chains(store):
    store.add(SRC, doc("2024-01-01", b"a1", part="vol1"))
    store.add(SRC, doc("2024-01-01", b"b1", part="vol2"))
    store.add(SRC, doc("2025-01-01", b"a2", part="vol1"))
    assert len(store.records("demo", "vol1")) == 2
    assert store.records("demo", "vol2")[0]["valid_to"] is None


def test_legislation_history_chain_and_backfill(store):
    for d, b in [("2012-04-06", b"a"), ("2015-01-01", b"b"), ("2020-12-31", b"c")]:
        store.add(SRC, leg(d, b))
    # Same date again: skipped even if the bytes differ slightly.
    assert store.add(SRC, leg("2015-01-01", b"b2")) is None
    # Back-fill an older version: it closes against the next one.
    rec = store.add(SRC, leg("2010-10-01", b"z"))
    assert rec["valid_to"] == "2012-04-06"
    recs = store.records("demo")
    assert [r["valid_from"] for r in recs] == ["2010-10-01", "2012-04-06", "2015-01-01", "2020-12-31"]
    assert check_chain(recs) == []


def test_records_are_json_on_disk(store):
    rec = store.add(SRC, doc("2024-01-01", b"v1"))
    path = store.versions_dir / "demo" / f"{rec['version_id']}.json"
    data = json.loads(path.read_text())
    for key in ["source_id", "version_id", "valid_from", "valid_to", "sha256", "fetched_at", "raw_path", "s3_key"]:
        assert key in data


def test_part_key_drops_edition_text():
    a = part_key("Approved Document B (fire safety) volume 1: Dwellings, 2019 edition incorporating 2020 amendments")
    b = part_key("Approved Document B (fire safety) volume 1: Dwellings, 2019 edition incorporating 2020, 2022 and 2025 amendments")
    assert a == b == "approved-document-b-fire-safety-volume-1-dwellings"
    assert part_key("2026 amendments to Approved Document B") != part_key("2025 amendments to Approved Document B")


def test_validate_catches_bad_entries():
    bad = {"sources": [
        {"id": "Bad Id", "mode": "ingest", "licence": "proprietary", "fetch": {"method": "url"}},
        {"id": "x", "title": "t", "publisher": "p", "url": "u", "kind": "standard", "licence": "proprietary",
         "mode": "link_only", "priority": 1, "why": "w", "checked": "2026-11-19", "fetch": {"method": "url"}},
    ]}
    errs = validate_sources(bad)
    assert any("bad id" in e for e in errs)
    assert any("ingest needs OGL-3.0" in e for e in errs)
    assert any("link_only must not be fetched" in e for e in errs)


def test_real_sources_yaml_is_valid():
    path = Path(__file__).resolve().parents[1] / "corpus" / "sources.yaml"
    if not path.exists():
        pytest.skip("sources.yaml not written yet")
    assert validate_sources(load_sources(path)) == []
