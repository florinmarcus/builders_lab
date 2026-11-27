"""The landing card: today's jobs, finish dates and recent emails. Plain code, no model (ADR 0006)."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from builders_api.errors import ValidationError
from builders_api.service import jobs

LANGUAGES = ("en", "ro")


def show_today(firm: uuid.UUID, language: str = "en", now: dt.datetime | None = None) -> dict[str, Any]:
    """Jobs with days to their target date and the emails of the last 7 days, newest first.
    `language` sets the card's labels and button questions (en or ro); the data stays as stored."""
    if language not in LANGUAGES:
        raise ValidationError("language must be en or ro.")
    now = now or dt.datetime.now(dt.timezone.utc)
    today = now.date()
    listed = jobs.list_jobs(firm, since_days=7, now=now)
    out = []
    for j in listed["jobs"]:
        target = dt.date.fromisoformat(j["target_date"]) if j["target_date"] else None
        days_left = (target - today).days if target else None
        out.append({
            "ref": j["ref"], "title": j["title"], "client": j["client"], "status": j["status"],
            "target_date": j["target_date"], "days_left": days_left,
            "due": days_left is not None and days_left <= 0 and j["status"] == "active",
            "recent_emails": j["recent_emails"][:3],
            "email_count_7_days": len(j["recent_emails"]),
        })
    out.sort(key=lambda j: (j["days_left"] is None, j["days_left"] if j["days_left"] is not None else 0))
    return {
        "today": today.isoformat(),
        "language": language,
        "jobs": out,
        "emails_7_days": sum(j["email_count_7_days"] for j in out) + len(listed["recent_emails_not_linked_to_a_job"]),
        "recent_emails_not_linked_to_a_job": listed["recent_emails_not_linked_to_a_job"][:3],
    }
