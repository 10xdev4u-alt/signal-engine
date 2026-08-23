"""Dashboard tests: every page renders on empty and populated databases."""

import pytest
from fastapi.testclient import TestClient

from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.web.app import create_app, run_server


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    yield client_for(monkeypatch), conn


def client_for(monkeypatch):
    return TestClient(create_app())


def seed_cluster(conn):
    conn.execute(
        "INSERT INTO posts(id, subreddit, title, selftext, permalink, created_utc) "
        "VALUES ('t3_cb', 'smallbusiness', 'Chargebacks destroying margin', "
        "'spent 400 on fee', 'https://old.reddit.com/r/smallbusiness/comments/cb/', "
        "'2026-08-20T10:00:00+00:00')"
    )
    conn.execute(
        "INSERT INTO pain_clusters(label, mention_count, desperation_score) "
        "VALUES ('chargeback fee margin', 1, 2.0)"
    )
    conn.execute(
        "INSERT INTO cluster_members(cluster_id, ref_type, ref_id, quote) "
        "VALUES (1, 'post', 't3_cb', 'How do I stop chargebacks?')"
    )
    conn.execute(
        "INSERT INTO fetch_log(url, kind, http_status, bytes) "
        "VALUES ('https://www.reddit.com/r/x/.rss', 'post_feed', 429, 10)"
    )
    conn.commit()


def test_all_routes_render_on_empty_db(client):
    http, _ = client
    for path in ("/digest", "/pains", "/status", "/profile/nope"):
        response = http.get(path, follow_redirects=False)
        assert response.status_code in (200, 302), f"{path} -> {response.status_code}"
    assert http.get("/", follow_redirects=False).headers["location"] == "/digest"


def test_pain_pages_render_populated(client):
    http, conn = client
    seed_cluster(conn)
    listing = http.get("/pains")
    assert listing.status_code == 200
    assert "chargeback" in listing.text
    detail = http.get("/pains/1")
    assert detail.status_code == 200
    assert "How do I stop chargebacks?" in detail.text
    assert "old.reddit.com" in detail.text
    status_page = http.get("/status")
    assert "429" in status_page.text  # recent problems surfaced


def test_server_refuses_non_loopback():
    with pytest.raises(ValueError):
        run_server(host="0.0.0.0", port=1)


def test_unknown_pain_returns_404(client):
    http, _ = client
    response = http.get("/pains/424242")
    assert response.status_code == 404
