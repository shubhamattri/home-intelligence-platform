"""Resilient async HTTP client shared by services and clients.

Wraps httpx with tenacity retries and a minimal circuit breaker so a flaky
downstream (another service or a 3rd-party API) degrades gracefully instead of
hanging the caller.
"""

from __future__ import annotations

import time
from types import TracebackType
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .errors import UpstreamError

_RETRYABLE = (httpx.TransportError, httpx.HTTPStatusError)


class CircuitBreaker:
    """Trips open after ``fail_max`` consecutive failures for ``reset_s`` seconds."""

    def __init__(self, fail_max: int = 5, reset_s: float = 30.0) -> None:
        self.fail_max = fail_max
        self.reset_s = reset_s
        self._failures = 0
        self._opened_at: float | None = None

    def allow(self) -> bool:
        if self._opened_at is None:
            return True
        if (time.monotonic() - self._opened_at) >= self.reset_s:
            # half-open: allow one trial
            self._opened_at = None
            self._failures = 0
            return True
        return False

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.fail_max:
            self._opened_at = time.monotonic()


class ResilientClient:
    """Async HTTP client with retry + circuit breaker. Use as an async context manager."""

    def __init__(
        self,
        base_url: str = "",
        timeout_s: float = 30.0,
        retries: int = 3,
        breaker: CircuitBreaker | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url, timeout=timeout_s, headers=headers or {}
        )
        self._retries = retries
        self._breaker = breaker or CircuitBreaker()

    async def __aenter__(self) -> ResilientClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._client.aclose()

    async def request_json(self, method: str, url: str, **kwargs: Any) -> Any:
        """Perform a request and return parsed JSON, with retry + breaker."""

        if not self._breaker.allow():
            raise UpstreamError(f"circuit open for {url}")

        @retry(
            reraise=True,
            stop=stop_after_attempt(self._retries),
            wait=wait_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception_type(_RETRYABLE),
        )
        async def _do() -> Any:
            resp = await self._client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()

        try:
            result = await _do()
        except _RETRYABLE as e:
            self._breaker.record_failure()
            raise UpstreamError(f"{method} {url} failed: {e}") from e
        self._breaker.record_success()
        return result

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        return await self.request_json("GET", url, **kwargs)

    async def post_json(self, url: str, **kwargs: Any) -> Any:
        return await self.request_json("POST", url, **kwargs)
