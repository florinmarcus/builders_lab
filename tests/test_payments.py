"""Payment date sums (no database)."""

import datetime as dt

from builders_api.service.payments import current_cycle

SUB = {"valuation_day_of_month": None, "due_days_after_valuation": None, "due_day_of_month": 25,
       "final_date_days_after_due": 21, "payment_notice_days_after_due": 5, "pay_less_days_before_final": 5}
MAIN = {"valuation_day_of_month": 28, "due_days_after_valuation": 7, "due_day_of_month": None,
        "final_date_days_after_due": 14, "payment_notice_days_after_due": 5, "pay_less_days_before_final": 5}


def test_fenwick_dates_on_demo_day():
    c = current_cycle(SUB, dt.date(2026, 11, 21))
    assert c["due_date"] == dt.date(2026, 11, 25)
    assert c["payment_notice_by"] == dt.date(2026, 11, 30)
    assert c["pay_less_notice_by"] == dt.date(2026, 12, 11)
    assert c["final_date_for_payment"] == dt.date(2026, 12, 16)


def test_cycle_stays_until_final_date_passes():
    assert current_cycle(SUB, dt.date(2026, 12, 16))["due_date"] == dt.date(2026, 11, 25)
    assert current_cycle(SUB, dt.date(2026, 12, 17))["due_date"] == dt.date(2026, 12, 25)


def test_main_contract_from_valuation_date():
    c = current_cycle(MAIN, dt.date(2026, 11, 21))
    assert (c["valuation_date"], c["due_date"], c["final_date_for_payment"]) == (
        dt.date(2026, 11, 28), dt.date(2026, 12, 5), dt.date(2026, 12, 19))


def test_short_month_uses_last_day():
    terms = {**MAIN, "valuation_day_of_month": 31}
    assert current_cycle(terms, dt.date(2027, 2, 10))["valuation_date"] == dt.date(2027, 1, 31)
    assert current_cycle(terms, dt.date(2027, 2, 22))["valuation_date"] == dt.date(2027, 2, 28)
