"""Service layer against the seeded mock data."""

import datetime as dt

import pytest

from builders_api import quotas
from builders_api.errors import NotFoundError, QuotaExceededError, ValidationError
from builders_api.service import documents, jobs, payments, regulations

DEMO_DAY = dt.date(2026, 11, 21)


@pytest.fixture()
def firm(seeded):
    return jobs.firm_id("oakline")


def test_list_jobs_groups_recent_emails(firm):
    out = jobs.list_jobs(firm, since_days=1, now=dt.datetime(2026, 11, 21, 12, tzinfo=dt.timezone.utc))
    by_ref = {j["ref"]: j for j in out["jobs"]}
    assert set(by_ref) == {"ELM-22", "KWY-4", "RIV-12"}
    assert [e["subject"] for e in by_ref["KWY-4"]["recent_emails"]] == ["Unit 4 Kingsway: application for payment 2"]
    assert out["recent_emails_not_linked_to_a_job"] == []


def test_job_lookup_by_ref_or_words(firm):
    assert jobs.resolve_job(firm, "elm-22")["ref"] == "ELM-22"
    assert jobs.resolve_job(firm, "Kingsway")["ref"] == "KWY-4"
    with pytest.raises(NotFoundError):
        jobs.resolve_job(firm, "Mill Lane")
    with pytest.raises(ValidationError):
        jobs.resolve_job(firm, "Hollowell")  # in every address


def test_get_job_has_only_real_approvals_with_quotes(firm):
    facts = jobs.get_job(firm, "ELM-22")["facts"]
    approvals = [f for f in facts if f["type"] == "approval"]
    assert len(approvals) == 2
    assert all(f["quote"] and f["source"]["filename"].endswith(".txt") for f in approvals)
    assert any(f["type"] == "discussion" and "NOT approved" in f["summary"] for f in facts)


def test_missing_items_elm(firm):
    items = {i["item"]: i["status"] for i in jobs.list_missing_items(firm, "ELM-22", today=DEMO_DAY)["items"]}
    assert items["Electrical certificate"] == "missing"
    assert items["Final photos"] == "missing"
    assert items["Client approval for each change"] == "present"


def test_missing_items_flags_insurance(firm):
    items = {i["item"]: i for i in jobs.list_missing_items(firm, "KWY-4", today=DEMO_DAY)["items"]}
    ins = items["Subcontractor insurance in date"]
    assert ins["status"] == "some_expired"
    assert sorted(s["warning"] for s in ins["sources"]) == ["expired", "expiring soon"]


def test_search_filters_by_job_and_cites(firm):
    out = documents.search_job_documents(firm, "pocket door approved", job="ELM-22")
    assert out["results"] and all(r["job"] == "ELM-22" for r in out["results"])
    assert out["results"][0]["source"]["label"]
    assert documents.search_job_documents(firm, "pocket door", job="RIV-12")["results"] == []


def test_asbestos_facts_never_claim_absence_beyond_sample(firm):
    facts = [f for f in jobs.get_job(firm, "RIV-12")["facts"] if f["type"] == "asbestos_item"]
    hall = next(f for f in facts if f["detail"]["room"] == "Hall")
    assert "this sample only" in hall["summary"]
    assert any(f["detail"]["result"] == "presumed" for f in facts)


def test_payment_dates_moment_7(firm):
    out = payments.get_payment_dates(firm, "KWY-4", today=DEMO_DAY)
    assert out["next_deadline"] == {"date": "2026-11-30", "what": "payment_notice_by",
                                    "contract": "Fenwick Drylining Ltd", "party": "subcontract"}
    sub = next(c for c in out["contracts"] if c["party"] == "subcontract")
    assert sub["current_cycle"]["pay_less_notice_by"] == "2026-12-11"
    assert sub["source"]["filename"].startswith("Fenwick")


def test_regulations_fallback(seeded):
    out = regulations.search_regulations("what happens if I miss a pay less notice")
    assert out["backend"] == "fallback"
    top = out["passages"][0]
    assert top["section"].startswith("s111") and top["edition_date"] and top["url"].startswith("https://")
    with pytest.raises(ValidationError):
        regulations.search_regulations("wall", as_of_date="21/11/2026")


def test_quota_blocks_at_limit(firm, conn):
    conn.execute("update quota_limits set daily_limit = 2 where metric = 'tool_calls'")
    conn.commit()
    quotas.consume(firm, "tool_calls")
    quotas.consume(firm, "tool_calls")
    with pytest.raises(QuotaExceededError):
        quotas.consume(firm, "tool_calls")


def test_regulations_fallback_returns_nothing_for_unrelated_questions(seeded):
    assert regulations.search_regulations("Control of Asbestos Regulations regulation 5 duty to assess")["passages"] == []
    assert regulations.search_regulations("VAT domestic reverse charge for subcontractors")["passages"] == []
    hits = regulations.search_regulations("what happens if I miss a pay less notice")["passages"]
    assert hits and hits[0]["section"].startswith("s111")


def test_show_today_lists_jobs_by_days_left(firm):
    from builders_api.service import today
    out = today.show_today(firm, now=dt.datetime(2026, 11, 27, 9, tzinfo=dt.timezone.utc))
    assert out["today"] == "2026-11-27"
    refs = [j["ref"] for j in out["jobs"]]
    assert refs[0] == "RIV-12" and set(refs) == {"ELM-22", "KWY-4", "RIV-12"}
    riv = out["jobs"][0]
    assert riv["days_left"] == 0 and riv["due"] is True
    assert all(len(j["recent_emails"]) <= 3 for j in out["jobs"])
    assert out["emails_7_days"] == sum(j["email_count_7_days"] for j in out["jobs"])
