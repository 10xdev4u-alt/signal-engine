"""Feed entry types and the only boundary that knows Reddit wire formats."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Protocol

from bs4 import BeautifulSoup


class FeedParseError(Exception):
    """Raised when a feed cannot be parsed at all (not merely empty)."""


@dataclass(frozen=True)
class PostEntry:
    id: str
    subreddit: str
    title: str
    author: str | None
    selftext: str  # plain text; link posts arrive empty
    permalink: str
    created_utc: str

    @property
    def is_link_post(self) -> bool:
        return self.selftext == ""


@dataclass(frozen=True)
class CommentEntry:
    id: str
    post_id: str
    subreddit: str
    author: str | None
    body: str  # plain text
    permalink: str
    created_utc: str


class FeedSource(Protocol):
    def posts(self, subreddit: str) -> list[PostEntry]: ...

    def comments(self, post: PostEntry) -> list[CommentEntry]: ...


def strip_html(raw: str) -> str:
    """Reddit wraps body HTML inside an escaped string; unwrap then strip tags."""
    text = html.unescape(raw or "")
    return " ".join(
        BeautifulSoup(text, "html.parser").get_text(separator=" ").split()
    )


def posts_url(subreddit: str) -> str:
    return f"https://www.reddit.com/r/{subreddit}/.rss"


def comments_url(post_permalink: str) -> str:
    return post_permalink.rstrip("/") + "/.rss"
