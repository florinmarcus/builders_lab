"""sync_inbox: fetch new emails, store and file them, and hand Claude the emails that still need facts."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from builders_api.db import connection
from builders_api.errors import AppError
from builders_api.service import ingest, mail_sources
from builders_api.service.jobs import attachment_source, email_source

log = logging.getLogger(__name__)
TEXT_FOR_CLAUDE = 6000  # characters per email body or document handed back for extraction
MAX_PENDING = 10        # emails per call; call again for more


def sync_inbox(firm: uuid.UUID) -> dict[str, Any]:
    source = mail_sources.from_env()
    counts = {"new": 0, "already_had": 0, "failed": 0}
    failures = []
    for item in source.fetch():
        try:
            state, _ = ingest.store(firm, ingest.parse(item.raw))
            counts["new" if state == "new" else "already_had"] += 1
        except AppError:
            raise  # quota or configuration: stop and tell the user
        except Exception as exc:  # noqa: BLE001 - one bad email must not stop the rest; re-run retries it
            log.exception("could not ingest %s", item.source_id)
            counts["failed"] += 1
            failures.append({"source": item.source_id, "error": type(exc).__name__})
    pending, more = needs_facts(firm)
    return {
        "counts": counts,
        "failures": failures,
        "emails_needing_facts": pending,
        "more_waiting": more,
        "next_step": (
            "For each email in emails_needing_facts, read it and call save_facts once: the job (ref) if you can "
            "tell, each attachment's document type and dates, and the facts with exact quotes. "
            "Then call sync_inbox again if more_waiting is true."
            if pending else "Nothing left to extract."
        ),
    }


def needs_facts(firm: uuid.UUID) -> tuple[list[dict[str, Any]], bool]:
    """Emails with no facts saved and no extraction recorded yet, oldest first."""
    with connection() as conn:
        rows = conn.execute(
            """select e.id, e.from_name, e.from_address, e.subject, e.sent_at, e.body_text, e.filing_reason,
                      j.ref as job_ref
               from emails e left join jobs j on j.id = e.job_id
               where e.firm_id = %s and e.facts_done_at is null
                 and not exists (select 1 from facts f where f.email_id = e.id)
               order by e.sent_at limit %s""",
            (firm, MAX_PENDING + 1),
        ).fetchall()
        out = []
        for r in rows[:MAX_PENDING]:
            atts = conn.execute(
                """select id, filename, document_type, document_date, text_content from attachments
                   where email_id = %s order by filename""", (r["id"],)).fetchall()
            out.append({
                "email_id": str(r["id"]),
                "source": email_source(r),
                "filed_to": r["job_ref"],
                "filing_reason": r["filing_reason"],
                "body": r["body_text"][:TEXT_FOR_CLAUDE],
                "attachments": [{
                    "attachment_id": str(a["id"]),
                    "source": {**attachment_source({**a, "sent_at": r["sent_at"]})},
                    "text": a["text_content"][:TEXT_FOR_CLAUDE],
                } for a in atts],
            })
    return out, len(rows) > MAX_PENDING
