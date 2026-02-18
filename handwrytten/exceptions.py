"""Exception classes for the Handwrytten SDK."""

from __future__ import annotations

from typing import Any, Optional


class HandwryttenError(Exception):
    """Base exception for all Handwrytten API errors."""

    def __init__(
        self,
        message: str = "An error occurred with the Handwrytten API",
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)


class AuthenticationError(HandwryttenError):
    """Raised when API authentication fails (401/403)."""

    def __init__(self, message: str = "Invalid or missing API key", **kwargs):
        super().__init__(message=message, **kwargs)


class BadRequestError(HandwryttenError):
    """Raised when the request is malformed or has invalid parameters (400)."""

    def __init__(self, message: str = "Bad request", **kwargs):
        super().__init__(message=message, **kwargs)


class NotFoundError(HandwryttenError):
    """Raised when the requested resource is not found (404)."""

    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message=message, **kwargs)


class RateLimitError(HandwryttenError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please retry after a delay.",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        self.retry_after = retry_after
        super().__init__(message=message, **kwargs)


class ServerError(HandwryttenError):
    """Raised when the Handwrytten API returns a server error (5xx)."""

    def __init__(self, message: str = "Handwrytten server error", **kwargs):
        super().__init__(message=message, **kwargs)
