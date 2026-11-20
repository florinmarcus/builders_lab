"""Jobs, their emails, documents, facts and required items."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from builders_api.db import connection
from builders_api.errors import NotFoundError, ValidationError

EXPIRING_SOON_DAYS = 14


def _d(value: dt.date | dt.datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        value = value.date()
    return value.isoformat()


def email_source(row: dict) -> dict[str, Any]:
    when = _d(row["sent_at"])
    who = row.get("from_name") or row.get("from_address") or "unknown sender"
    return {
        "type": "email",
        "id": str(row["email_id"] if "email_id" in row else row["id"]),
        "from": who,
        "address": row.get("from_address"),  # so drafts can be addressed (reply goes to the sender)
        "date": when,
        "subject": row.get("subject"),
        "label": f"Email from {who}, {when}: \"{row.get('subject') or ''}\"",
    }


def attachment_source(row: dict) -> dict[str, Any]:
    when = _d(row.get("document_date")) or _d(row.get("sent_at"))
    return {
        "type": "document",
        "id": str(row["attachment_id"] if "attachment_id" in row else row["id"]),
        "filename": row["filename"],
        "document_type": row.get("document_type"),
        "date": when,
        "label": f"{row['filename']} ({row.get('document_type') or 'document'}, {when})",
    }


def firm_id(slug: str) -> uuid.UUID:
    with connection() as conn:
        row = conn.execute("select id from firms where slug = %s", (slug,)).fetchone()
    if not row:
        raise NotFoundError(f"No firm called '{slug}'. Has the mock data been loaded?")
    return row["id"]


def resolve_job(firm: uuid.UUID, job: str) -> dict:
    """Find a job by ref, or by words in its title or address. Must match exactly one."""
    words = (job or "").strip()
    if not words:
        raise ValidationError("Give a job ref (e.g. ELM-22) or words from the job's title or address.")
    with connection() as conn:
        row = conn.execute(
            "select * from jobs where firm_id = %s and lower(ref) = lower(%s)", (firm, words)
        ).fetchone()
        if row:
            return row
        rows = conn.execute(
            """select * from jobs where firm_id = %s and (
                   title ilike '%%' || %s || '%%' or address ilike '%%' || %s || '%%'
                   or exists (select 1 from unnest(match_terms) t where lower(t) = lower(%s)))""",
            (firm, words, words, words),
        ).fetchall()
    if len(rows) == 1:
        return rows[0]
    if not rows:
        raise NotFoundError(f"No job matches '{words}'. Use list_jobs to see the job refs.")
    raise ValidationError(
        f"'{words}' matches more than one job. Use one of these refs.", matches=[r["ref"] for r in rows]
    )


def list_jobs(firm: uuid.UUID, since_days: int = 1, now: dt.datetime | None = None) -> dict[str, Any]:
    if not 0 <= since_days <= 90:
        raise ValidationError("since_days must be between 0 and 90.")
    now = now or dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=since_days)
    with connection() as conn:
        jobs = conn.execute(
            """select j.id, j.ref, j.title, j.address, j.status, j.job_type_code, j.target_date,
                      c.name as client, c.kind as client_kind
               from jobs j left join clients c on c.id = j.client_id
               where j.firm_id = %s order by j.ref""",
            (firm,),
        ).fetchall()
        recent = conn.execute(
            """select id, job_id, from_name, from_address, subject, sent_at, filing_reason
               from emails where firm_id = %s and sent_at >= %s order by sent_at desc""",
            (firm, since),
        ).fetchall()
    by_job: dict[Any, list] = {}
    for e in recent:
        by_job.setdefault(e["job_id"], []).append(email_source(e))
    return {
        "since": since.isoformat(timespec="minutes"),
        "jobs": [
            {
                "ref": j["ref"],
                "title": j["title"],
                "address": j["address"],
                "client": j["client"],
                "client_kind": j["client_kind"],
                "job_type": j["job_type_code"],
                "status": j["status"],
                "target_date": _d(j["target_date"]),
                "recent_emails": by_job.get(j["id"], []),
            }
            for j in jobs
        ],
        "recent_emails_not_linked_to_a_job": by_job.get(None, []),
    }


def get_job(firm: uuid.UUID, job: str) -> dict[str, Any]:
    j = resolve_job(firm, job)
    with connection() as conn:
        client = conn.execute("select name, kind, email, phone from clients where id = %s", (j["client_id"],)).fetchone()
        emails = conn.execute(
            "select id, from_name, from_address, subject, sent_at from emails where job_id = %s order by sent_at",
            (j["id"],),
        ).fetchall()
        docs = conn.execute(
            """select a.id, a.filename, a.document_type, a.document_date, a.expires_on, a.page_count, e.sent_at
               from attachments a join emails e on e.id = a.email_id
               where a.job_id = %s order by coalesce(a.document_date, e.sent_at::date)""",
            (j["id"],),
        ).fetchall()
        facts = conn.execute(
            """select f.fact_type, f.summary, f.quote, f.value, f.fact_date, f.source_page,
                      e.id as email_id, e.from_name, e.from_address, e.subject, e.sent_at,
                      a.id as attachment_id, a.filename, a.document_type, a.document_date
               from facts f
               left join emails e on e.id = f.email_id
               left join attachments a on a.id = f.attachment_id
               where f.job_id = %s order by f.fact_type, f.fact_date nulls last""",
            (j["id"],),
        ).fetchall()
        terms = conn.execute(
            "select party, counterparty, contract_form from contract_terms where job_id = %s order by party, counterparty",
            (j["id"],),
        ).fetchall()
    return {
        "job": {
            "ref": j["ref"],
            "title": j["title"],
            "address": j["address"],
            "job_type": j["job_type_code"],
            "status": j["status"],
            "start_date": _d(j["start_date"]),
            "target_date": _d(j["target_date"]),
        },
        "client": client,
        "emails": [email_source(e) for e in emails],
        "documents": [
            {**attachment_source(d), "expires_on": _d(d["expires_on"]), "pages": d["page_count"]} for d in docs
        ],
        "facts": [_fact(f) for f in facts],
        "contracts": terms,
    }


def _fact(f: dict) -> dict[str, Any]:
    if f["attachment_id"]:
        source = attachment_source(f)
        if f["source_page"]:
            source["page"] = f["source_page"]
            source["label"] += f", page {f['source_page']}"
    else:
        source = email_source(f)
    return {
        "type": f["fact_type"],
        "summary": f["summary"],
        "quote": f["quote"],
        "detail": f["value"],
        "date": _d(f["fact_date"]),
        "source": source,
    }


def list_missing_items(firm: uuid.UUID, job: str, today: dt.date | None = None) -> dict[str, Any]:
    j = resolve_job(firm, job)
    today = today or dt.date.today()
    with connection() as conn:
        items = conn.execute(
            "select code, label, satisfied_by from required_items where job_type_code = %s order by sort_order",
            (j["job_type_code"],),
        ).fetchall()
        docs = conn.execute(
            """select a.id, a.filename, a.document_type, a.document_date, a.expires_on, e.sent_at
               from attachments a join emails e on e.id = a.email_id where a.job_id = %s""",
            (j["id"],),
        ).fetchall()
        facts = conn.execute(
            """select f.fact_type, f.summary, f.fact_date, f.source_page,
                      e.id as email_id, e.from_name, e.from_address, e.subject, e.sent_at,
                      a.id as attachment_id, a.filename, a.document_type, a.document_date
               from facts f left join emails e on e.id = f.email_id left join attachments a on a.id = f.attachment_id
               where f.job_id = %s""",
            (j["id"],),
        ).fetchall()
    out = []
    for item in items:
        wanted = set(item["satisfied_by"])
        evidence = [d for d in docs if d["document_type"] in wanted]
        fact_evidence = [f for f in facts if f["fact_type"] in wanted]
        status, sources = "missing", []
        if evidence:
            for d in evidence:
                src = {**attachment_source(d), "expires_on": _d(d["expires_on"])}
                if d["expires_on"] and d["expires_on"] < today:
                    src["warning"] = "expired"
                elif d["expires_on"] and (d["expires_on"] - today).days <= EXPIRING_SOON_DAYS:
                    src["warning"] = "expiring soon"
                sources.append(src)
            warnings = [s.get("warning") for s in sources]
            if all(w == "expired" for w in warnings):
                status = "expired"
            elif "expired" in warnings:
                status = "some_expired"
            elif "expiring soon" in warnings:
                status = "expiring_soon"
            else:
                status = "present"
        elif fact_evidence:
            status = "present"
            sources = [_fact({**f, "quote": None, "value": {}})["source"] for f in fact_evidence]
        out.append({"item": item["label"], "status": status, "sources": sources})
    return {
        "job": {"ref": j["ref"], "title": j["title"], "job_type": j["job_type_code"]},
        "checked_on": today.isoformat(),
        "items": out,
        "note": "Checklist is the firm's own list, not a legal requirement.",
    }
