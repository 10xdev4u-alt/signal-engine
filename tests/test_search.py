"""Search page tests: no SQL in this file — seeding goes through the store API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.ingest.store import upsert_post
from signal_engine.sources.base import PostEntry
from signal_engine.web.app import create_app

MALFORMED = (
    Path(__file__).parent / "fixtures" / "malformed_queries.txt"
).read_text().splitlines()


def make_post(pid: str, title: str, body: str, created: str) -> PostEntry:
    return PostEntry(
        id=f"t3_{pid}",
        subreddit="smallbusiness",
        title=title,
        author="/u/tester",
        selftext=body,
        permalink=f"https://old.reddit.com/r/smallbusiness/comments/{pid}/",
        created_utc=created,
    )


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    http = TestClient(create_app())
    return http, conn


def seed_search_corpus(conn):
    upsert_post(conn, make_post(
        "s1", "Chargebacks destroying margin", "tried dispute template",
        "2026-08-20T10:00:00+00:00"))
    upsert_post(conn, make_post(
        "s2", "Sourdough starter question", "smells like acetone",
        "2026-08-21T10:00:00+00:00"))
    for i in range(7):
        upsert_post(
            conn,
            make_post(f"s3{i}", f"chargebacks case {i}", "body", f"2026-08-1{i}T09:00:00+00:00"),
        )


def test_search_finds_term_and_excludes_others(client):
    http, conn = client
    seed_search_corpus(conn)
    page = http.get("/search", params={"q": "chargeback"})
    assert page.status_code == 200
    assert "Chargebacks destroying margin" in page.text
    assert "Sourdough" not in page.text


def test_quoted_phrase_narrows(client):
    http, conn = client
    seed_search_corpus(conn)
    phrase_page = http.get("/search", params={"q": '"dispute template"'})
    assert phrase_page.status_code == 200
    assert "comments/s1/" in phrase_page.text  # only the matching post links out


def test_search_filters_narrow_results(client):
    http, conn = client
    seed_search_corpus(conn)
    no_comments = http.get("/search", params={"q": "chargeback", "type": "comment"})
    assert "No matches" in no_comments.text
    future_only = http.get("/search", params={"q": "chargeback", "frm": "2026-08-25"})
    assert "No matches" in future_only.text
    other_sub = http.get("/search", params={"q": "chargeback", "sub": "teaching"})
    assert "No matches" in other_sub.text


def test_malformed_queries_never_500(client):
    http, _ = client
    payloads_path = Path(__file__).parent / "fixtures" / "malformed_queries.txt"
    for evil in payloads_path.read_text().splitlines():
        if not evil:
            continue
        response = http.get("/search", params={"q": evil})
        assert response.status_code == 200, f"{evil!r} -> {response.status_code}"


def test_search_count_display(client):
    http, conn = client
    seed_search_corpus(conn)
    page = http.get("/search", params={"q": "chargeback"})
    assert "8 result(s)" in page.text
    assert "items indexed" in page.text
