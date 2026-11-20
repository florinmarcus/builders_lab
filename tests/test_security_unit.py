"""Guard (IP blocking, lockdown) and key expiry states, no database."""

import datetime as dt

from builders_api.security import Guard, access_state, new_key

TODAY = dt.date(2026, 11, 21)


def test_access_states():
    assert access_state(TODAY + dt.timedelta(days=30), 7, TODAY) == "ok"
    assert access_state(TODAY + dt.timedelta(days=14), 7, TODAY) == "expiring"
    assert access_state(TODAY, 7, TODAY) == "expiring"
    assert access_state(TODAY - dt.timedelta(days=7), 7, TODAY) == "grace"
    assert access_state(TODAY - dt.timedelta(days=8), 7, TODAY) == "ended"


def test_ip_block_expires():
    now = [0.0]
    g = Guard(fail_limit=2, block_seconds=60, clock=lambda: now[0])
    g.record_failure("1.2.3.4")
    assert not g.is_blocked("1.2.3.4")
    g.record_failure("1.2.3.4")
    assert g.is_blocked("1.2.3.4") and not g.is_blocked("5.6.7.8")
    now[0] = 61
    assert not g.is_blocked("1.2.3.4")


def test_lockdown_on_traffic_spike_and_on_failures():
    now = [0.0]
    g = Guard(lockdown_requests_per_min=5, lockdown_failures_per_min=3, lockdown_seconds=900, clock=lambda: now[0])
    for _ in range(6):
        g.record_request()
    assert g.locked_down()
    now[0] = 901
    assert not g.locked_down()
    for ip in ("a", "b", "c", "d"):
        g.record_failure(ip)
    assert g.locked_down()


def test_scanner_404s_do_not_trigger_lockdown():
    g = Guard(lockdown_failures_per_min=2)
    for i in range(10):
        g.record_failure(f"10.0.0.{i}", count_for_lockdown=False)
    assert not g.locked_down()


def test_keys_are_random_and_prefixed():
    (k1, p1), (k2, p2) = new_key(), new_key()
    assert k1 != k2 and k1.startswith(f"bl_{p1}_") and len(k1) > 40


def test_key_header_forms():
    from builders_api.mcp_server.gateway import _key_from_headers
    k = "bl_abcd1234_secret"
    assert _key_from_headers({b"authorization": f"Bearer {k}".encode()}) == k
    assert _key_from_headers({b"authorization": f"bearer  {k} ".encode()}) == k
    assert _key_from_headers({b"authorization": k.encode()}) == k
    assert _key_from_headers({b"x-api-key": k.encode()}) == k
    assert _key_from_headers({b"authorization": b"Bearer "}) is None
