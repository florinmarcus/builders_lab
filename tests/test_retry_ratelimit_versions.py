"""Retries, rate limit and version locking (no database)."""

import pytest

from builders_api import versions
from builders_api.errors import UpstreamError, ValidationError
from builders_api.mcp_server.ratelimit import TokenBucket
from builders_api.retry import with_retries


def test_retries_only_retryable_errors():
    calls, sleeps = [], []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise UpstreamError("throttled", retryable=True)
        return "ok"

    assert with_retries(flaky, sleep=sleeps.append) == "ok"
    assert len(calls) == 3 and len(sleeps) == 2 and all(s >= 0 for s in sleeps)


def test_no_retry_for_validation_error():
    calls = []

    def bad():
        calls.append(1)
        raise ValidationError("bad input")

    with pytest.raises(ValidationError):
        with_retries(bad, sleep=lambda s: None)
    assert len(calls) == 1


def test_gives_up_after_attempts():
    with pytest.raises(UpstreamError):
        with_retries(lambda: (_ for _ in ()).throw(UpstreamError("5xx", retryable=True)), attempts=3, sleep=lambda s: None)


def test_token_bucket():
    now = [0.0]
    bucket = TokenBucket(per_minute=2, clock=lambda: now[0])
    assert bucket.allow("a") and bucket.allow("a") and not bucket.allow("a")
    assert bucket.allow("b")
    now[0] = 30.0
    assert bucket.allow("a")


def test_versions_are_locked_and_unchanged():
    assert versions.check_lock() == []


def test_every_tool_has_a_description():
    names = {"list_jobs", "get_job", "list_missing_items", "search_job_documents",
             "search_regulations", "get_payment_dates", "sync_inbox"}
    assert names <= {n for (k, n) in versions.active() if k == "tool_description"}
