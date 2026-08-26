"""Search API tests: tests the pure JSON API endpoints."""

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
    resp = http.get("/api/search", params={"q": "chargeback"})
    assert resp.status_code == 200
    data = resp.json()
    titles = [r["title"] for r in data["results"]]
    assert any("Chargebacks destroying margin" in t for t in titles)
    assert not any("Sourdough" in t for t in titles)


def test_quoted_phrase_narrows(client):
    http, conn = client
    seed_search_corpus(conn)
    upsert_post(conn, make_post(
        "s9", "Dispute templates collection", "many dispute templates here",
        "2026-08-22T10:00:00+00:00"))
    resp = http.get("/api/search", params={"q": '"dispute template"'})
    assert resp.status_code == 200
    data = resp.json()
    permalinks = [r["permalink"] for r in data["results"]]
    assert any("comments/s1/" in p for p in permalinks)
    assert not any("comments/s9/" in p for p in permalinks)


def test_search_filters_narrow_results(client):
    http, conn = client
    seed_search_corpus(conn)
    no_comments = http.get("/api/search", params={"q": "chargeback", "type": "comment"})
    assert no_comments.json()["results"] == []
    future_only = http.get("/api/search", params={"q": "chargeback", "from": "2026-08-25"})
    assert future_only.json()["results"] == []
    other_sub = http.get("/api/search", params={"q": "chargeback", "sub": "teaching"})
    assert other_sub.json()["results"] == []


def test_malformed_queries_never_500(client):
    http, _ = client
    for evil in MALFORMED:
        if not evil:
            continue
        resp = http.get("/api/search", params={"q": evil})
        assert resp.status_code == 200, f"{evil!r} -> {resp.status_code}"


def test_search_count_display(client):
    http, conn = client
    seed_search_corpus(conn)
    resp = http.get("/api/search", params={"q": "chargeback"})
    data = resp.json()
    assert len(data["results"]) == 8
    assert data["indexed"] > 0


def test_eval_api_mark_creates_row(client):
    http, conn = client
    seed_search_corpus(conn)
    resp = http.post("/api/eval/post/t3_s1?verdict=real_problem")
    assert resp.status_code == 200
    row = conn.execute(
        "SELECT verdict FROM eval_marks WHERE ref_type = 'post' AND ref_id = 't3_s1'"
    ).fetchone()
    assert row is not None and row["verdict"] == "real_problem"


def test_eval_api_overview(client):
    http, _ = client
    resp = http.get("/api/eval")
    assert resp.status_code == 200
    data = resp.json()
    assert "p10" in data
    assert "evaluated" in data
    assert "sample_size" in data


def test_eval_api_marks_export(client):
    http, _ = client
    http.post("/api/eval/post/t3_s1?verdict=real_problem")
    resp = http.get("/api/eval/marks.json")
    assert resp.status_code == 200
    marks = resp.json()
    assert isinstance(marks, list) and marks and marks[0]["ref_id"] == "t3_s1"
