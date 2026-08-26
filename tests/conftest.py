"""Shared test fixtures — uses store API only, no raw SQL seeds."""
import pytest
from fastapi.testclient import TestClient

from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.ingest.store import upsert_post
from signal_engine.sources.base import PostEntry
from signal_engine.web.app import create_app


def _post(pid: str, subreddit: str, title: str, body: str) -> PostEntry:
    return PostEntry(
        id=f"t3_{pid}", subreddit=subreddit, title=title,
        author="/u/tester", selftext=body,
        permalink=f"https://old.reddit.com/r/{subreddit}/comments/{pid}/",
        created_utc="2026-08-20T10:00:00+00:00",
    )


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    http = TestClient(create_app())
    return http, conn


@pytest.fixture()
def populated_client(client):
    """Client with seeded posts and rebuilt clusters."""
    http, conn = client
    upsert_post(conn, _post("s1", "smallbusiness", "Chargebacks destroying margin", "dispute fee"))
    upsert_post(conn, _post("s2", "smallbusiness", "Sourdough starter", "smells acetone"))
    for i in range(7):
        upsert_post(conn, _post(f"s3{i}", "smallbusiness", f"chargeback case {i}", "body"))
    from signal_engine.analyze.cluster import rebuild_clusters
    rebuild_clusters(conn)
    from signal_engine.analyze.questions import record_intent
    record_intent(conn)
    from signal_engine.digest.daily import build_digest
    build_digest(conn)
    return http, conn
