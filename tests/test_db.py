import re

import pytest

from signal_engine.config import Settings, load_settings
from signal_engine.db import (
    add_subreddit,
    connect,
    deactivate_subreddit,
    get_setting,
    list_subreddits,
    migrate,
    set_setting,
)


def test_migrate_creates_all_tables(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    ran = migrate(conn)
    tables = {
        r["name"]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','trigger')")
    }
    for expected in [
        "subreddits", "fetch_log", "posts", "comments", "phrase_stats",
        "pain_clusters", "cluster_members", "intent_scores", "profiles",
        "eval_marks", "digests", "settings", "search_index",
        "posts_ai_fts", "comments_ai_fts",
    ]:
        assert expected in tables, f"missing {expected}"
    assert ran == ["001_init.sql", "002_fts.sql"]


def test_migrate_is_idempotent(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    counts_before = conn.execute("SELECT COUNT(*) c FROM _migrations").fetchone()["c"]
    rows_before = conn.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
    ran_again = migrate(conn)
    assert ran_again == []
    assert conn.execute("SELECT COUNT(*) c FROM _migrations").fetchone()["c"] == counts_before
    assert conn.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"] == rows_before


def test_fts_index_finds_inserted_post(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    conn.execute(
        "INSERT INTO posts(id, subreddit, title, author, selftext, permalink, created_utc) "
        "VALUES ('t3_x1', 'smallbusiness', 'Chargebacks eating margin', '/u/a', "
        "'Spent $400 on fees this month', 'https://old.reddit.com/r/smallbusiness/comments/x1/', "
        "'2026-08-20T10:00:00Z')"
    )
    conn.commit()
    hits = conn.execute(
        "SELECT ref_id FROM search_index WHERE search_index MATCH 'chargebacks'"
    ).fetchall()
    assert [h["ref_id"] for h in hits] == ["t3_x1"]


def test_subreddit_registry_roundtrip(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    add_subreddit(conn, "teachers", group="discovery")
    add_subreddit(conn, "smallbusiness")  # re-add stays single row, stays active
    subs = list_subreddits(conn)
    assert {s["name"] for s in subs} == {"smallbusiness", "teachers"}
    assert list_subreddits(conn, group="discovery")[0]["name"] == "teachers"
    deactivate_subreddit(conn, "teachers")
    assert all(s["name"] != "teachers" for s in list_subreddits(conn))


def test_settings_mask_secrets():
    fake = "not-a-real-credential-just-a-fixture-value"
    masked = repr(Settings(anthropic_api_key=fake))
    assert fake not in masked
    assert "***" in masked


def test_load_settings_from_env_and_types(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "PACE_SECONDS=\"60\"\n# comment\nPORT=8000\n"
        "ANTHROPIC_API_KEY=fixture-value-not-real\n"
    )
    s = load_settings(dotenv_path=env_file)
    assert s.pace_seconds == 60.0
    assert s.port == 8000
    assert s.anthropic_api_key == "fixture-value-not-real"
    assert s.has_llm


def test_process_environment_beats_dotenv(tmp_path):
    from signal_engine.config import load_settings

    env_file = tmp_path / ".env"
    env_file.write_text("PACE_SECONDS=60\n")
    s = load_settings(
        dotenv_path=env_file, environ={"PACE_SECONDS": "90", "DB_PATH": "/x/t.db"}
    )
    assert s.pace_seconds == 90.0  # process env wins over the file
    assert s.db_path == "/x/t.db"


def test_settings_repr_is_valid_dataclass_shape():
    assert re.match(r"^Settings\(", repr(Settings()))


@pytest.mark.parametrize(
    "key,val",
    [("etag:smallbusiness", 'W/"abc"'), ("llm_spend_month", "1.5")],
)
def test_settings_kv_roundtrip(tmp_path, key, val):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    set_setting(conn, key, val)
    assert get_setting(conn, key) == val
