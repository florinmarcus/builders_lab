"""Exponential backoff with full jitter, only for retryable errors."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def is_retryable(exc: BaseException) -> bool:
    """Throttling, timeouts and 5xx are retryable. Anything else is not."""
    if getattr(exc, "retryable", False):
        return True
    return isinstance(exc, (TimeoutError, ConnectionError))


def with_retries(
    fn: Callable[[], T],
    *,
    attempts: int = 4,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    sleep: Callable[[float], None] = time.sleep,
    retryable: Callable[[BaseException], bool] = is_retryable,
) -> T:
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - re-raised below when not retryable
            if attempt == attempts or not retryable(exc):
                raise
            sleep(random.uniform(0, min(max_delay, base_delay * 2 ** (attempt - 1))))
    raise AssertionError("unreachable")
