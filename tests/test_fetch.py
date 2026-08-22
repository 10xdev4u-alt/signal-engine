"""End-to-end fetch orchestration over a mock transport — zero real network."""

from pathlib import Path

import httpx
import pytest

from signal_engine.db import add_subreddit, connect, get_setting, migrate
from signal_engine.ingest.fetch import fetch_subreddits
from signal_engine.sources.polite import PacedClient

FIX = Path(__file__).parent / "fixtures"
POST_FEED = (FIX / "post_feed.atom").read_text()
ETAG = 'W/"v1"'


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def make_client(calls: list[int]):
    """200 with fixture + ETag on first fetch; 304 whenever If-None-Match matches."""

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        inm = request.headers.get("if-none-match")
        if inm is not None and inm == ETAG:
            return httpx.Response(304)
        return httpx.Response(200, text=POST_FEED, headers={"ETag": ETAG})

    return PacedClient(
        pace_seconds=1.0,
        sleep=lambda s: None,
        now=lambda: 0.0,
        transport=httpx.MockTransport(handler),
    )


@pytest.fixture()
def db(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    return conn


def test_fetch_stores_posts_and_etag(db):
    calls: list[int] = []
    summary = fetch_subreddits(
        db, make_client(calls), now_fn=FakeClock(), min_poll_interval=10**9
    )
    assert summary.fetched == ["smallbusiness"]
    assert summary.new_posts == 2
    assert db.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"] == 2
    log = db.execute("SELECT * FROM fetch_log").fetchone()
    assert log["http_status"] == 200 and log["bytes"] > 0
    assert get_setting(db, "etag:smallbusiness") == ETAG


def test_second_fetch_is_304_then_third_skips_entirely(db):
    calls: list[int] = []
    client = make_client(calls)
    clock = FakeClock()
    fetch_subreddits(db, client, now_fn=clock, min_poll_interval=900.0)
    calls_after_first = len(calls)
    # second poll: etag matches -> 304; still a request, nothing stored
    s2 = fetch_subreddits(db, client, now_fn=clock, min_poll_interval=900.0)
    assert s2.not_modified == ["smallbusiness"]
    assert len(calls) == calls_after_first + 1
    # third poll right after a 304 within the window: skipped with ZERO requests
    s3 = fetch_subreddits(db, client, now_fn=clock, min_poll_interval=900.0)
    assert s3.skipped == ["smallbusiness"]
    assert len(calls) == calls_after_first + 1


def test_429_is_logged_and_retried_not_raised(db):
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) == 1:
            return httpx.Response(429, headers={"Retry-After": "3"})
        return httpx.Response(200, text=POST_FEED)

    client = PacedClient(
        pace_seconds=1.0, sleep=lambda s: None, now=lambda: 0.0,
        transport=httpx.MockTransport(handler),
    )
    summary = fetch_subreddits(db, client, now_fn=FakeClock(), min_poll_interval=10**9)
    assert summary.fetched == ["smallbusiness"]
    rows = db.execute("SELECT http_status FROM fetch_log ORDER BY id").fetchall()
    assert [r["http_status"] for r in rows] == [429, 200]


def test_breaker_stops_run_and_reports(db):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Blocked")

    add_subreddit(db, "teachers")
    client = PacedClient(
        pace_seconds=1.0, max_consecutive_blocks=3, sleep=lambda s: None, now=lambda: 0.0,
        transport=httpx.MockTransport(handler),
    )
    summary = fetch_subreddits(db, client, names=["smallbusiness", "teachers"])
    assert summary.breaker_tripped is not None
    assert "circuit open" in summary.breaker_tripped
