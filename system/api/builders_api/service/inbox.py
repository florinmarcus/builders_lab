"""Inbox sync. Ingestion (Gmail -> Postgres) is step 4 and not built yet."""

from __future__ import annotations

import uuid
from typing import Any

from builders_api.errors import NotConfiguredError


def sync_inbox(firm: uuid.UUID) -> dict[str, Any]:
    raise NotConfiguredError(
        "Inbox sync is not connected yet. The emails already filed are available through the other tools."
    )
