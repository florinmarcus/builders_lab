"""Per-client rate limit for the public endpoint (token bucket, in memory)."""

from __future__ import annotations

import json
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


class RateLimitMiddleware:
    """ASGI middleware. Client key: first X-Forwarded-For address (tunnel), else the peer address."""

    def __init__(self, app, per_minute: int) -> None:
        self.app = app
        self.bucket = TokenBucket(per_minute)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers") or [])
        fwd = headers.get(b"x-forwarded-for", b"").decode().split(",")[0].strip()
        key = fwd or (scope.get("client") or ("unknown",))[0]
        if self.bucket.allow(key):
            return await self.app(scope, receive, send)
        body = json.dumps(
            {"error": {"code": "rate_limited", "message": "Too many requests. Wait a minute and try again.", "retryable": True}}
        ).encode()
        await send({"type": "http.response.start", "status": 429,
                    "headers": [(b"content-type", b"application/json"), (b"retry-after", b"60")]})
        await send({"type": "http.response.body", "body": body})
