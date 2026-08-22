"""Fetch orchestration: post feeds per subreddit, logged and etag-aware."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from signal_engine.db import get_setting, list_subreddits, set_setting
from signal_engine.ingest.store import upsert_post
from signal_engine.sources.base import posts_url
from signal_engine.sources.polite import CircuitBreakerOpen, PacedClient


@dataclass
class FetchSummary:
    fetched_counts: list[tuple[str, int]] = field(default_factory=list)
    not_modified: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)
    breaker_tripped: str | None = None

    @property
    def fetched(self) -> list[str]:
        return [name for name, _ in self.fetched_counts]

    @property
    def new_posts(self) -> int:
        return sum(count for _, count in self.fetched_counts)


def _log_fetch(
    conn: sqlite3.Connection, url: str, kind: str, status: int | None, size: int
) -> None:
    conn.execute(
        "INSERT INTO fetch_log(url, kind, http_status, bytes) VALUES (?, ?, ?, ?)",
        (url, kind, status, size),
    )
    conn.commit()


def _drain_attempts(
    conn: sqlite3.Connection, client: PacedClient, start: int = 0
) -> None:
    """Persist every raw attempt (incl. 429/403) so error rates stay truthful."""
    for url, status, size in client.attempt_log[start:]:
        _log_fetch(conn, url, "post_feed", status, size)
    del client.attempt_log[start:]


def fetch_subreddits(
    conn: sqlite3.Connection,
    client: PacedClient,
    names: list[str] | None = None,
    now_fn: Callable[[], float] | None = None,
    min_poll_interval: float = 900.0,
) -> FetchSummary:
    """Pull new-post feeds for the given (or all active) subreddits.

    Skips a subreddit entirely when it was polled recently and answered
    304 Not Modified last time — zero requests when nothing can be new.
    """
    summary = FetchSummary()
    clock = now_fn or time.time
    targets = names or [s["name"] for s in list_subreddits(conn)]
    from signal_engine.sources.rss import parse_post_feed

    for name in targets:
        url = posts_url(name)
        last_poll_key = f"last_poll:{name}"
        last_304_key = f"last_was_304:{name}"
        last_poll = get_setting(conn, last_poll_key)
        if (
            last_poll
            and get_setting(conn, last_304_key) == "1"
            and clock() - float(last_poll) < min_poll_interval
        ):
            summary.skipped.append(name)
            continue
        headers: dict[str, str] = {}
        etag = get_setting(conn, f"etag:{name}")
        if etag:
            headers["If-None-Match"] = etag
        try:
            seen = len(client.attempt_log)
            response = client.get(url, extra_headers=headers or None)
        except CircuitBreakerOpen as exc:
            _drain_attempts(conn, client)
            summary.breaker_tripped = str(exc)
            break
        _drain_attempts(conn, client, start=seen)
        set_setting(conn, last_poll_key, repr(clock()))
        if response.status_code == 304:
            set_setting(conn, last_304_key, "1")
            summary.not_modified.append(name)
            continue
        set_setting(conn, last_304_key, "0")
        if response.status_code != 200:
            summary.errors.append((name, f"HTTP {response.status_code}"))
            continue
        try:
            _, posts = parse_post_feed(response.text)
        except Exception as exc:  # noqa: BLE001 - surfaced as an error row
            summary.errors.append((name, f"parse: {exc}"))
            continue
        count = sum(1 for p in posts if upsert_post(conn, p))
        set_setting(conn, f"etag:{name}", response.headers.get("etag") or "")
        set_setting(conn, f"last_fetch_ok:{name}", repr(clock()))
        summary.fetched_counts.append((stored_subreddit(posts, name), count))
    return summary


def stored_subreddit(posts: list, fallback: str) -> str:
    """Posts already carry their feed's category; fall back to requested name."""
    return posts[0].subreddit if posts else fallback
