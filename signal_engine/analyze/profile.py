"""Profile builder: deterministic stats + budget-gated LLM narrative.

Built per ADR-0003: deterministic core always works, LLM is additive and
budget-capped. Renders a dated markdown snapshot per subreddit.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from dataclasses import dataclass, field

from signal_engine.llm.base import NullProvider, Provider
from signal_engine.llm.budget import (
    call_within_budget,
    estimate_cost,
    record_spend,
    spent_this_month,
)

_SELECT_TOP_PHRASES = (
    "SELECT phrase, SUM(count) AS total FROM phrase_stats"
    " WHERE subreddit = ? GROUP BY phrase ORDER BY total DESC LIMIT ?"
)
_SELECT_POSTS_HOURS = "SELECT created_utc AS t FROM posts WHERE subreddit = ?"
_SELECT_COMMENTS_HOURS = "SELECT created_utc AS t FROM comments WHERE subreddit = ?"
_SELECT_TOP_THREADS = (
    "SELECT id, title, permalink FROM posts WHERE subreddit = ?"
    " ORDER BY length(COALESCE(selftext, '')) DESC LIMIT ?"
)
_SELECT_POSTS_BODIES = (
    "SELECT selftext FROM posts WHERE subreddit = ? AND selftext != ''"
)
_SELECT_WEEK_POSTS = (
    "SELECT COUNT(*) c FROM posts WHERE subreddit = ? AND created_utc >= ?"
)
_SELECT_WEEK_COMMENTS = (
    "SELECT COUNT(*) c FROM comments WHERE subreddit = ? AND created_utc >= ?"
)
_SELECT_PREV_POSTS = (
    "SELECT COUNT(*) c FROM posts WHERE subreddit = ?"
    " AND created_utc >= ? AND created_utc < ?"
)
_SELECT_LATEST_PROFILE = (
    "SELECT snapshot_md, generated_at FROM profiles"
    " WHERE subreddit = ? ORDER BY generated_at DESC LIMIT 1"
)
_SELECT_ACTIVE_SUBS = "SELECT name FROM subreddits WHERE active = 1 ORDER BY name"
_INSERT_PROFILE = "INSERT INTO profiles(subreddit, snapshot_md) VALUES (?, ?)"
_UPDATE_SETTING = (
    "UPDATE settings SET value = ? WHERE key = ?"
)
_SELECT_SETTING = "SELECT value FROM settings WHERE key = ?"
_INSERT_SETTING = "INSERT INTO settings(key, value) VALUES (?, ?)"
_UPDATE_LAST_RUN = (
    "UPDATE settings SET value = ? WHERE key = 'profile_last_run'"
)

_TRIED_PATTERN = __import__("re").compile(
    r"\b(tried|stopped using|used to|wasted|burned by)\b", __import__("re").IGNORECASE
)


@dataclass
class ProfileBuildResult:
    subreddit: str
    llm_calls: int
    sections_written: list[str] = field(default_factory=list)
    diff_summary: str = "initial snapshot"


def _hour_buckets(hours: list[int]) -> str:
    if not hours:
        return "_no data yet_"
    return ", ".join(f"{h:02d}:00" for h in hours)


def _top_threads_md(threads: list[dict]) -> str:
    if not threads:
        return "_no threads with body text yet_"
    return "\n".join(f"- [{t['title']}]({t['permalink']})" for t in threads)


def _deterministic_sections(conn: sqlite3.Connection, subreddit: str) -> str:
    phrases_rows = list(conn.execute(_SELECT_TOP_PHRASES, (subreddit, 15)))
    phrases = [r["phrase"] for r in phrases_rows]
    counts: dict[int, int] = {}
    for sql in (_SELECT_POSTS_HOURS, _SELECT_COMMENTS_HOURS):
        for row in conn.execute(sql, (subreddit,)):
            try:
                h = dt.datetime.fromisoformat(
                    row["t"].replace("Z", "+00:00")
                ).hour
                counts[h] = counts.get(h, 0) + 1
            except ValueError:
                continue
    hours = sorted(counts, key=counts.get, reverse=True)[:8]
    threads_rows = list(conn.execute(_SELECT_TOP_THREADS, (subreddit, 5)))
    threads = [dict(r) for r in threads_rows]
    tried = sum(
        1
        for r in conn.execute(_SELECT_POSTS_BODIES, (subreddit,))
        if _TRIED_PATTERN.search(r["selftext"])
    )
    week_ago = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=7)).isoformat()
    fortnight_ago = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=14)).isoformat()
    posts_this = conn.execute(
        _SELECT_WEEK_POSTS, (subreddit, week_ago)
    ).fetchone()["c"]
    posts_prev = conn.execute(
        _SELECT_PREV_POSTS, (subreddit, fortnight_ago, week_ago)
    ).fetchone()["c"]
    comments_this = conn.execute(
        _SELECT_WEEK_COMMENTS, (subreddit, week_ago)
    ).fetchone()["c"]
    parts = [
        "## Deterministic profile",
        "",
        f"- Posts this week: {posts_this} (prior week: {posts_prev})",
        f"- Comments this week: {comments_this}",
        f"- Posts with 'tried X' or 'stopped using' markers: {tried}",
        f"- Most active hours (UTC): {_hour_buckets(hours)}",
        "",
        "### Most distinctive phrases",
        "",
    ]
    parts.extend(f"- `{p}`" for p in phrases) if phrases else parts.append(
        "_not enough data yet_"
    )
    parts.append("")
    parts.append("### Top threads by body length")
    parts.append("")
    parts.append(_top_threads_md(threads))
    parts.append("")
    return "\n".join(parts)


_LLM_SECTIONS = (
    (
        "demographics",
        "Inferred demographics and what people here are afraid of. "
        "Quote a specific phrase from the input. Mark every inference with `(inferred)`.",
    ),
    (
        "language",
        "The community's exact language for problem, solution, and tried-and-failed. "
        "Quote three phrases verbatim.",
    ),
    (
        "tone",
        "How the community writes: post length, formality, humor, opening patterns. "
        "Two or three sentences grounded in what you saw.",
    ),
)


def _llm_section(
    provider: Provider,
    section: str,
    instruction: str,
    context: str,
    max_tokens: int = 400,
) -> str | None:
    system = (
        "You write community-profile sections for a research tool. "
        "Every claim must quote a specific phrase from the input. "
        "If the input is too thin, say so instead of inventing. "
        "No marketing language. No exclamation marks."
    )
    user = f"Section: {section}\n\nInstructions: {instruction}\n\nContext:\n{context}"
    body = provider.complete(system, user, max_tokens=max_tokens).strip()
    if not body or body.startswith("_(LLM"):
        return None
    return body


def _diff_note(previous_md: str, new_md: str) -> str:
    if not previous_md:
        return "initial snapshot"
    prev = set(previous_md.splitlines())
    new = set(new_md.splitlines())
    return f"lines added: {len(new - prev)}, lines removed: {len(prev - new)}"


def _record_run_at(conn: sqlite3.Connection, ts: str) -> None:
    if conn.execute(_SELECT_SETTING, ("profile_last_run",)).fetchone() is None:
        conn.execute(_INSERT_SETTING, ("profile_last_run", ts))
    else:
        conn.execute(_UPDATE_LAST_RUN, (ts,))


def build_profile(
    conn: sqlite3.Connection,
    subreddit: str,
    provider: Provider | None = None,
    monthly_cap: float = 1.0,
) -> ProfileBuildResult:
    """Render and persist a profile snapshot for `subreddit`."""
    deterministic = _deterministic_sections(conn, subreddit)
    phrases_rows = list(
        conn.execute(_SELECT_TOP_PHRASES, (subreddit, 15))
    )
    phrases = [r["phrase"] for r in phrases_rows]
    threads_rows = list(
        conn.execute(_SELECT_TOP_THREADS, (subreddit, 5))
    )
    threads = [dict(r) for r in threads_rows]
    context = (
        f"PHRASES={json.dumps(phrases)}\n"
        f"TOP_THREADS={json.dumps([t['title'] for t in threads])}\n"
    )
    llm_calls = 0
    sections_written: list[str] = []
    llm_sections_md: list[str] = []
    if provider is not None and not isinstance(provider, NullProvider):
        if spent_this_month(conn) < monthly_cap:
            for name, instruction in _LLM_SECTIONS:
                cost = estimate_cost(provider.model, 600, 400)
                if not call_within_budget(conn, cost, monthly_cap):
                    break
                body = _llm_section(provider, name, instruction, context)
                if body is not None:
                    record_spend(conn, cost)
                    llm_sections_md.append(f"### {name.title()}\n\n{body}\n")
                    sections_written.append(name)
                llm_calls += 1
                if llm_calls >= 3:
                    break
    previous_row = conn.execute(_SELECT_LATEST_PROFILE, (subreddit,)).fetchone()
    previous_md = previous_row["snapshot_md"] if previous_row else ""
    today = dt.date.today().isoformat()
    diff = _diff_note(previous_md, deterministic)
    log_line = (
        f"- {today}: {diff}"
        + (f", LLM sections: {', '.join(sections_written)}" if sections_written else "")
    )
    body_parts: list[str] = [
        f"# r/{subreddit}",
        "",
        f"_Snapshot taken {today}._",
        "",
        deterministic,
    ]
    if llm_sections_md:
        body_parts.append("\n## LLM narrative\n")
        body_parts.extend(llm_sections_md)
    body_parts.append("\n## Update log\n")
    # Carry forward dated log lines from the previous snapshot, filtering out
    # the legacy "first snapshot" placeholder so it doesn't accumulate forever.
    if previous_md and "\n## Update log\n" in previous_md:
        history = previous_md.split("\n## Update log\n", 1)[1]
        history_lines = [
            line for line in history.splitlines()
            if line.startswith("- 2")  # only keep ISO-dated log lines
        ]
        history = "\n".join(history_lines) + ("\n" if history_lines else "")
    else:
        history = ""
    body_parts.append(history + log_line + "\n")
    snapshot_md = "\n".join(body_parts)
    conn.execute(_INSERT_PROFILE, (subreddit, snapshot_md))
    _record_run_at(conn, dt.datetime.now(tz=dt.UTC).isoformat())
    conn.commit()
    return ProfileBuildResult(
        subreddit=subreddit,
        llm_calls=llm_calls,
        sections_written=sections_written,
        diff_summary=diff,
    )


def build_all_active(
    conn: sqlite3.Connection,
    provider: Provider | None = None,
    monthly_cap: float = 1.0,
) -> list[ProfileBuildResult]:
    """Build profiles for every active subreddit; one budget, shared."""
    subs = [row["name"] for row in conn.execute(_SELECT_ACTIVE_SUBS)]
    return [
        build_profile(conn, name, provider=provider, monthly_cap=monthly_cap)
        for name in subs
    ]
