"""Pacing, backoff, and breaker tests — injected clock, never real sleeps."""

import httpx
import pytest

from signal_engine.sources.polite import CircuitBreakerOpen, PacedClient


class FakeClock:
    def __init__(self):
        self.t = 1000.0
        self.slept: list[float] = []

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds
        self.slept.append(seconds)


def _client(handler, clock, pace=45.0):
    return PacedClient(
        pace_seconds=pace,
        sleep=clock.sleep,
        now=clock.now,
        transport=httpx.MockTransport(handler),
    )


def test_two_requests_neever_closer_than_pace():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, text="ok")

    clock = FakeClock()
    client = _client(handler, clock)
    client.get("https://example.com/a")
    client.get("https://example.com/b")  # immediately after — must wait pace
    assert clock.slept == [45.0]
    assert len(calls) == 2


def test_429_retries_after_header_delay_without_raising():
    attempts = {"n": 0}

    def handler(request):
        attempts["n"] += 1
        if attempts["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200, text="feed")

    clock = FakeClock()
    client = _client(handler, clock)
    response = client.get("https://example.com/feed")
    assert response.status_code == 200
    assert clock.slept == [7.0]
    assert client.backoff_events == [("https://example.com/feed", 7)]
    assert client.consecutive_blocks == 0  # success resets the counter


def test_exponential_backoff_when_no_retry_after():
    def handler(request):
        return httpx.Response(429)

    clock = FakeClock()
    client = _client(handler, clock)
    with pytest.raises(CircuitBreakerOpen):
        client.get("https://example.com/x")
    # four waits happen (blocks 1-4); on block 5 the breaker aborts without sleeping
    assert clock.slept == [90.0, 180.0, 360.0, 720.0]
    # every blocked attempt was recorded for logging
    assert len(client.attempt_log) == 5
    assert {status for _, status, _ in client.attempt_log} == {429}


def test_breaker_blocks_subsequent_calls_until_success_resets():
    state = {"fail": 3}

    def handler(request):
        if state["fail"] > 0:
            state["fail"] -= 1
            return httpx.Response(403, text="Blocked")
        return httpx.Response(200, text="fine")

    clock = FakeClock()
    client = PacedClient(
        pace_seconds=1.0, max_consecutive_blocks=3, sleep=clock.sleep, now=clock.now,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(CircuitBreakerOpen):
        client.get("https://example.com/1")
    # a new client models the next cron run; recovery clears the breaker
    client2 = PacedClient(
        pace_seconds=1.0, max_consecutive_blocks=3, sleep=clock.sleep, now=clock.now,
        transport=httpx.MockTransport(lambda request: httpx.Response(200)),
    )
    assert client2.get("https://example.com/2").status_code == 200
