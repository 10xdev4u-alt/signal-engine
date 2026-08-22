"""SQLite connection factory, migration runner, subreddit registry."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply unapplied migrations in filename order; returns names applied."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS _migrations("
        "name TEXT PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')))"
    )
    applied = {row["name"] for row in conn.execute("SELECT name FROM _migrations")}
    ran: list[str] = []
    for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        conn.executescript(path.read_text())
        conn.execute("INSERT INTO _migrations(name) VALUES (?)", (path.name,))
        conn.commit()
        ran.append(path.name)
    return ran


def add_subreddit(conn: sqlite3.Connection, name: str, group: str = "core") -> None:
    conn.execute(
        "INSERT INTO subreddits(name, group_name) VALUES (?, ?) "
        "ON CONFLICT(name) DO UPDATE SET active = 1",
        (name.strip(), group),
    )
    conn.commit()


def deactivate_subreddit(conn: sqlite3.Connection, name: str) -> None:
    conn.execute("UPDATE subreddits SET active = 0 WHERE name = ?", (name,))
    conn.commit()


def list_subreddits(
    conn: sqlite3.Connection, active_only: bool = True, group: str | None = None
) -> list[dict]:
    sql = "SELECT name, group_name, active FROM subreddits"
    clauses, params = [], []
    if active_only:
        clauses.append("active = 1")
    if group:
        clauses.append("group_name = ?")
        params.append(group)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY name"
    return [dict(row) for row in conn.execute(sql, params)]


def get_setting(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
