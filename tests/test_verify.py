"""verify_answer: deterministic grounding and guardrail checks."""

import datetime as dt

import pytest

from builders_api.service import jobs, verify

NOTICE = "AI-generated, check before use."


@pytest.fixture()
def firm(seeded):
    return jobs.firm_id("oakline")


def _chat(conn):
    return str(conn.execute("select id from attachments where filename like 'WhatsApp%'").fetchone()[0])


def test_grounded_answer_passes(firm, conn):
    chat = _chat(conn)
    text = f"Victoria approved underfloor heating (£2,400 + VAT) on 3 Nov and the pocket door (£850). {NOTICE}"
    v = verify.verify_answer(firm, text, [
        {"id": "c1", "quote": "Yes, go ahead with the underfloor heating in the kitchen.", "source": {"type": "document", "id": chat}},
        {"id": "c2", "quote": "Approved, thanks. Pocket door it is.", "source": {"type": "document", "id": chat}},
    ])
    assert v["pass"], v["problems"]


def test_invented_number_and_quote_fail(firm, conn):
    chat = _chat(conn)
    v = verify.verify_answer(firm, f"Garden lighting approved for £1,950. {NOTICE}", [
        {"id": "c1", "quote": "Garden lighting approved", "source": {"type": "document", "id": chat}}])
    codes = {p["code"] for p in v["problems"]}
    assert not v["pass"] and {"QUOTE_NOT_IN_SOURCE", "NUMBER_NOT_IN_SOURCES"} <= codes


def test_guardrails(firm):
    v = verify.verify_answer(firm, "Bedroom 2 has no asbestos. I have sent the invoice. Call 07700 900123.", [])
    codes = [p["code"] for p in v["problems"]]
    assert codes.count("BANNED_PHRASE") == 2 and "MISSING_AI_NOTICE" in codes
    assert any(p["code"] == "PERSONAL_DATA" and p["severity"] == "warning" for p in v["problems"])


def test_unknown_source_and_numbers_without_claims(firm):
    v = verify.verify_answer(firm, f"Pay £18,240 by 30 Nov. {NOTICE}", [])
    assert "NO_CLAIMS" in [p["code"] for p in v["problems"]]
    v = verify.verify_answer(firm, f"x {NOTICE}", [{"id": "c1", "quote": "x", "source": {"type": "email", "id": "00000000-0000-0000-0000-000000000000"}}])
    assert v["problems"][0]["code"] == "SOURCE_NOT_FOUND"


def test_calculation_backs_payment_dates(firm, conn, monkeypatch):
    real_date = dt.date
    class FakeDate(dt.date):
        @classmethod
        def today(cls):
            return real_date(2026, 11, 21)
    monkeypatch.setattr(verify.dt, "date", FakeDate)
    monkeypatch.setattr("builders_api.service.payments.dt.date", FakeDate)
    v = verify.verify_answer(firm, f"Give Fenwick a payment notice by 30 Nov 2026; pay less notice by 11 Dec. {NOTICE}",
                             [{"id": "c1", "source": {"type": "calculation", "id": "KWY-4"}}])
    assert v["pass"], v["problems"]


def test_regulation_quote(firm):
    v = verify.verify_answer(firm, f"The payer must pay the notified sum by the final date. {NOTICE}", [
        {"id": "c1", "quote": "the payer must pay the notified sum (to the extent not already paid) on or before the final date for payment",
         "source": {"type": "regulation", "id": "hgcra-111"}}])
    assert v["pass"], v["problems"]
