"""Idempotent persistence for parsed feed entries."""

from __future__ import annotations

import sqlite3

from signal_engine.sources.base import CommentEntry, PostEntry


def upsert_post(conn: sqlite3.Connection, post: PostEntry) -> bool:
    """True when a new row was inserted, False when an existing one updated."""
    exists = conn.execute("SELECT 1 FROM posts WHERE id = ?", (post.id,)).fetchone()
    if exists:
        conn.execute(
            "UPDATE posts SET title = ?, author = ?, "
            "selftext = CASE WHEN ? = '' THEN selftext ELSE ? END, "
            "permalink = ? WHERE id = ?",
            (post.title, post.author, post.selftext, post.selftext, post.permalink, post.id),
        )
        conn.commit()
        return False
    conn.execute(
        "INSERT INTO posts(id, subreddit, title, author, selftext, permalink, created_utc) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            post.id, post.subreddit, post.title, post.author,
            post.selftext, post.permalink, post.created_utc,
        ),
    )
    conn.commit()
    return True


def upsert_comment(conn: sqlite3.Connection, comment: CommentEntry) -> bool:
    exists = conn.execute("SELECT 1 FROM comments WHERE id = ?", (comment.id,)).fetchone()
    if exists:
        conn.execute(
            "UPDATE comments SET body = ? WHERE id = ?", (comment.body, comment.id)
        )
        conn.commit()
        return False
    conn.execute(
        "INSERT INTO comments(id, post_id, subreddit, author, body, permalink, created_utc) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            comment.id, comment.post_id, comment.subreddit, comment.author,
            comment.body, comment.permalink, comment.created_utc,
        ),
    )
    conn.commit()
    return True
