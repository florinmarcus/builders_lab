"""about_regulations_library (S100): the built library file, the live database part and the service."""

import datetime
import json
import os
import uuid

import pytest

from builders_api.errors import UpstreamError, ValidationError
from builders_api.service import regulations
from system.rag import library
from system.rag import pgsearch as P


def test_library_file_is_up_to_date_with_sources_yaml():
    assert library.OUT.read_text() == library.render(library.build()), "run: python -m system.rag.library"


def test_reasons_come_from_sources_yaml_fields():
    r = library.reason_of
    assert r({"mode": "ingest", "kind": "legislation"}) is None
    assert r({"mode": "ingest", "kind": "hse-guidance", "language": "ro"}) == "not_english"
    assert r({"mode": "link_only", "kind": "standard", "status": "current"}) == "paid_standard"
    assert r({"mode": "link_only", "kind": "standard", "status": "withdrawn"}) == "withdrawn"
    assert r({"mode": "link_only", "kind": "contract"}) == "paid_contract"
    assert r({"mode": "restricted", "kind": "guidance"}) == "licence_unclear"
    assert r({"mode": "link_only", "kind": "guidance", "licence": "proprietary"}) == "link_only"


def test_known_gaps_are_listed():
    titles = " ".join(g["title"] for g in json.loads(library.OUT.read_text())["not_held"])
    assert "BS 7671" in titles and "JCT" in titles


def test_summary_in_fallback_mode_is_short_and_honest(monkeypatch):
    monkeypatch.setattr(regulations, "_corpus_about", lambda: None)
    out = regulations.about_regulations_library()
    assert out["version"]["backend"] == "fallback" and "not connected" in out["version"]["note"]
    assert out["version"]["nation"] == "England" and out["version"]["versions_in_force_from"] == "2025-01-01"
    assert out["gaps"]["not_held"][0]["examples"] and out["gaps"]["scope"]
    assert "not measured" in out["quality"]
    assert len(json.dumps(out)) < 8000


def fake_about():
    return {"loaded_at": "2026-11-24T10:00:00+00:00", "schema_version": 3, "passages": 120,
            "sources": [{"source_id": "car2012", "title": "Control of Asbestos Regulations 2012", "legal_weight": "law",
                         "passages": 100, "versions": 1, "edition_date": "2012-04-06", "next_from": None,
                         "url": "https://www.legislation.gov.uk/uksi/2012/632"},
                        {"source_id": "new-doc", "title": "A document not in sources.yaml", "legal_weight": "guidance",
                         "passages": 20, "versions": 2, "edition_date": "2025-06-01", "next_from": "2027-01-01",
                         "url": "https://example.gov.uk/x"}]}


def test_live_library_merges_database_and_sources(monkeypatch):
    monkeypatch.setattr(regulations, "_corpus_about", lambda: fake_about)
    out = regulations.about_regulations_library("summary")
    v = out["version"]
    assert (v["backend"], v["documents"], v["passages"], v["loaded_at"]) == ("corpus", 2, 120, "2026-11-24T10:00:00+00:00")
    assert {t["type"] for t in out["contents"]["by_type"]} == {"law", "guidance"}
    assert out["gaps"]["listed_but_not_loaded"] == len(library.build()["documents"]) - 1
    docs = regulations.about_regulations_library("contents")["documents"]
    assert docs[0]["type"] == "law" and docs[0]["publisher"]  # publisher comes from sources.yaml
    assert docs[1]["newer_version_from"] == "2027-01-01"
    gaps = regulations.about_regulations_library("gaps")
    assert gaps["not_held"][0]["documents"][0]["url"] and gaps["listed_but_not_loaded"]["documents"]


def test_bad_part_and_database_trouble(monkeypatch):
    with pytest.raises(ValidationError):
        regulations.about_regulations_library("everything")

    def broken():
        raise P.SearchError("timeout")
    monkeypatch.setattr(regulations, "_corpus_about", lambda: broken)
    monkeypatch.setattr(regulations, "with_retries", lambda fn: fn())
    with pytest.raises(UpstreamError) as e:
        regulations.about_regulations_library()
    assert e.value.retryable


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="needs Postgres")
def test_about_reads_stats_and_documents_in_force():
    import psycopg
    url, s = os.environ["TEST_DATABASE_URL"], "about_" + uuid.uuid4().hex[:8]
    with psycopg.connect(url, autocommit=True) as c:
        c.execute(f"CREATE SCHEMA {s}")
        try:
            c.execute(f"CREATE TABLE {s}.stats (schema_version int, chunk_count int, avg_len float8, "
                      "loaded_at timestamptz, sources jsonb)")
            c.execute(f"CREATE TABLE {s}.chunks (source_id text, source_title text, legal_weight text, version_id text, "
                      "edition_date date, valid_from date, valid_to date, url text)")
            c.execute(f"INSERT INTO {s}.stats VALUES (3, 4, 100, '2026-11-24 10:00+00', '[]')")
            c.execute(f"""INSERT INTO {s}.chunks VALUES
                ('adb', 'AD B', 'statutory-guidance', 'v2025', '2025-03-02', '2025-03-02', NULL, 'https://x/2025'),
                ('adb', 'AD B', 'statutory-guidance', 'v2025', '2025-03-02', '2025-03-02', NULL, 'https://x/2025'),
                ('adb', 'AD B', 'statutory-guidance', 'v2029', '2026-09-30', '2029-09-01', NULL, 'https://x/2029'),
                ('old', 'Old guide', 'guidance', 'v1', '2019-01-01', '2019-01-01', '2024-12-31', 'https://x/old')""")
            out = P.about(url, schema=s, today=datetime.date(2026, 11, 25))
        finally:
            c.execute(f"DROP SCHEMA {s} CASCADE")
    assert out["passages"] == 4 and out["schema_version"] == 3 and out["loaded_at"].startswith("2026-11-24")
    (adb,) = out["sources"]  # the old guide ended before today
    assert (adb["passages"], adb["versions"], adb["edition_date"], adb["next_from"]) == (3, 2, "2025-03-02", "2029-09-01")
    assert adb["url"] == "https://x/2025"  # the link of the version in force today
