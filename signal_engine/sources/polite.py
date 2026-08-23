"""Polite HTTP fetching: minimum interval, backoff on 429/403, circuit breaker."""

from __future__ import annotations

import time
from collections.abc import Callable

import httpx

USER_AGENT = "signal-engine/0.1 (personal research; contact via repo)"
BLOCK_STATUSES = {429, 403}
MAX_BACKOFF_SECONDS = 8 * 3600


class CircuitBreakerOpen(RuntimeError):
    """Raised once too many consecutive block responses have been seen."""


def _retry_after_seconds(response: httpx.Response) -> int | None:
    raw = response.headers.get("retry-after")
    if raw is None:
        return None
    try:
        return max(0, int(float(raw)))
    except ValueError:
        return None


class PacedClient:
    """Sequential GETs separated by at least ``pace_seconds``.

    Sleep and clock are injectable so tests never wait for real.
    """

    def __init__(
        self,
        pace_seconds: float = 45.0,
        max_consecutive_blocks: int = 5,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.monotonic,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.pace_seconds = pace_seconds
        self.max_consecutive_blocks = max_consecutive_blocks
        self._sleep = sleep
        self._now = now
        self._client = httpx.Client(
            transport=transport,
            headers={"User-Agent": USER_AGENT},
            timeout=30.0,
            follow_redirects=True,
        )
        self._last_request_at: float | None = None
        self.consecutive_blocks = 0
        # (url, seconds_waited) for every backoff, oldest first
        self.backoff_events: list[tuple[str, int]] = []
        # every raw HTTP attempt, including blocked ones: (url, status, bytes)
        self.attempt_log: list[tuple[str, int, int]] = []

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PacedClient:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def get(self, url: str, extra_headers: dict[str, str] | None = None) -> httpx.Response:
        if self.consecutive_blocks >= self.max_consecutive_blocks:
            raise CircuitBreakerOpen(
                f"circuit open after {self.consecutive_blocks} consecutive blocks"
            )
        if self._last_request_at is not None:
            elapsed = self._now() - self._last_request_at
            if elapsed < self.pace_seconds:
                self._sleep(self.pace_seconds - elapsed)
        while True:
            response = self._client.get(url, headers=extra_headers)
            self._last_request_at = self._now()
            self.attempt_log.append((url, response.status_code, len(response.content)))
            if response.status_code in BLOCK_STATUSES:
                self.consecutive_blocks += 1
                if self.consecutive_blocks >= self.max_consecutive_blocks:
                    # no sleep before raising — nobody waits on an aborted run
                    raise CircuitBreakerOpen(
                        f"circuit open after {self.consecutive_blocks} "
                        f"consecutive blocks (last {response.status_code} on {url})"
                    )
                delay = _retry_after_seconds(response)
                if delay is None:
                    delay = self.pace_seconds * (2 ** min(self.consecutive_blocks, 7))
                # server-supplied Retry-After gets the same ceiling as ours
                delay = min(delay, MAX_BACKOFF_SECONDS)
                self.backoff_events.append((url, int(delay)))
                self._sleep(delay)
                continue
            self.consecutive_blocks = 0
            return response
