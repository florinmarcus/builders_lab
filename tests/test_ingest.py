"""Ingestion from .eml files, job filing, sync_inbox hand-over, save_facts checks, and seed keeping keys."""

import datetime as dt
import sys
from pathlib import Path

import pytest

pytest.importorskip("reportlab")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system" / "data" / "mock"))
from generate import generate  # noqa: E402

from builders_api.admin import create_key, list_keys  # noqa: E402
from builders_api.db.seed import seed  # noqa: E402
from builders_api.errors import NotFoundError  # noqa: E402
from builders_api.service import facts, inbox, jobs  # noqa: E402


@pytest.fixture()
def firm(seeded, tmp_path, monkeypatch):
    out = tmp_path / "mail"
    generate(out, dt.date(2026, 11, 21))
    monkeypatch.setenv("MAIL_SOURCE", f"eml:{out}")
    return jobs.firm_id("oakline")


def _email(conn, subject_part):
    return conn.execute("select e.id, j.ref, e.filing_reason from emails e left join jobs j on j.id = e.job_id "
                        "where e.subject like %s", (f"%{subject_part}%",)).fetchone()


def test_sync_is_idempotent_and_files_by_job(firm, conn):
    first = inbox.sync_inbox(firm)
    assert first["counts"] == {"new": 9, "already_had": 11, "failed": 0}
    assert inbox.sync_inbox(firm)["counts"]["new"] == 0
    assert _email(conn, "brief and drawing schedule")[1] == "ELM-22"
    assert _email(conn, "Final account?")[1] == "ELM-22"          # by sender history
    assert "sender" in _email(conn, "Final account?")[2]
    assert _email(conn, "completion by 27 Nov")[1] == "RIV-12"
    assert _email(conn, "Flooring quote")[1] == "ELM-22"           # from the attachment text
    pdf = conn.execute("select page_count, text_content from attachments where filename like 'Ashby%'").fetchone()
    assert pdf[0] == 1 and "Supply and fit" in pdf[1]


def test_hand_over_and_save_facts_checks(firm, conn):
    out = inbox.sync_inbox(firm)
    assert out["more_waiting"] and len(out["emails_needing_facts"]) == 10
    target = next(e for e in out["emails_needing_facts"] if "brief and drawing schedule" in e["source"]["subject"])
    result = facts.save_facts(firm, target["email_id"], "ELM-22", [], [
        {"fact_type": "key_date", "summary": "Client wants a start before end of October",
         "quote": "Victoria wants work to start  before the end of October"},
        {"fact_type": "approval", "summary": "Invented", "quote": "Yes, add the conservatory"},
        {"fact_type": "nonsense", "summary": "x", "quote": "drawing schedule"},
    ], "tools/save_facts.v1")
    assert result["saved"]["facts"] == 1
    reasons = [r["reason"] for r in result["rejected"]]
    assert any("not found word for word" in r for r in reasons) and any("unknown fact_type" in r for r in reasons)
    again = inbox.sync_inbox(firm)["emails_needing_facts"]
    assert target["email_id"] not in [e["email_id"] for e in again]
    # calling again replaces, not duplicates
    facts.save_facts(firm, target["email_id"], None, [], [
        {"fact_type": "key_date", "summary": "Start before end of October", "quote": "start before the end of October"}],
        "tools/save_facts.v1")
    n = conn.execute("select count(*) from facts where email_id = %s", (target["email_id"],)).fetchone()[0]
    assert n == 1


def test_attachment_types_and_expiry(firm, conn):
    out = inbox.sync_inbox(firm)
    e14 = next(e for e in out["emails_needing_facts"] if "interim application 2" in e["source"]["subject"])
    att = e14["attachments"][0]
    r = facts.save_facts(firm, e14["email_id"], "KWY-4",
                         [{"attachment_id": att["attachment_id"], "document_type": "application_for_payment",
                           "document_date": "2026-10-28"}], [], "tools/save_facts.v1")
    assert r["saved"] == {"facts": 0, "attachments": 1}
    row = conn.execute("select document_type, document_date from attachments where id = %s", (att["attachment_id"],)).fetchone()
    assert row[0] == "application_for_payment" and row[1] == dt.date(2026, 10, 28)


def test_unknown_email(firm):
    with pytest.raises(NotFoundError):
        facts.save_facts(firm, "00000000-0000-0000-0000-000000000000", None, [], [], "v")


def test_reseed_keeps_api_keys(seeded):
    create_key("oakline", "keep me", dt.date(2027, 1, 1))
    seed(seeded)
    assert [k["label"] for k in list_keys("oakline")] == ["keep me"]
