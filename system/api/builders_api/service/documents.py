"""Full-text search over a firm's emails and attachments (Postgres)."""

from __future__ import annotations

import uuid
from typing import Any

from builders_api.db import connection
from builders_api.errors import ValidationError
from builders_api.service.jobs import attachment_source, email_source, resolve_job

HEADLINE = "MaxFragments=2, MaxWords=30, MinWords=8, StartSel=«, StopSel=»"


def _or_query(conn, text: str) -> str:
    """Words joined with OR, so partial matches still rank (plainto_tsquery joins with AND)."""
    q = conn.execute("select plainto_tsquery('english', %s)::text as q", (text,)).fetchone()["q"]
    return q.replace(" & ", " | ")


def search_job_documents(firm: uuid.UUID, query: str, job: str | None = None, limit: int = 10) -> dict[str, Any]:
    query = (query or "").strip()
    if not query:
        raise ValidationError("Give some words to search for.")
    if not 1 <= limit <= 25:
        raise ValidationError("limit must be between 1 and 25.")
    job_row = resolve_job(firm, job) if job else None
    job_id = job_row["id"] if job_row else None
    with connection() as conn:
        tsq = _or_query(conn, query)
        if not tsq:
            return {"query": query, "results": [], "note": "Only common words given; try more specific words."}
        params = {"f": firm, "q": tsq, "j": job_id, "n": limit}
        rows = conn.execute(
            f"""
            select * from (
              select 'email' as kind, e.id, e.id as email_id, null::uuid as attachment_id,
                     e.from_name, e.from_address, e.subject, e.sent_at, null as filename,
                     null as document_type, null::date as document_date, j.ref as job_ref,
                     ts_rank(e.search, to_tsquery('english', %(q)s)) as rank,
                     ts_headline('english', e.subject || ' — ' || e.body_text, to_tsquery('english', %(q)s), '{HEADLINE}') as snippet
              from emails e left join jobs j on j.id = e.job_id
              where e.firm_id = %(f)s and e.search @@ to_tsquery('english', %(q)s)
                and (%(j)s::uuid is null or e.job_id = %(j)s)
              union all
              select 'document', a.id, e.id, a.id, e.from_name, e.from_address, e.subject, e.sent_at,
                     a.filename, a.document_type, a.document_date, j.ref,
                     ts_rank(a.search, to_tsquery('english', %(q)s)),
                     ts_headline('english', a.text_content, to_tsquery('english', %(q)s), '{HEADLINE}')
              from attachments a join emails e on e.id = a.email_id left join jobs j on j.id = a.job_id
              where a.firm_id = %(f)s and a.search @@ to_tsquery('english', %(q)s)
                and (%(j)s::uuid is null or a.job_id = %(j)s)
            ) hits order by rank desc, sent_at desc limit %(n)s
            """,
            params,
        ).fetchall()
    results = []
    for r in rows:
        source = email_source(r) if r["kind"] == "email" else {
            **attachment_source(r),
            "attached_to": email_source(r)["label"],
        }
        results.append({"job": r["job_ref"], "snippet": r["snippet"], "source": source})
    return {"query": query, "job": job_row["ref"] if job_row else None, "results": results}
