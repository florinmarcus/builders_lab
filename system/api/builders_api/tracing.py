"""One trace row per model call and per tool call."""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections.abc import Iterator
from typing import Any

from builders_api.db import connection

log = logging.getLogger(__name__)


@dataclass
class Span:
    trace_id: uuid.UUID
    kind: str  # 'model' or 'tool'
    name: str
    firm_id: uuid.UUID | None = None
    version_id: str | None = None
    model_id: str | None = None
    parent_span_id: uuid.UUID | None = None
    span_id: uuid.UUID = field(default_factory=uuid.uuid4)
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error_type: str | None = None


def write(span: Span, latency_ms: int) -> None:
    """Write the row. A tracing failure is logged, never raised to the caller."""
    try:
        with connection() as conn:
            conn.execute(
                """insert into traces (trace_id, span_id, parent_span_id, firm_id, kind, name, model_id,
                                       version_id, input_tokens, output_tokens, cost_usd, latency_ms,
                                       status, error_type, sources)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    span.trace_id, span.span_id, span.parent_span_id, span.firm_id, span.kind, span.name,
                    span.model_id, span.version_id, span.input_tokens, span.output_tokens, span.cost_usd,
                    latency_ms, span.status, span.error_type, json.dumps(span.sources, default=str),
                ),
            )
    except Exception:  # noqa: BLE001
        log.exception("could not write trace row for %s", span.name)


@contextmanager
def traced(span: Span) -> Iterator[Span]:
    start = time.perf_counter()
    try:
        yield span
    except Exception as exc:
        span.status = "error"
        span.error_type = getattr(exc, "code", type(exc).__name__)
        raise
    finally:
        write(span, int((time.perf_counter() - start) * 1000))
