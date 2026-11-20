"""Ingest emails: parse, pull text from attachments, file by job, store. Idempotent and re-runnable.

No model here (ADR 0006). Claude reads what this returns and records facts with save_facts.
`emails.gmail_message_id` holds the email's Message-ID for every source, so the same email is never stored twice.
"""

from __future__ import annotations

import datetime as dt
import email
import hashlib
import io
import logging
import re
import uuid
from dataclasses import dataclass, field
from email import policy
from email.utils import getaddresses, parseaddr

from builders_api import quotas
from builders_api.db import connection

log = logging.getLogger(__name__)
MAX_TEXT = 200_000  # characters stored per document


@dataclass
class ParsedAttachment:
    filename: str
    mime_type: str
    data: bytes
    text: str = ""
    page_count: int | None = None

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


@dataclass
class ParsedEmail:
    message_id: str
    from_name: str
    from_address: str
    to: list[str]
    subject: str
    sent_at: dt.datetime
    body: str
    attachments: list[ParsedAttachment] = field(default_factory=list)


def pdf_text(data: bytes) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n\n".join(f"[page {i}]\n{t.strip()}" for i, t in enumerate(pages, 1)), len(pages)


def parse(raw: bytes) -> ParsedEmail:
    msg = email.message_from_bytes(raw, policy=policy.default)
    message_id = (msg.get("Message-ID") or "").strip().strip("<>")
    if not message_id:
        message_id = "noid-" + hashlib.sha256(raw).hexdigest()[:32]
    name, addr = parseaddr(msg.get("From", ""))
    try:
        sent = msg["Date"].datetime if msg["Date"] else None
    except (TypeError, ValueError):
        sent = None
    sent = sent or dt.datetime.now(dt.timezone.utc)
    if sent.tzinfo is None:
        sent = sent.replace(tzinfo=dt.timezone.utc)
    body_part = msg.get_body(preferencelist=("plain", "html"))
    body = body_part.get_content() if body_part else ""
    if body_part is not None and body_part.get_content_type() == "text/html":
        body = re.sub(r"<[^>]+>", " ", body)
    atts = []
    for part in msg.iter_attachments():
        data = part.get_payload(decode=True) or b""
        att = ParsedAttachment(part.get_filename() or "attachment", part.get_content_type(), data)
        try:
            if att.mime_type == "application/pdf" or att.filename.lower().endswith(".pdf"):
                att.text, att.page_count = pdf_text(data)
            elif att.mime_type.startswith("text/"):
                att.text = data.decode(part.get_content_charset() or "utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - a broken attachment must not stop the email
            log.warning("could not read text from %s", att.filename)
        att.text = att.text[:MAX_TEXT]
        atts.append(att)
    return ParsedEmail(
        message_id=message_id, from_name=name, from_address=addr.lower(),
        to=[a for _, a in getaddresses(msg.get_all("To", []))], subject=str(msg.get("Subject", "")),
        sent_at=sent, body=body.strip()[:MAX_TEXT], attachments=atts,
    )


def file_to_job(conn, firm: uuid.UUID, mail: ParsedEmail) -> tuple[uuid.UUID | None, str]:
    """Pick the job by its words (ref, match terms, address) in the email and attachments, else by the
    sender's earlier emails. Ambiguous or nothing found: leave unfiled and say why."""
    haystack = " ".join([mail.subject, mail.body] + [a.filename + " " + a.text for a in mail.attachments]).lower()
    jobs = conn.execute("select id, ref, address, match_terms from jobs where firm_id = %s", (firm,)).fetchall()
    hits = {}
    for j in jobs:
        terms = [j["ref"].lower(), j["address"].split(",")[0].lower()] + [t.lower() for t in j["match_terms"]]
        found = [t for t in terms if t and t in haystack]
        if found:
            hits[j["id"]] = (j["ref"], found)
    if len(hits) == 1:
        (jid, (ref, found)), = hits.items()
        return jid, f"matched {ref} by: {', '.join(found[:3])}"
    if len(hits) > 1:
        return None, "matches several jobs: " + ", ".join(sorted(r for r, _ in hits.values()))
    rows = conn.execute(
        """select job_id, count(*) n from emails where firm_id = %s and from_address = %s and job_id is not null
           group by job_id order by n desc""", (firm, mail.from_address)).fetchall()
    if len(rows) == 1:
        ref = conn.execute("select ref from jobs where id = %s", (rows[0]["job_id"],)).fetchone()["ref"]
        return rows[0]["job_id"], f"sender's earlier emails are all on {ref}"
    return None, "no job words found; sender not linked to one job"


def store(firm: uuid.UUID, mail: ParsedEmail) -> tuple[str, uuid.UUID | None]:
    """Insert one email and its attachments. Returns ('new' | 'existing', email id)."""
    with connection() as conn:
        existing = conn.execute(
            "select id from emails where firm_id = %s and gmail_message_id = %s", (firm, mail.message_id)
        ).fetchone()
        if existing:
            return "existing", existing["id"]
        quotas.consume(firm, "documents_ingested", 1 + len(mail.attachments))
        job_id, reason = file_to_job(conn, firm, mail)
        eid = conn.execute(
            """insert into emails (firm_id, gmail_message_id, from_name, from_address, to_addresses, subject, sent_at,
                                   body_text, job_id, filing_reason, ingest_status, ingest_attempts, ingested_at)
               values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'done',1,now()) returning id""",
            (firm, mail.message_id, mail.from_name, mail.from_address, mail.to, mail.subject, mail.sent_at,
             mail.body, job_id, reason),
        ).fetchone()["id"]
        for a in mail.attachments:
            conn.execute(
                """insert into attachments (firm_id, email_id, filename, mime_type, size_bytes, sha256, page_count,
                                            text_content, job_id)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (email_id, sha256) do nothing""",
                (firm, eid, a.filename, a.mime_type, len(a.data), a.sha256, a.page_count, a.text, job_id),
            )
        return "new", eid
