"""Golden tests for the deterministic analyzer (issue #6)."""

import pytest

from signal_engine.analyze import (
    build_phrase_stats,
    frustration_level,
    intent_score,
    rebuild_clusters,
    record_intent,
)
from signal_engine.db import add_subreddit, connect, migrate

CHARGEBACK_POSTS = [
    "How do I stop chargebacks destroying my margin? Spent $400 on fees this month.",
    "Chargebacks are destroying my margin, spent another $500 on fees this month.",
    "Chargebacks destroying my margin too, banks never side with small sellers on fee disputes.",
]
SOURDOUGH_POST = "My sourdough starter smells like acetone, is it dead?"
OFF_TOPIC = "Margins look great this quarter, team."


@pytest.fixture()
def db(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    for i, text in enumerate(CHARGEBACK_POSTS):
        conn.execute(
            "INSERT INTO posts(id, subreddit, title, selftext, permalink, created_utc) "
            "VALUES (?, 'smallbusiness', ?, '', ?, ?)",
            (f"t3_cb{i}", text, f"https://old.reddit.com/r/smallbusiness/comments/cb{i}/",
             f"2026-08-20T1{i}:00:00+00:00"),
        )
    conn.execute(
        "INSERT INTO posts(id, subreddit, title, selftext, permalink, created_utc) "
        "VALUES ('t3_dough', 'smallbusiness', ?, '', "
        "'https://old.reddit.com/r/smallbusiness/comments/dough/', '2026-08-21T10:00:00+00:00')",
        (SOURDOUGH_POST,),
    )
    conn.commit()
    return conn


def test_intent_score_calibration():
    assert intent_score("Margins look good this quarter.") == 1
    assert intent_score("Is there a way to automate invoicing?") == 2
    assert intent_score("Any recommendations for invoicing software?") == 4
    assert intent_score("How do I stop chargebacks? Worth paying for a service?") == 5


def test_frustration_levels():
    assert frustration_level("Great news everyone, sales are up.") == 0
    assert frustration_level("I got burned by that vendor.") == 1
    assert frustration_level("Wasted money, wasted time, total scam.") == 2
    assert frustration_level(
        "Wasted money, wasted time, scam, about to give up, tried everything, nothing works."
    ) == 3


def test_phrase_stats_counts_exact_bigram(db):
    written = build_phrase_stats(db)
    assert written > 0
    row = db.execute(
        "SELECT count FROM phrase_stats WHERE phrase = 'destroying margin' "
        "AND subreddit = 'smallbusiness'"
    ).fetchone()
    assert row is not None and row["count"] == 3  # once per chargeback post
    # deterministic rebuild
    assert build_phrase_stats(db) == written


def test_record_intent_scores_and_skips_ones(db):
    written = record_intent(db)
    assert written >= 2  # chargeback posts carry asks
    scored = {
        row["ref_id"]: row["heuristic_score"]
        for row in db.execute("SELECT ref_id, heuristic_score FROM intent_scores")
    }
    assert scored.get("t3_cb0", 0) >= 3
    assert scored.get("t3_dough", 0) in (None, 2)  # sourdough curiosity at best
    assert "t3_dough" not in scored or scored["t3_dough"] < 3
    # idempotent: second run scores nothing new
    assert record_intent(db) == 0


def test_clusters_group_same_problem_separate_other(db):
    build_phrase_stats(db)
    clusters = rebuild_clusters(db)
    assert clusters >= 2
    rows = db.execute(
        "SELECT id, label, mention_count FROM pain_clusters ORDER BY mention_count DESC"
    ).fetchall()
    top = rows[0]
    assert top["mention_count"] == 3  # the three chargeback posts merged
    assert "chargeback" in top["label"]
    dough = [
        r for r in rows
        if db.execute(
            "SELECT 1 FROM cluster_members WHERE cluster_id = ? AND ref_id = 't3_dough'",
            (r["id"],),
        ).fetchone()
    ]
    assert len(dough) == 1 and dough[0]["mention_count"] == 1
    # every cluster exposes quotes with permalinks resolvable
    for r in rows:
        members = db.execute(
            "SELECT ref_type, ref_id, quote FROM cluster_members WHERE cluster_id = ?",
            (r["id"],),
        ).fetchall()
        assert len(members) == r["mention_count"]
        assert all(m["quote"] for m in members)
