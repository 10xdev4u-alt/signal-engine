"""Parse Reddit's public Atom feeds into typed entries."""

from __future__ import annotations

import feedparser

from signal_engine.sources.base import (
    CommentEntry,
    FeedParseError,
    PostEntry,
    strip_html,
)


def _text(value) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def parse_post_feed(xml_text: str) -> tuple[str, list[PostEntry]]:
    """Returns (subreddit, posts). Subreddit comes from the feed category."""
    fp = feedparser.parse(xml_text)
    if fp.bozo and not fp.entries:
        raise FeedParseError(f"unparseable post feed: {fp.bozo_exception}")
    subreddit = ""
    for cat in fp.feed.get("tags", []):
        term = cat.get("term")
        if term:
            subreddit = str(term)
            break
    posts: list[PostEntry] = []
    for e in fp.entries:
        if not str(e.get("id", "")).startswith("t3_"):
            continue
        content = e.get("content")
        raw_html = content[0].value if content else e.get("summary", "")
        body = strip_html(raw_html)
        # link posts carry only an attribution footer; keep them empty-bodied
        lowered = body.lower()
        if "submitted by" in lowered and "[link]" in lowered and len(body) < 300:
            body = ""
        posts.append(
            PostEntry(
                id=str(e.id),
                subreddit=subreddit,
                title=_text(e.get("title")) or "",
                author=_text(e.get("author")),
                selftext=body,
                permalink=str(e.get("link") or ""),
                created_utc=str(e.get("published") or e.get("updated") or ""),
            )
        )
    return subreddit, posts


def parse_comment_feed(xml_text: str, subreddit: str, post_id: str) -> list[CommentEntry]:
    """First entry is the submission itself; the rest are its comments."""
    fp = feedparser.parse(xml_text)
    if fp.bozo and not fp.entries:
        raise FeedParseError(f"unparseable comment feed: {fp.bozo_exception}")
    comments: list[CommentEntry] = []
    for e in fp.entries:
        eid = str(e.get("id", ""))
        if not eid.startswith("t1_"):
            continue
        content = e.get("content")
        body = strip_html(content[0].value if content else e.get("summary", ""))
        comments.append(
            CommentEntry(
                id=eid,
                post_id=post_id,
                subreddit=subreddit,
                author=_text(e.get("author")),
                body=body,
                permalink=str(e.get("link") or ""),
                created_utc=str(e.get("published") or e.get("updated") or ""),
            )
        )
    return comments
