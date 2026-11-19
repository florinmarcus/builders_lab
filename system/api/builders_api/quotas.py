"""Daily quotas per firm: documents ingested, tool calls, Bedrock spend (USD)."""

from __future__ import annotations

import uuid

from builders_api.db import connection
from builders_api.errors import QuotaExceededError

DEFAULT_LIMITS = {"documents_ingested": 200, "tool_calls": 500, "bedrock_usd": 2.0}


def consume(firm_id: uuid.UUID, metric: str, amount: float = 1) -> float:
    """Add `amount` to today's usage, or raise if it would pass the limit. Returns new usage.

    Atomic: the check and the increment happen in one statement.
    """
    with connection() as conn:
        row = conn.execute("select daily_limit from quota_limits where firm_id=%s and metric=%s", (firm_id, metric)).fetchone()
        limit = float(row["daily_limit"]) if row else DEFAULT_LIMITS[metric]
        row = conn.execute(
            """insert into quota_usage (firm_id, metric, day, used)
               select %(f)s, %(m)s, current_date, %(a)s where %(a)s <= %(l)s
               on conflict (firm_id, metric, day) do update set used = quota_usage.used + %(a)s
                   where quota_usage.used + %(a)s <= %(l)s
               returning used""",
            {"f": firm_id, "m": metric, "a": amount, "l": limit},
        ).fetchone()
    if row is None:
        raise QuotaExceededError(
            f"Daily limit reached for {metric.replace('_', ' ')} ({limit:g}). It resets at midnight UTC.",
            metric=metric,
            limit=limit,
        )
    return float(row["used"])
