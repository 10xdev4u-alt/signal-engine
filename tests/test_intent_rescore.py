"""LLM intent re-scoring tests: NullProvider skip, budget cap, error degrade."""

from __future__ import annotations

import datetime as dt

import pytest

from signal_engine.analyze import record_intent
from signal_engine.analyze.questions import rescore_with_llm
from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.ingest.store import upsert_comment, upsert_post
from signal_engine.llm.base import NullProvider
from signal_engine.llm.budget import CallCost, record_spend, spent_this_month
from signal_engine.sources.base import CommentEntry, PostEntry


class StubProvider:
    name = "stub"
    model = "claude-haiku-4-5-20251001"

    def __init__(self, body):
        self.body = body
        self.calls = 0

    def complete(self, system, user, max_tokens=400):
        self.calls += 1
        return self.body


class FailingProvider:
    name = "failing"
    model = "claude-haiku-4-5-20251001"

    def complete(self, system, user, max_tokens=400):
        raise RuntimeError("simulated LLM outage")


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    today = dt.date.today().isoformat()
    upsert_post(conn, PostEntry(
        id="t3_p1", subreddit="smallbusiness",
        title="How do I stop chargebacks destroying my margin?",
        author="/u/a", selftext="spent $400 on fees this month",
        permalink="https://old.reddit.com/r/smallbusiness/comments/p1/",
        created_utc=f"{today}T10:00:00+00:00",
    ))
    upsert_post(conn, PostEntry(
        id="t3_p2", subreddit="smallbusiness",
        title="What should I do about chargebacks?",
        author="/u/b", selftext="looking for any recommendations",
        permalink="https://old.reddit.com/r/smallbusiness/comments/p2/",
        created_utc=f"{today}T11:00:00+00:00",
    ))
    upsert_post(conn, PostEntry(
        id="t3_p3", subreddit="smallbusiness",
        title="Random thought: my fridge is humming, is it broken?",
        author="/u/c", selftext="anyone know how to fix a humming fridge?",
        permalink="https://old.reddit.com/r/smallbusiness/comments/p3/",
        created_utc=f"{today}T12:00:00+00:00",
    ))
    upsert_comment(conn, CommentEntry(
        id="t1_c1", post_id="t3_p1", subreddit="smallbusiness",
        author="/u/d", body="any tool recommendations for dispute templates?",
        permalink="https://old.reddit.com/r/smallbusiness/comments/p1/_/c1/",
        created_utc=f"{today}T13:00:00+00:00",
    ))
    record_intent(conn)
    return conn


def test_null_provider_skips_immediately(db):
    result = rescore_with_llm(db, NullProvider())
    assert result == 0
    # no rows touched
    scored = db.execute(
        "SELECT COUNT(*) c FROM intent_scores WHERE llm_score IS NOT NULL"
    ).fetchone()["c"]
    assert scored == 0


def test_budget_exhausted_skips(db):
    # Pre-load the ledger past the cap (0.5) by spending 1.0 total
    cheap = CallCost(
        model="claude-haiku-4-5-20251001", input_tokens=1, output_tokens=1, cost_usd=1.0
    )
    record_spend(db, cheap)
    assert spent_this_month(db) == pytest.approx(1.0, abs=1e-6)
    provider = StubProvider("4")
    result = rescore_with_llm(db, provider, cap=0.5)
    assert result == 0
    assert provider.calls == 0


def test_updates_llm_score_and_respects_existing(db):
    provider = StubProvider("4")
    result = rescore_with_llm(db, provider, cap=1.0, max_items=10)
    # 3 posts + 1 comment with heuristic >= 3; rescore_with_llm should have hit them
    assert result == 4
    assert provider.calls == 4
    # Every re-scored row has a non-NULL llm_score
    scored = db.execute(
        "SELECT ref_type, ref_id, llm_score FROM intent_scores"
        " WHERE llm_score IS NOT NULL ORDER BY scored_at"
    ).fetchall()
    assert len(scored) == 4
    for row in scored:
        assert row["llm_score"] == 4


def test_idempotent_does_not_rescore_already_scored(db):
    StubProvider("4")
    rescore_with_llm(db, StubProvider("4"), cap=1.0, max_items=10)
    second = rescore_with_llm(db, StubProvider("4"), cap=1.0, max_items=10)
    assert second == 0  # no new targets because llm_score IS NOT NULL excludes them


def test_max_items_caps_run(db):
    provider = StubProvider("3")
    result = rescore_with_llm(db, provider, cap=1.0, max_items=2)
    assert result == 2
    assert provider.calls == 2


def test_provider_error_degrades_to_heuristic(db):
    result = rescore_with_llm(db, FailingProvider(), cap=1.0, max_items=10)
    # When the provider raises, _llm_rescore_one catches it and returns heuristic
    assert result == 4  # all 4 targets processed
    scored = db.execute(
        "SELECT ref_type, ref_id, llm_score, heuristic_score FROM intent_scores"
        " WHERE llm_score IS NOT NULL ORDER BY scored_at"
    ).fetchall()
    for row in scored:
        # llm_score equals heuristic_score because the failure path returns heuristic
        assert row["llm_score"] == row["heuristic_score"]
