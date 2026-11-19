"""Typed errors. Tools turn these into clear structured errors, never stack traces."""

from __future__ import annotations


class AppError(Exception):
    code = "app_error"
    retryable = False

    def __init__(self, message: str, **details: object) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        out = {"code": self.code, "message": self.message, "retryable": self.retryable}
        if self.details:
            out["details"] = self.details
        return out


class ValidationError(AppError):
    code = "invalid_input"


class NotFoundError(AppError):
    code = "not_found"


class AuthError(AppError):
    code = "not_authorised"


class NotConfiguredError(AppError):
    code = "not_configured"


class QuotaExceededError(AppError):
    code = "quota_exceeded"


class RateLimitedError(AppError):
    code = "rate_limited"
    retryable = True


class UpstreamError(AppError):
    """A service we call failed. Retryable only for throttling, timeouts and 5xx."""

    code = "upstream_error"

    def __init__(self, message: str, *, retryable: bool = False, **details: object) -> None:
        super().__init__(message, **details)
        self.retryable = retryable
