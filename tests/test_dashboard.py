"""Dashboard API tests: every API endpoint returns correct JSON."""

import pytest
from fastapi.testclient import TestClient

from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.ingest.store import upsert_post
from signal_engine.sources.base import PostEntry
from signal_engine.web.app import create_app, run_server


def _post(pid: str, title: str, body: str) -> PostEntry:
    return PostEntry(
        id=f"t3_{pid}", subreddit="smallbusiness", title=title,
        author="/u/tester", selftext=body,
        permalink=f"https://old.reddit.com/r/smallbusiness/comments/{pid}/",
        created_utc="2026-08-20T10:00:00+00:00",
    )


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    yield TestClient(create_app()), conn


def test_all_api_endpoints_return_200_on_empty_db(client):
    http, _ = client
    for path in ("/api/digest", "/api/pains", "/api/status", "/api/profile/nope"):
        resp = http.get(path)
        assert resp.status_code == 200, f"{path} -> {resp.status_code}"


def test_pain_api_returns_populated_data(client):
    http, conn = client
    upsert_post(conn, _post("cb", "Chargebacks destroying margin", "spent 400 on fee"))
    from signal_engine.analyze.cluster import rebuild_clusters
    rebuild_clusters(conn)
    resp = http.get("/api/pains")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["clusters"]) > 0


def test_pain_detail_api_returns_evidence(client):
    http, conn = client
    upsert_post(conn, _post("cb", "Chargebacks destroying margin", "spent 400 on fee"))
    from signal_engine.analyze.cluster import rebuild_clusters
    rebuild_clusters(conn)
    resp = http.get("/api/pains/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cluster"]["mention_count"] >= 1
    assert len(data["members"]) > 0


def test_status_api_returns_subs(client):
    http, conn = client
    resp = http.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["subs"]) > 0
    assert data["subs"][0]["name"] == "smallbusiness"


def test_server_refuses_non_loopback():
    with pytest.raises(ValueError):
        run_server(host="0.0.0.0", port=1)


def test_unknown_pain_returns_404(client):
    http, _ = client
    resp = http.get("/api/pains/424242")
    assert resp.status_code == 404
