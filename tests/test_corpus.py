"""Offline tests for the corpus catalogue and version store."""

import json
from datetime import date
import re
from pathlib import Path

import pytest

from system.rag.corpus import (
    Fetched,
    Store,
    check_chain,
    content_hash,
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


LEG_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Legislation xmlns="http://www.legislation.gov.uk/namespaces/legislation"
  xmlns:ukm="http://www.legislation.gov.uk/namespaces/metadata"
  xmlns:dc="http://purl.org/dc/elements/1.1/" RestrictStartDate="2010-10-01">
<ukm:Metadata><dc:modified>{modified}</dc:modified><ukm:UnappliedEffects>{effects}</ukm:UnappliedEffects></ukm:Metadata>
<Primary><P1 id="regulation-2" {attrs}><Text>{text}</Text></P1></Primary>
</Legislation>"""


def leg_xml(text="Building work means...", modified="2026-11-06",
            effects='<ukm:UnappliedEffect A="1" B="2"/>', attrs='Status="valid" Extent="E+W"') -> bytes:
    return LEG_XML.format(text=text, modified=modified, effects=effects, attrs=attrs).encode("utf-8")


def test_xml_content_hash_ignores_metadata_and_attribute_order():
    base = content_hash(leg_xml(), "application/xml")
    # Metadata changes (dates, unapplied effects, their attribute order) are not a new version.
    assert content_hash(leg_xml(modified="2026-11-20"), "application/xml") == base
    assert content_hash(leg_xml(effects='<ukm:UnappliedEffect B="2" A="1"/><ukm:UnappliedEffect C="3"/>'),
                        "application/xml") == base
    # Attribute order in the law text is not a change either.
    assert content_hash(leg_xml(attrs='Extent="E+W" Status="valid"'), "application/xml") == base
    # A change to the law text, or its attributes, is.
    assert content_hash(leg_xml(text="Building work means, in Wales..."), "application/xml") != base
    assert content_hash(leg_xml(attrs='Status="repealed" Extent="E+W"'), "application/xml") != base
    # The exact-file hash still sees every byte.
    assert sha256(leg_xml(modified="2026-11-20")) != sha256(leg_xml())


def test_xml_content_hash_falls_back_to_bytes_when_unparsable():
    assert content_hash(b"<not xml", "application/xml") == sha256(b"<not xml")


def test_xml_content_hash_on_real_building_regulations_file():
    raws = sorted((Path(__file__).parent.parent / "corpus" / "raw" / "br2010" / "main").glob("*.xml"))
    if not raws:
        pytest.skip("raw files not on this machine")
    data = raws[0].read_bytes()
    restamped = re.sub(rb"<dc:modified>[^<]*</dc:modified>", b"<dc:modified>1999-01-01</dc:modified>", data)
    assert restamped != data
    assert content_hash(restamped, "application/xml") == content_hash(data, "application/xml")
    assert content_hash(data, "application/xml") != sha256(data)


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


def _drop_raw(store, rec):
    raw = store.rel_base / rec["raw_path"]
    raw.unlink()
    return raw


def test_restore_writes_missing_raw_file_when_hash_matches(store):
    rec = store.add(SRC, doc("2024-01-01", b"v1"))
    raw = _drop_raw(store, rec)
    assert store.add(SRC, doc("2024-01-01", b"v1")) is None  # no new version
    assert raw.read_bytes() == b"v1"
    assert store.restored == [rec["raw_path"]]
    assert len(store.records("demo")) == 1


def test_restore_old_version_too(store):
    old = store.add(SRC, doc("2024-01-01", b"v1"))
    store.add(SRC, doc("2024-06-01", b"v2"))
    raw = _drop_raw(store, old)
    assert store.add(SRC, doc("2024-01-01", b"v1")) is None
    assert raw.read_bytes() == b"v1"
    assert len(store.records("demo")) == 2


def test_restore_legislation_date_with_same_bytes(store):
    rec = store.add(SRC, leg("2015-01-01", b"b"))
    raw = _drop_raw(store, rec)
    assert store.needs_date("demo", "main", "2015-01-01")
    assert store.add(SRC, leg("2015-01-01", b"b")) is None
    assert raw.read_bytes() == b"b"
    assert not store.needs_date("demo", "main", "2015-01-01")


def test_restore_mismatch_writes_nothing_and_is_listed(store):
    rec = store.add(SRC, leg("2015-01-01", b"b"))
    raw = _drop_raw(store, rec)
    assert store.add(SRC, leg("2015-01-01", b"b-changed")) is None
    assert not raw.exists()
    assert not list((store.raw_dir / "demo" / "main").iterdir())
    assert store.mismatched == [rec["raw_path"]]
    assert store.restored == []


def test_present_raw_file_is_left_alone(store):
    store.add(SRC, doc("2024-01-01", b"v1"))
    assert store.add(SRC, doc("2024-01-01", b"v1")) is None
    assert store.restored == [] and store.mismatched == []
    assert not store.needs_date("demo", "main", "2024-01-01")


def test_needs_date_for_unknown_date(store):
    assert store.needs_date("demo", "main", "2015-01-01")


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


# ---------------------------------------------------------------- scope (ADR 0016, S115)

from system.rag.corpus import SCOPE_FROM, force_period, in_scope, scope_counts, version_in_scope  # noqa: E402

ROOT = Path(__file__).parent.parent


def test_scope_rule_keeps_current_versions_and_those_in_force_from_2025():
    assert SCOPE_FROM == "2025-01-01"
    assert in_scope({"valid_to": None})
    assert in_scope({"valid_to": "2025-01-01"})  # the rule as decided: valid_to on or after 1 January 2025
    assert in_scope({"valid_to": "2025-03-02"})
    assert not in_scope({"valid_to": "2024-12-31"})
    assert not in_scope({"valid_to": "2010-10-01"})


def test_source_dates_override_a_records_open_end():
    src = {"in_force_parts": {"old": {"from": date(2019, 8, 30), "to": date(2020, 11, 26), "why": "page 2"},
                              "late": {"to": "2025-03-02", "why": "page 3"}}}
    old = {"part": "old", "valid_from": "2025-01-14", "valid_to": None}
    assert force_period(old, src) == ("2019-08-30", "2020-11-26") and not in_scope(old, src)
    late = {"part": "late", "valid_from": "2025-01-14", "valid_to": None}
    assert force_period(late, src) == ("2025-01-14", "2025-03-02") and in_scope(late, src)
    other = {"part": "other", "valid_from": "2025-01-14", "valid_to": None}
    assert force_period(other, src) == ("2025-01-14", None) and in_scope(other, src)


def test_in_force_parts_need_a_date_and_a_reason():
    base = {"id": "x", "title": "X", "publisher": "P", "url": "https://x", "kind": "guidance", "licence": "OGL-3.0",
            "mode": "ingest", "priority": 3, "why": "w", "checked": "2026-11-22", "fetch": {"method": "none"}}
    good = {**base, "in_force_parts": {"a": {"to": date(2019, 8, 30), "why": "page 2"}}}
    assert validate_sources({"sources": [good]}) == []
    for bad in ({"to": "2019"}, {"to": "2019-08-30"}, {"why": "w"}, {"to": "2019-08-30", "why": "w", "from": "x"}):
        errs = validate_sources({"sources": [{**base, "in_force_parts": {"a": bad}}]})
        assert errs and "in_force_parts a" in errs[0]


def test_version_in_scope_and_counts_read_the_records(tmp_path):
    corpus = tmp_path / "corpus"
    (corpus / "versions" / "demo").mkdir(parents=True)
    for vid, vt in (("main@2010", "2024-04-06"), ("main@2024", "2026-01-01"), ("main@2026", None)):
        (corpus / "versions" / "demo" / f"{vid}.json").write_text(json.dumps(
            {"source_id": "demo", "part": "main", "version_id": vid, "valid_from": "2010-01-01", "valid_to": vt}))
    assert not version_in_scope("demo", "main@2010", corpus)
    assert version_in_scope("demo", "main@2024", corpus) and version_in_scope("demo", "main@2026", corpus)
    assert version_in_scope("demo", "no-record", corpus)  # nothing says it is old
    assert scope_counts(corpus) == {"demo": (2, 1)}


def test_real_adb_historical_keeps_only_the_editions_in_force_from_2025():
    """AD B 2019 edition with the 2020 and 2022 amendments (in force on 1 January 2025) and the text collated with
    the 2025, 2026 and 2029 amendments, both volumes; every older edition and booklet is out (documents' own dates)."""
    srcs = {s["id"]: s for s in load_sources()["sources"]}
    src = srcs["adb-historical"]
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "versions" / "adb-historical").glob("*.json")]
    assert len(recs) == 17 and set(src["in_force_parts"]) == {r["part"] for r in recs}
    kept = sorted(r["part_title"] for r in recs if in_scope(r, src))
    assert len(kept) == 4
    assert all("2019 edition incorporating 2020 and 2022 amendments" in t for t in kept)
    assert sum("collated with 2025, 2026 and 2029" in t for t in kept) == 2


def test_accept_refetch_writes_dated_legislation_file_and_lists_it(store):
    """S126: with accept_refetch, a missing dated legislation file is written from a fresh download whose bytes differ,
    listed with both SHA-256 values; the record is not changed. Without the option it stays a mismatch."""
    rec = store.add(SRC, leg("2015-01-01", b"b"))
    raw = _drop_raw(store, rec)
    store.accept_refetch = True
    assert store.add(SRC, leg("2015-01-01", b"b-new-metadata")) is None
    assert raw.read_bytes() == b"b-new-metadata"
    assert store.mismatched == [] and len(store.refetched) == 1
    e = store.refetched[0]
    assert e["record_sha256"] == rec["sha256"] and e["file_sha256"] != rec["sha256"]
    assert e["text_check"].startswith(("same text", "not verifiable"))
    assert store.records("demo")[0]["sha256"] == rec["sha256"]  # record untouched
