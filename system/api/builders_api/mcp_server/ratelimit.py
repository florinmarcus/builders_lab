"""Token bucket rate limiter (in memory, one server; parking lot S7)."""

from __future__ import annotations

import threading
import time


class TokenBucket:
    def __init__(self, per_minute: int, clock=time.monotonic) -> None:
        self.rate = per_minute / 60.0
        self.capacity = float(per_minute)
        self.clock = clock
        self._state: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self.clock()
        with self._lock:
            tokens, last = self._state.get(key, (self.capacity, now))
            tokens = min(self.capacity, tokens + (now - last) * self.rate)
            if tokens < 1:
                self._state[key] = (tokens, now)
                return False
            self._state[key] = (tokens - 1, now)
            if len(self._state) > 10_000:  # keep memory bounded
                self._state.clear()
            return True
