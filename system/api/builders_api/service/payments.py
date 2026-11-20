"""Payment dates from stored contract terms. Our code does the date sums, not the model."""

from __future__ import annotations

import calendar
import datetime as dt
import uuid
from typing import Any

from builders_api.db import connection
from builders_api.service.jobs import resolve_job


def _on_day(year: int, month: int, day: int) -> dt.date:
    """That day of the month, or the last day if the month is shorter."""
    return dt.date(year, month, min(day, calendar.monthrange(year, month)[1]))


def _add_months(year: int, month: int, n: int) -> tuple[int, int]:
    m = month - 1 + n
    return year + m // 12, m % 12 + 1


def cycle_dates(terms: dict, due: dt.date, valuation: dt.date | None) -> dict[str, dt.date | None]:
    final = due + dt.timedelta(days=terms["final_date_days_after_due"])
    return {
        "valuation_date": valuation,
        "due_date": due,
        "payment_notice_by": due + dt.timedelta(days=terms["payment_notice_days_after_due"]),
        "pay_less_notice_by": final - dt.timedelta(days=terms["pay_less_days_before_final"]),
        "final_date_for_payment": final,
    }


def current_cycle(terms: dict, today: dt.date) -> dict[str, dt.date | None]:
    """The earliest monthly cycle whose final date for payment is today or later."""
    for n in range(-3, 4):
        y, m = _add_months(today.year, today.month, n)
        if terms["valuation_day_of_month"]:
            valuation = _on_day(y, m, terms["valuation_day_of_month"])
            due = valuation + dt.timedelta(days=terms["due_days_after_valuation"] or 0)
        else:
            valuation, due = None, _on_day(y, m, terms["due_day_of_month"])
        dates = cycle_dates(terms, due, valuation)
        if dates["final_date_for_payment"] >= today:
            return dates
    raise AssertionError("no cycle found")  # cannot happen with monthly cycles


def _roles(party: str) -> dict[str, str]:
    if party == "subcontract":
        return {
            "we_are": "payer",
            "payment_notice": "We (Marcus Limited) must give it to the subcontractor.",
            "pay_less_notice": "Only if we intend to pay less than the notified sum; we give it.",
        }
    return {
        "we_are": "payee",
        "payment_notice": "The employer (or its named person) gives it to us.",
        "pay_less_notice": "The employer gives it if it intends to pay less.",
    }


def get_payment_dates(firm: uuid.UUID, job: str, today: dt.date | None = None) -> dict[str, Any]:
    j = resolve_job(firm, job)
    today = today or dt.date.today()
    with connection() as conn:
        rows = conn.execute(
            """select t.*, a.filename, a.document_type, a.document_date, a.id as attachment_id, e.sent_at
               from contract_terms t
               left join attachments a on a.id = t.source_attachment_id
               left join emails e on e.id = a.email_id
               where t.job_id = %s order by t.party, t.counterparty""",
            (j["id"],),
        ).fetchall()
    contracts, upcoming = [], []
    for t in rows:
        dates = current_cycle(t, today)
        iso = {k: (v.isoformat() if v else None) for k, v in dates.items()}
        for key in ("payment_notice_by", "pay_less_notice_by", "final_date_for_payment"):
            if dates[key] >= today:
                upcoming.append((dates[key], key, t["counterparty"], t["party"]))
        source = None
        if t["attachment_id"]:
            source = {
                "type": "document",
                "id": str(t["attachment_id"]),
                "filename": t["filename"],
                "label": f"{t['filename']} ({t['document_type']}, {t['document_date'] or t['sent_at'].date()})",
            }
        contracts.append(
            {
                "party": t["party"],
                "counterparty": t["counterparty"],
                "contract_form": t["contract_form"],
                "terms": {
                    k: t[k]
                    for k in (
                        "valuation_day_of_month", "due_days_after_valuation", "due_day_of_month",
                        "final_date_days_after_due", "payment_notice_days_after_due", "pay_less_days_before_final",
                    )
                    if t[k] is not None
                },
                "current_cycle": iso,
                "who_gives_notices": _roles(t["party"]),
                "source": source,
            }
        )
    upcoming.sort()
    nxt = upcoming[0] if upcoming else None
    return {
        "job": {"ref": j["ref"], "title": j["title"]},
        "today": today.isoformat(),
        "next_deadline": (
            {"date": nxt[0].isoformat(), "what": nxt[1], "contract": nxt[2], "party": nxt[3]} if nxt else None
        ),
        "contracts": contracts,
        "note": "Dates calculated by our code from the contract terms stored for this job. "
        "For what the law says if a notice is missed, use search_regulations.",
    }
