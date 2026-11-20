"""save_facts: Claude records what it read in one email. The server checks every item before saving (ADR 0006).

Checks: the email belongs to the firm; the job exists; attachments belong to the email; types are known;
dates are real dates; every quote appears word for word (ignoring spacing and case) in its source text.
Calling again for the same email replaces what Claude saved before (seed facts are kept).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from typing import Any

from builders_api.db import connection
from builders_api.errors import NotFoundError, ValidationError
from builders_api.service.jobs import resolve_job

DOCUMENT_TYPES = {
    "quote", "acceptance", "variation", "invoice", "application_for_payment", "payment_notice", "pay_less_notice",
    "contract_particulars", "rams", "insurance_certificate", "electrical_certificate", "building_control_approval",
    "building_control_completion", "completion_photos", "works_order", "asbestos_survey", "gas_capping_note",
    "gas_safety_record", "electrical_test", "drawing_schedule", "chat_export", "order_confirmation", "other",
}
FACT_TYPES = {
    "approval", "discussion", "variation", "quote_accepted", "key_date", "amount", "asbestos_item", "survey_scope",
    "certificate_pending", "instruction", "request", "other",
}
MAX_FACTS = 30


def _norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def _date(value: Any, field: str) -> dt.date | None:
    if value in (None, ""):
        return None
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        raise ValidationError(f"{field} must look like 2026-11-21, got {value!r}.") from None


def save_facts(firm: uuid.UUID, email_id: str, job: str | None, attachments: list[dict] | None,
               facts: list[dict] | None, version_id: str) -> dict[str, Any]:
    attachments, facts = attachments or [], facts or []
    if len(facts) > MAX_FACTS:
        raise ValidationError(f"At most {MAX_FACTS} facts per email.")
    try:
        eid = uuid.UUID(str(email_id))
    except ValueError:
        raise ValidationError("email_id must be the id from sync_inbox.") from None
    job_row = resolve_job(firm, job) if job else None

    with connection() as conn:
        mail = conn.execute("select id, body_text, subject, job_id from emails where id = %s and firm_id = %s",
                            (eid, firm)).fetchone()
        if not mail:
            raise NotFoundError("No such email for this firm.")
        atts = {str(a["id"]): a for a in conn.execute(
            "select id, filename, text_content from attachments where email_id = %s", (eid,)).fetchall()}

        rejected: list[dict[str, Any]] = []
        att_updates = []
        for i, a in enumerate(attachments):
            aid = str(a.get("attachment_id", ""))
            if aid not in atts:
                rejected.append({"attachment": i, "reason": "attachment_id is not on this email"})
                continue
            dtype = a.get("document_type")
            if dtype not in DOCUMENT_TYPES:
                rejected.append({"attachment": i, "reason": f"unknown document_type {dtype!r}"})
                continue
            try:
                att_updates.append((dtype, _date(a.get("document_date"), "document_date"),
                                    _date(a.get("expires_on"), "expires_on"), aid))
            except ValidationError as exc:
                rejected.append({"attachment": i, "reason": exc.message})

        to_save = []
        for i, f in enumerate(facts):
            ftype, summary, quote = f.get("fact_type"), (f.get("summary") or "").strip(), (f.get("quote") or "").strip()
            aid = str(f["attachment_id"]) if f.get("attachment_id") else None
            if ftype not in FACT_TYPES:
                rejected.append({"fact": i, "reason": f"unknown fact_type {ftype!r}"})
                continue
            if not summary or not quote:
                rejected.append({"fact": i, "reason": "summary and quote are both required"})
                continue
            if aid and aid not in atts:
                rejected.append({"fact": i, "reason": "attachment_id is not on this email"})
                continue
            source_text = atts[aid]["text_content"] if aid else (mail["subject"] + "\n" + mail["body_text"])
            if _norm(quote) not in _norm(source_text):
                rejected.append({"fact": i, "reason": "quote not found word for word in the source; copy it exactly"})
                continue
            try:
                fdate = _date(f.get("date"), "date")
            except ValidationError as exc:
                rejected.append({"fact": i, "reason": exc.message})
                continue
            value = f.get("detail") or {}
            if not isinstance(value, dict):
                rejected.append({"fact": i, "reason": "detail must be an object"})
                continue
            page = f.get("page") if isinstance(f.get("page"), int) else None
            to_save.append((ftype, summary, quote, json.dumps(value), fdate, page, aid))

        job_id = job_row["id"] if job_row else mail["job_id"]
        if job_row:
            conn.execute("update emails set job_id = %s, filing_reason = %s where id = %s",
                         (job_id, f"filed by Claude to {job_row['ref']}", eid))
            conn.execute("update attachments set job_id = %s where email_id = %s", (job_id, eid))
        for dtype, ddate, exp, aid in att_updates:
            conn.execute("update attachments set document_type = %s, document_date = %s, expires_on = %s where id = %s",
                         (dtype, ddate, exp, aid))
        conn.execute("delete from facts where email_id = %s and prompt_version <> 'seed'", (eid,))
        for ftype, summary, quote, value, fdate, page, aid in to_save:
            conn.execute(
                """insert into facts (firm_id, job_id, email_id, attachment_id, fact_type, summary, quote, value,
                                      fact_date, source_page, prompt_version)
                   values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s)""",
                (firm, job_id, eid, aid, ftype, summary, quote, value, fdate, page, version_id),
            )
        conn.execute("update emails set facts_done_at = now(), facts_version = %s where id = %s", (version_id, eid))

    return {
        "email_id": str(eid),
        "job": job_row["ref"] if job_row else None,
        "saved": {"facts": len(to_save), "attachments": len(att_updates)},
        "rejected": rejected,
        "note": "Fix rejected items and call save_facts again for this email (it replaces earlier saves)."
        if rejected else "All saved.",
    }
