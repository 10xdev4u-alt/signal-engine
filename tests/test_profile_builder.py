"""Profile builder tests: deterministic core, budget-gated LLM, dated log."""

from __future__ import annotations

import pytest

from signal_engine.analyze.profile import (
    ProfileBuildResult,
    build_all_active,
    build_profile,
)
from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.llm import budget as budget_mod
from signal_engine.llm.base import NullProvider
from signal_engine.llm.budget import CallCost, record_spend


class StubProvider:
    """Configurable LLM stub for testing the narrative path without network."""

    name = "stub"
    model = "claude-haiku-4-5-20251001"

    def __init__(self, body: str = "stubbed narrative text"):
        self.body = body
        self.calls = 0

    def complete(self, system: str, user: str, max_tokens: int = 400) -> str:
        self.calls += 1
        return self.body


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    return conn


def _seed_posts(conn):
    import datetime as dt

    from signal_engine.ingest.store import upsert_post
    from signal_engine.sources.base import PostEntry

    today = dt.date.today()
    posts = [
        PostEntry(
            id="t3_p1", subreddit="smallbusiness",
            title="How do I stop chargebacks destroying my margin?",
            author="/u/a", selftext="spent $400 on fees this month",
            permalink="https://old.reddit.com/r/smallbusiness/comments/p1/",
            created_utc=f"{today.isoformat()}T10:00:00+00:00",
        ),
        PostEntry(
            id="t3_p2", subreddit="smallbusiness", title="Chargebacks destroying my margin again",
            author="/u/b", selftext="third this month, banks never side with us",
            permalink="https://old.reddit.com/r/smallbusiness/comments/p2/",
            created_utc=f"{today.isoformat()}T11:00:00+00:00",
        ),
        PostEntry(
            id="t3_p3", subreddit="smallbusiness", title="Tried Google Ads for my Etsy store",
            author="/u/c", selftext="zero conversions in two weeks, wasted money",
            permalink="https://old.reddit.com/r/smallbusiness/comments/p3/",
            created_utc=f"{(today - dt.timedelta(days=10)).isoformat()}T09:00:00+00:00",
        ),
    ]
    for entry in posts:
        upsert_post(conn, entry)


def test_deterministic_section_renders_with_data(db):
    _seed_posts(db)
    result = build_profile(db, "smallbusiness")
    assert isinstance(result, ProfileBuildResult)
    assert result.subreddit == "smallbusiness"
    assert result.llm_calls == 0
    md = db.execute(
        "SELECT snapshot_md FROM profiles ORDER BY generated_at DESC LIMIT 1"
    ).fetchone()["snapshot_md"]
    assert "# r/smallbusiness" in md
    assert "## Deterministic profile" in md
    assert "Posts this week: 2" in md
    assert "tried" in md.lower()  # frustration lexicon hit on "tried"/"wasted"
    assert "chargeback" in md
    assert "## Update log" in md
    assert "initial snapshot" in md


def test_idempotent_rerun_appends_to_update_log(db):
    _seed_posts(db)
    build_profile(db, "smallbusiness")
    build_profile(db, "smallbusiness")
    rows = list(db.execute("SELECT snapshot_md FROM profiles ORDER BY generated_at"))
    assert len(rows) == 2
    latest_log = rows[-1]["snapshot_md"].split("\n## Update log\n", 1)[1]
    # Each dated run contributes one log line; all are dated so the filter keeps them.
    dated_lines = [line for line in latest_log.splitlines() if line.startswith("- 2")]
    assert len(dated_lines) == 2
    assert "initial snapshot" in dated_lines[0]
    assert "lines added" in dated_lines[1]


def test_null_provider_path_is_deterministic_only(db):
    _seed_posts(db)
    result = build_profile(db, "smallbusiness", provider=NullProvider())
    assert result.llm_calls == 0
    assert result.sections_written == []
    md = db.execute(
        "SELECT snapshot_md FROM profiles ORDER BY generated_at DESC LIMIT 1"
    ).fetchone()["snapshot_md"]
    assert "## LLM narrative" not in md


def test_real_provider_calls_are_budget_capped(db, monkeypatch):
    _seed_posts(db)
    # Pre-load the ledger so the first call passes but the third would breach
    cheap = CallCost(
        model="claude-haiku-4-5-20251001", input_tokens=1, output_tokens=1, cost_usd=0.000001
    )
    for _ in range(8):
        record_spend(db, cheap)
    provider = StubProvider(
        body="Observed in r/smallbusiness: 'chargeback destroying margin' recurring."
    )
    result = build_profile(db, "smallbusiness", provider=provider, monthly_cap=0.0001)
    # Budget is below the cost of a single call, so no LLM sections are written
    assert result.llm_calls == 0
    md = db.execute(
        "SELECT snapshot_md FROM profiles ORDER BY generated_at DESC LIMIT 1"
    ).fetchone()["snapshot_md"]
    assert "## LLM narrative" not in md


def test_stub_provider_writes_narrative_and_records_spend(db):
    _seed_posts(db)
    provider = StubProvider(
        body=(
            "Observed in r/smallbusiness: 'chargeback destroying margin' "
            "and 'tried dispute template'."
        )
    )
    result = build_profile(db, "smallbusiness", provider=provider, monthly_cap=1.0)
    # StubProvider returns a non-LLM-error body for all 3 sections within budget
    assert result.llm_calls == 3
    assert "demographics" in result.sections_written
    assert "language" in result.sections_written
    assert "tone" in result.sections_written
    md = db.execute(
        "SELECT snapshot_md FROM profiles ORDER BY generated_at DESC LIMIT 1"
    ).fetchone()["snapshot_md"]
    assert "## LLM narrative" in md
    assert "## Demographics" in md
    assert "## Language" in md
    assert "## Tone" in md
    # ledger now non-zero
    spent_row = db.execute(
        "SELECT value FROM settings WHERE key = ?", (f"llm_spend:{budget_mod.month_key()}",)
    ).fetchone()
    assert spent_row is not None
    assert float(spent_row["value"]) > 0


def test_build_all_active_iterates_active_subs(db):
    _seed_posts(db)
    add_subreddit(db, "teachers")
    results = build_all_active(db)
    subs = {r.subreddit for r in results}
    assert subs == {"smallbusiness", "teachers"}


def test_profile_last_run_setting_recorded(db):
    _seed_posts(db)
    build_profile(db, "smallbusiness")
    row = db.execute("SELECT value FROM settings WHERE key = 'profile_last_run'").fetchone()
    assert row is not None
    assert "T" in row["value"]  # ISO timestamp with T separator
