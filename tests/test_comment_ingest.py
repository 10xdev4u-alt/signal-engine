"""Comment feed ingestion: age cutoff, oldest-first, request budget."""

from datetime import UTC

import httpx
import pytest

from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.ingest.fetch import fetch_comments
from signal_engine.sources.polite import PacedClient

FIX = __import__("pathlib").Path(__file__).parent / "fixtures"
COMMENT_FEED = (FIX / "comment_feed.atom").read_text()


def insert_post(conn, post_id, created_utc):
    conn.execute(
        "INSERT INTO posts(id, subreddit, title, author, selftext, permalink, created_utc) "
        "VALUES (?, 'smallbusiness', 't', '/u/a', '', ?, ?)",
        (post_id, f"https://old.reddit.com/r/smallbusiness/comments/{post_id}/", created_utc),
    )
    conn.commit()


@pytest.fixture()
def db(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    return conn


def comment_client(calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        pid = request.url.path.split("/comments/")[1].strip("/")
        # unique comment ids per post so cross-post upserts never collide
        return httpx.Response(200, text=COMMENT_FEED.replace("t1_cmt0", f"t1_{pid}_c0"))

    return PacedClient(
        pace_seconds=1.0,
        sleep=lambda s: None,
        now=lambda: 0.0,
        transport=httpx.MockTransport(handler),
    )


NOW = 1787000000.0  # fixed epoch


def _iso(epoch: float) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(epoch, tz=UTC).isoformat()


def test_only_recent_posts_selected_oldest_first(db):
    insert_post(db, "p_new", _iso(NOW - 1 * 3600))         # 1h old
    insert_post(db, "p_old", _iso(NOW - 36 * 3600))        # 36h old
    insert_post(db, "p_ancient", _iso(NOW - 100 * 24 * 3600))  # 100 days old
    calls: list[str] = []
    summary = fetch_comments(
        db, comment_client(calls), max_age_h=48, budget=10, now_fn=lambda: NOW
    )
    fetched_ids = [pid for pid, _ in summary.fetched_counts]
    assert fetched_ids == ["p_old", "p_new"]  # oldest first, ancient excluded
    assert db.execute("SELECT COUNT(*) c FROM comments").fetchone()["c"] == 4


def test_budget_caps_requests_per_run(db):
    for i in range(5):
        insert_post(db, f"p{i}", _iso(NOW - 3600))
    calls: list[str] = []
    fetch_comments(db, comment_client(calls), max_age_h=48, budget=2, now_fn=lambda: NOW)
    assert len(calls) == 2


def test_done_posts_never_refetched(db):
    insert_post(db, "p1", _iso(NOW - 3600))
    calls: list[str] = []
    fetch_comments(db, comment_client(calls), max_age_h=48, budget=5, now_fn=lambda: NOW)
    first_count = len(calls)
    assert first_count == 1
    fetch_comments(db, comment_client(calls), max_age_h=48, budget=5, now_fn=lambda: NOW)
    assert len(calls) == first_count  # zero new requests


def test_error_response_still_marks_done(db):
    def handler(request):
        return httpx.Response(404, text="gone")

    client = PacedClient(
        pace_seconds=1.0, sleep=lambda s: None, now=lambda: 0.0,
        transport=httpx.MockTransport(handler),
    )
    insert_post(db, "p_dead", _iso(NOW - 3600))
    summary = fetch_comments(db, client, max_age_h=48, budget=5, now_fn=lambda: NOW)
    assert summary.errors == [("p_dead", "HTTP 404")]
    done = db.execute(
        "SELECT comments_done_at FROM posts WHERE id = 'p_dead'"
    ).fetchone()["comments_done_at"]
    assert done is not None
