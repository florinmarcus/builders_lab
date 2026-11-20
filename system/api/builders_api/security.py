"""API keys, IP blocking, lockdown and the kill switch (ADR 0007).

Keys look like `bl_<prefix>_<secret>`. We store the prefix and an HMAC of the whole key, never the key.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import logging
import os
import secrets
import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass

from builders_api.db import connection

log = logging.getLogger(__name__)

WARN_DAYS = 14


def _pepper() -> bytes:
    pepper = os.environ.get("API_KEY_PEPPER", "")
    if not pepper:
        log.warning("API_KEY_PEPPER not set: key hashes use no server secret")
    return pepper.encode()


def hash_key(key: str) -> str:
    return hmac.new(_pepper(), key.encode(), hashlib.sha256).hexdigest()


def new_key() -> tuple[str, str]:
    """Return (full key, prefix)."""
    prefix = secrets.token_hex(4)
    return f"bl_{prefix}_{secrets.token_urlsafe(32)}", prefix


# ------------------------------------------------------------------ who is calling


@dataclass(frozen=True)
class Caller:
    firm_id: uuid.UUID
    key_id: uuid.UUID
    key_prefix: str
    access: str  # 'ok', 'expiring', 'grace', 'ended'
    expires_on: dt.date


current_caller: ContextVar[Caller | None] = ContextVar("current_caller", default=None)


def access_state(expires_on: dt.date, grace_days: int, today: dt.date) -> str:
    if today <= expires_on:
        return "expiring" if (expires_on - today).days <= WARN_DAYS else "ok"
    if today <= expires_on + dt.timedelta(days=grace_days):
        return "grace"
    return "ended"


def key_failure_reason(key: str | None) -> str:
    """Why a key was refused, for the log. Never includes the key itself."""
    if not key:
        return "no key header"
    parts = key.split("_")
    if len(parts) < 3 or parts[0] != "bl":
        return f"bad format (length {len(key)}, starts {key[:3]!r})"
    with connection() as conn:
        row = conn.execute("select revoked_at from api_keys where key_prefix = %s", (parts[1],)).fetchone()
    if not row:
        return f"unknown prefix {parts[1]}"
    if row["revoked_at"] is not None:
        return f"revoked prefix {parts[1]}"
    return f"wrong secret for prefix {parts[1]}"


def check_key(key: str, today: dt.date | None = None) -> Caller | None:
    """Return the caller for a valid, unrevoked key, else None. Expired keys still return a Caller
    (with access 'grace' or 'ended') so tools can show a plain message instead of a technical error."""
    parts = key.split("_")
    if len(parts) < 3 or parts[0] != "bl":
        return None
    prefix = parts[1]
    with connection() as conn:
        row = conn.execute(
            "select id, firm_id, key_hash, expires_on, grace_days, revoked_at from api_keys where key_prefix = %s",
            (prefix,),
        ).fetchone()
        if not row or row["revoked_at"] is not None:
            return None
        if not hmac.compare_digest(row["key_hash"], hash_key(key)):
            return None
        conn.execute("update api_keys set last_used_at = now() where id = %s", (row["id"],))
    state = access_state(row["expires_on"], row["grace_days"], today or dt.date.today())
    return Caller(row["firm_id"], row["id"], prefix, state, row["expires_on"])


# ------------------------------------------------------------------ guards (in memory, one server)


class Guard:
    """Failed-auth IP blocking and automatic lockdown. In memory (parking lot S17)."""

    def __init__(
        self,
        *,
        fail_limit: int = 10,
        block_seconds: int = 3600,
        lockdown_requests_per_min: int = 600,
        lockdown_failures_per_min: int = 50,
        lockdown_seconds: int = 900,
        clock=time.monotonic,
    ) -> None:
        self.fail_limit = fail_limit
        self.block_seconds = block_seconds
        self.lockdown_requests_per_min = lockdown_requests_per_min
        self.lockdown_failures_per_min = lockdown_failures_per_min
        self.lockdown_seconds = lockdown_seconds
        self.clock = clock
        self._fails: dict[str, list[float]] = {}
        self._blocked: dict[str, float] = {}
        self._requests: list[float] = []
        self._failures: list[float] = []
        self._lockdown_until = 0.0
        self._lock = threading.Lock()

    @staticmethod
    def _recent(times: list[float], now: float, window: float) -> list[float]:
        return [t for t in times if now - t < window]

    def locked_down(self) -> bool:
        return self.clock() < self._lockdown_until

    def _start_lockdown(self, reason: str) -> None:
        self._lockdown_until = self.clock() + self.lockdown_seconds
        log.critical("LOCKDOWN for %s seconds: %s", self.lockdown_seconds, reason)
        alert(f"MCP server lockdown: {reason}")

    def is_blocked(self, ip: str) -> bool:
        with self._lock:
            until = self._blocked.get(ip)
            if until and self.clock() < until:
                return True
            self._blocked.pop(ip, None)
            return False

    def record_request(self) -> None:
        now = self.clock()
        with self._lock:
            self._requests = self._recent(self._requests, now, 60) + [now]
            if len(self._requests) > self.lockdown_requests_per_min and not self.locked_down():
                self._start_lockdown(f"{len(self._requests)} requests in a minute")

    def record_failure(self, ip: str, *, count_for_lockdown: bool = True) -> None:
        now = self.clock()
        with self._lock:
            fails = self._recent(self._fails.get(ip, []), now, self.block_seconds) + [now]
            self._fails[ip] = fails
            if len(fails) >= self.fail_limit:
                self._blocked[ip] = now + self.block_seconds
                self._fails.pop(ip, None)
                log.warning("blocked %s for %s seconds after %s failed key checks", ip, self.block_seconds, len(fails))
            if not count_for_lockdown:
                return
            self._failures = self._recent(self._failures, now, 60) + [now]
            if len(self._failures) > self.lockdown_failures_per_min and not self.locked_down():
                self._start_lockdown(f"{len(self._failures)} failed key checks in a minute")
            if len(self._fails) > 50_000:  # keep memory bounded
                self._fails.clear()


def alert(message: str) -> None:
    """Tell Florin. Email or SMS comes with deployment (parking lot N7); for now, the log."""
    log.critical("ALERT: %s", message)


# ------------------------------------------------------------------ kill switch (database flag)

_kill_cache: tuple[float, bool] = (0.0, False)


def kill_switch_on(cache_seconds: float = 5.0) -> bool:
    global _kill_cache
    now = time.monotonic()
    if now - _kill_cache[0] < cache_seconds:
        return _kill_cache[1]
    try:
        with connection() as conn:
            row = conn.execute("select value from server_flags where name = 'kill_switch'").fetchone()
        on = bool(row and row["value"] == "on")
    except Exception:  # noqa: BLE001 - if the database is down, fail closed
        log.exception("cannot read kill switch; refusing requests")
        on = True
    _kill_cache = (now, on)
    return on


def set_kill_switch(on: bool) -> None:
    global _kill_cache
    with connection() as conn:
        conn.execute(
            """insert into server_flags (name, value) values ('kill_switch', %s)
               on conflict (name) do update set value = excluded.value, updated_at = now()""",
            ("on" if on else "off",),
        )
    _kill_cache = (0.0, False)
