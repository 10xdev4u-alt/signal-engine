from pathlib import Path

import pytest

from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.ingest.store import upsert_comment, upsert_post
from signal_engine.sources.base import FeedParseError, comments_url, posts_url
from signal_engine.sources.rss import parse_comment_feed, parse_post_feed

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture()
def db(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    return conn


def test_posts_url_and_comments_url_shapes():
    assert posts_url("smallbusiness") == "https://www.reddit.com/r/smallbusiness/.rss"
    assert (
        comments_url("https://old.reddit.com/r/sub/comments/abc123/title/")
        == "https://old.reddit.com/r/sub/comments/abc123/title/.rss"
    )


def test_parse_post_feed_maps_all_fields():
    subreddit, posts = parse_post_feed((FIX / "post_feed.atom").read_text())
    assert subreddit == "smallbusiness"
    assert len(posts) == 2
    first = posts[0]
    assert first.id == "t3_abc123"
    assert first.title.startswith("How do I stop chargebacks")
    assert first.author == "/u/shopowner_22"
    assert first.permalink.endswith("/comments/abc123/how_do_i_stop_chargebacks/")
    assert "Spent $400" in first.selftext
    assert "<div" not in first.selftext and "&lt;" not in first.selftext
    link_post = posts[1]
    assert link_post.is_link_post and link_post.selftext == ""


def test_parse_comment_feed_skips_submission_entry():
    comments = parse_comment_feed(
        (FIX / "comment_feed.atom").read_text(), "smallbusiness", "t3_abc123"
    )
    assert [c.id for c in comments] == ["t1_cmt001", "t1_cmt002"]
    c1 = comments[0]
    assert c1.post_id == "t3_abc123"
    assert c1.permalink.endswith("/cmt001/")
    assert "Worth paying" in c1.body
    assert "<p>" not in c1.body


def test_malformed_xml_raises_typed_error():
    with pytest.raises(FeedParseError):
        parse_post_feed("<not-xml <<<>>>")
    with pytest.raises(FeedParseError):
        parse_comment_feed("garbage bytes \x00\x01", "x", "t3_x")


def test_double_upsert_is_idempotent(db):
    _, posts = parse_post_feed((FIX / "post_feed.atom").read_text())
    assert upsert_post(db, posts[0]) is True
    assert upsert_post(db, posts[0]) is False
    assert db.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"] == 1
    # FTS index stays consistent: exactly one indexed row for the post
    hits = db.execute(
        "SELECT ref_id FROM search_index WHERE search_index MATCH 'chargebacks'"
    ).fetchall()
    assert len(hits) == 1
    comments = parse_comment_feed(
        (FIX / "comment_feed.atom").read_text(), "smallbusiness", "t3_abc123"
    )
    for c in comments:
        assert upsert_comment(db, c) is True
    assert upsert_comment(db, comments[0]) is False
    assert db.execute("SELECT COUNT(*) c FROM comments").fetchone()["c"] == 2
