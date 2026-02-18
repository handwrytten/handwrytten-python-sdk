"""Low-level HTTP transport for the Handwrytten API."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

from handwrytten.exceptions import (
    AuthenticationError,
    BadRequestError,
    HandwryttenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

logger = logging.getLogger("handwrytten")

DEFAULT_BASE_URL = "https://api.handwrytten.com/v2/"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds


class HttpClient:
    """Handles HTTP communication with the Handwrytten API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.api_key,
                "User-Agent": "handwrytten-python/1.0.0",
            }
        )

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        """Make an HTTP request with automatic retries and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API endpoint path (relative to base_url).
            params: Query string parameters.
            json_body: JSON request body.
            idempotency_key: Optional idempotency key for safe retries.

        Returns:
            Parsed JSON response.

        Raises:
            HandwryttenError: On API errors.
        """
        url = urljoin(self.base_url, path.lstrip("/"))
        headers = {}

        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Request %s %s (attempt %d/%d) body=%s",
                    method,
                    url,
                    attempt + 1,
                    self.max_retries,
                    json_body,
                )

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                    headers=headers,
                    timeout=self.timeout,
                )

                return self._handle_response(response)

            except (RateLimitError, ServerError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait = RETRY_BACKOFF * (2**attempt)
                    if isinstance(e, RateLimitError) and e.retry_after:
                        wait = e.retry_after
                    logger.warning(
                        "Retryable error (attempt %d/%d), waiting %.1fs: %s",
                        attempt + 1,
                        self.max_retries,
                        wait,
                        e,
                    )
                    time.sleep(wait)
                else:
                    raise

            except requests.exceptions.ConnectionError as e:
                last_error = HandwryttenError(
                    f"Connection error: {e}", status_code=None
                )
                if attempt < self.max_retries - 1:
                    wait = RETRY_BACKOFF * (2**attempt)
                    logger.warning(
                        "Connection error (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        self.max_retries,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    raise last_error

            except requests.exceptions.Timeout as e:
                last_error = HandwryttenError(
                    f"Request timed out after {self.timeout}s", status_code=None
                )
                if attempt < self.max_retries - 1:
                    wait = RETRY_BACKOFF * (2**attempt)
                    time.sleep(wait)
                else:
                    raise last_error

        raise last_error  # type: ignore[misc]

    def _handle_response(self, response: requests.Response) -> Any:
        """Parse response and raise appropriate exceptions for error codes."""
        # Try to parse JSON body for error details
        body = None
        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError):
            body = response.text or None

        if response.status_code >= 500:
            msg = self._extract_error_message(body, "Server error")
            raise ServerError(
                message=msg,
                status_code=response.status_code,
                response_body=body,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                status_code=429,
                response_body=body,
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code in (401, 403):
            msg = self._extract_error_message(body, "Authentication failed")
            raise AuthenticationError(
                message=msg,
                status_code=response.status_code,
                response_body=body,
            )

        if response.status_code == 404:
            msg = self._extract_error_message(body, "Resource not found")
            raise NotFoundError(
                message=msg,
                status_code=response.status_code,
                response_body=body,
            )

        if response.status_code >= 400:
            msg = self._extract_error_message(body, "Bad request")
            raise BadRequestError(
                message=msg,
                status_code=response.status_code,
                response_body=body,
            )

        return body

    @staticmethod
    def _extract_error_message(body: Any, default: str) -> str:
        """Try to pull a human-readable error message from the response body."""
        if isinstance(body, dict):
            for key in ("message", "error", "errors", "detail", "msg"):
                if key in body:
                    val = body[key]
                    if isinstance(val, str):
                        return val
                    if isinstance(val, list) and val:
                        return str(val[0])
                    return str(val)
        if isinstance(body, str) and body:
            return body[:200]
        return default

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        return self.request(
            "POST", path, json_body=json_body, idempotency_key=idempotency_key
        )

    def post_multipart(
        self,
        path: str,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """POST with multipart/form-data encoding (for file uploads).

        Args:
            path: API endpoint path.
            files: Dict of file fields, e.g.
                ``{"file": ("name.jpg", open_file, "image/jpeg")}``.
            data: Additional form fields sent alongside the file.
        """
        url = urljoin(self.base_url, path.lstrip("/"))
        # Let requests set the multipart Content-Type with boundary
        headers = {"Content-Type": None}

        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Request POST %s multipart (attempt %d/%d) data=%s",
                    url,
                    attempt + 1,
                    self.max_retries,
                    data,
                )
                response = self.session.request(
                    method="POST",
                    url=url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.timeout,
                )
                return self._handle_response(response)

            except (RateLimitError, ServerError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait = RETRY_BACKOFF * (2**attempt)
                    if isinstance(e, RateLimitError) and e.retry_after:
                        wait = e.retry_after
                    time.sleep(wait)
                else:
                    raise

            except requests.exceptions.ConnectionError as e:
                last_error = HandwryttenError(
                    f"Connection error: {e}", status_code=None
                )
                if attempt < self.max_retries - 1:
                    time.sleep(RETRY_BACKOFF * (2**attempt))
                else:
                    raise last_error

            except requests.exceptions.Timeout:
                last_error = HandwryttenError(
                    f"Request timed out after {self.timeout}s", status_code=None
                )
                if attempt < self.max_retries - 1:
                    time.sleep(RETRY_BACKOFF * (2**attempt))
                else:
                    raise last_error

        raise last_error  # type: ignore[misc]

    def put(self, path: str, json_body: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("PUT", path, json_body=json_body)

    def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("DELETE", path, params=params)
