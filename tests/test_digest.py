"""Digest golden tests on a seeded fixture database."""

from pathlib import Path

import pytest

from signal_engine.analyze import build_phrase_stats, rebuild_clusters, record_intent
from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.digest.daily import build_digest, write_digest_file

TODAY = "2026-08-22"


@pytest.fixture()
def db(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    posts = [
        ("t3_a", "Chargebacks destroying my margin", "spent 400 on fee",
         "2026-08-22T09:00:00+00:00"),
        ("t3_b", "How do I stop chargebacks destroying my margin?", "third this month",
         "2026-08-22T10:00:00+00:00"),
        ("t3_c", "These chargebacks destroying my margin", "bank does nothing",
         "2026-08-21T08:00:00+00:00"),
    ]
    for pid, title, body, created in posts:
        domain = "https://old.reddit.com/r/smallbusiness/comments/"
        permalink = domain + pid + "/"
        sql = "INSERT INTO posts(id, subreddit, title, selftext, permalink, created_utc) VALUES (?, 'smallbusiness', ?, ?, ?, ?)"  # noqa: E501
        conn.execute(sql, (pid, title, body, permalink, created))
    # an old phrase from two weeks ago that should NOT count as new today
    conn.execute(
        "INSERT INTO phrase_stats(subreddit, phrase, day, count) "
        "VALUES ('smallbusiness', 'old pain', '2026-08-05', 9)"
    )
    conn.commit()
    return conn


def test_digest_sections_and_quotes(db):
    build_phrase_stats(db)
    record_intent(db)
    rebuild_clusters(db)
    digest = build_digest(db, date=TODAY)
    md = digest.md
    assert f"# Signal digest — {TODAY}" in md
    assert "chargeback" in md  # the merged cluster label surfaces
    assert "old.reddit.com/r/smallbusiness/comments/t3_a/" in md  # quote permalink
    assert len(digest.rising_pains) >= 1  # today's cluster activity is ranked
    assert "Fetch errors in last 24h: 0" in md


def test_digest_never_silently_empty(db):
    # wipe analytic tables: quiet day must still render explicit lines
    db.execute("DELETE FROM pain_clusters")
    db.commit()
    digest = build_digest(db, date=TODAY)
    assert "Nothing rose" in digest.md or "Top rising pains" in digest.md


def test_digest_idempotent_per_date(db):
    build_digest(db, date=TODAY)
    build_digest(db, date=TODAY)  # regenerate overwrites, never duplicates
    rows = db.execute("SELECT * FROM digests WHERE date = ?", (TODAY,)).fetchall()
    assert len(rows) == 1


def test_digest_new_phrase_requires_prior_absence(db):
    build_phrase_stats(db)
    db.execute("INSERT INTO phrase_stats(subreddit, phrase, day, count) VALUES ('smallbusiness', 'brand worry', ?, 5)", (TODAY,))  # noqa: E501
    db.execute("INSERT INTO phrase_stats(subreddit, phrase, day, count) VALUES ('smallbusiness', 'stale topic', '2026-08-08', 4)")  # noqa: E501
    db.commit()
    digest = build_digest(db, date=TODAY)
    phrases = [p["phrase"] for p in digest.new_phrases]
    assert "brand worry" in phrases  # never seen before today
    assert "stale topic" not in phrases  # seen inside the lookback window
    assert "old pain" not in phrases  # seen before the lookback window


def test_write_digest_file(db, tmp_path):
    digest = build_digest(db, date=TODAY)
    out = write_digest_file(digest, data_dir=str(tmp_path))
    assert Path(out).exists() and TODAY in Path(out).read_text()
