"""Daily digest: one markdown page answering what hurt and who's asking."""

from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Digest:
    date: str
    md: str
    rising_pains: list = field(default_factory=list)
    new_phrases: list = field(default_factory=list)
    intent_flags: list = field(default_factory=list)


def _day_window(date: str, days: int) -> tuple[str, str]:
    end = dt.date.fromisoformat(date)
    start = end - dt.timedelta(days=days)
    return start.isoformat(), end.isoformat()


def _rising_pains(conn: sqlite3.Connection, date: str) -> list[dict]:
    """Clusters ranked by mentions created in the trailing 24h of `date`."""
    window_start, _ = _day_window(date, 1)
    rows = conn.execute(
        """
        SELECT c.id, c.label, c.mention_count, c.desperation_score,
               SUM(CASE WHEN COALESCE(p.created_utc, cm.created_utc) >= ?
                        THEN 1 ELSE 0 END) AS fresh
        FROM pain_clusters c
        LEFT JOIN cluster_members m ON m.cluster_id = c.id
        LEFT JOIN posts p ON m.ref_type = 'post' AND p.id = m.ref_id
        LEFT JOIN comments cm ON m.ref_type = 'comment' AND cm.id = m.ref_id
        GROUP BY c.id
        ORDER BY fresh DESC, c.desperation_score DESC
        LIMIT 10
        """,
        (window_start,),
    ).fetchall()
    result = []
    for row in rows:
        if not result and row["fresh"] == 0:
            continue  # nothing rose today; skip stale clusters entirely
        quotes = conn.execute(
            "SELECT m.quote, COALESCE(p.permalink, cm.permalink) AS permalink "
            "FROM cluster_members m "
            "LEFT JOIN posts p ON m.ref_type = 'post' AND p.id = m.ref_id "
            "LEFT JOIN comments cm ON m.ref_type = 'comment' AND cm.id = m.ref_id "
            "WHERE m.cluster_id = ? LIMIT 3",
            (row["id"],),
        ).fetchall()
        result.append(
            {
                "label": row["label"],
                "mentions": row["mention_count"],
                "desperation": round(row["desperation_score"], 1),
                "quotes": [dict(q) for q in quotes if q["permalink"]],
            }
        )
    return result


def _new_phrases(conn: sqlite3.Connection, date: str) -> list[dict]:
    """1-2 word phrases with >=3 hits today that never appeared in the prior 14 days."""
    window_start, day_before = _day_window(date, 15)
    rows = conn.execute(
        """
        SELECT phrase, count FROM phrase_stats
        WHERE day = :day AND count >= 3
          AND phrase NOT IN (
              SELECT phrase FROM phrase_stats
              WHERE day >= :start AND day < :day_before
                AND length(phrase) - length(REPLACE(phrase, ' ', '')) <= 1
          )
        ORDER BY count DESC LIMIT 8
        """,
        {"day": date, "start": window_start, "day_before": day_before},
    ).fetchall()
    return [{"phrase": r["phrase"], "count": r["count"]} for r in rows]


def _intent_flags(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT s.ref_type, s.ref_id, COALESCE(s.llm_score, s.heuristic_score) AS score,
               COALESCE(NULLIF(p.title, ''), substr(cm.body, 1, 140)) AS snippet,
               COALESCE(p.permalink, cm.permalink) AS permalink, s.scored_at
        FROM intent_scores s
        LEFT JOIN posts p ON s.ref_type = 'post' AND p.id = s.ref_id
        LEFT JOIN comments cm ON s.ref_type = 'comment' AND cm.id = s.ref_id
        WHERE COALESCE(s.llm_score, s.heuristic_score) >= 4
        ORDER BY s.scored_at DESC LIMIT 25
        """
    ).fetchall()
    return [dict(r) for r in rows]


def build_digest(conn: sqlite3.Connection, date: str | None = None) -> Digest:
    today = dt.date.today().isoformat()
    date = date or today
    rising = _rising_pains(conn, date)
    phrases = _new_phrases(conn, date)
    flags = _intent_flags(conn)

    errors_24h = conn.execute(
        "SELECT COUNT(*) c FROM fetch_log WHERE http_status >= 400 "
        "AND ts >= datetime('now', '-1 day')"
    ).fetchone()["c"]
    breaker = conn.execute(
        "SELECT value FROM settings WHERE key = 'last_breaker'"
    ).fetchone()

    lines: list[str] = [f"# Signal digest — {date}", ""]
    lines += ["## Top rising pains", ""]
    if rising:
        for i, pain in enumerate(rising[:5], 1):
            lines.append(
                f"{i}. **{pain['label']}** — {pain['mentions']} mentions, "
                f"desperation {pain['desperation']}"
            )
            for quote in pain["quotes"]:
                lines.append(f"   > {quote['quote']}")
                lines.append(f"   > [{quote['permalink']}]({quote['permalink']})")
    else:
        lines.append("_Nothing rose in the last 24h — quiet day._")
    lines += ["", "## New phrases (not seen in prior 14 days)", ""]
    lines += [
        f"- `{p['phrase']}` ×{p['count']}" for p in phrases
    ] or ["_No new distinctive phrases._"]
    lines += ["", "## Actively asking (intent 4–5)", ""]
    if flags:
        for flag in flags[:15]:
            lines.append(
                f"- **[{flag['score']}]** {flag['snippet']} — "
                f"[{flag['ref_id']}]({flag['permalink'] or ''})"
            )
    else:
        lines.append("_Nobody is actively asking right now._")
    lines += ["", "## Engine health", ""]
    lines.append(f"- Fetch errors in last 24h: {errors_24h}")
    if breaker:
        lines.append(f"- Last breaker event: {breaker['value']}")

    md = "\n".join(lines)
    conn.execute(
        "INSERT INTO digests(date, md, json) VALUES (?, ?, ?) "
        "ON CONFLICT(date) DO UPDATE SET md = excluded.md, json = excluded.json",
        (date, md, "{}"),
    )
    conn.commit()
    return Digest(date=date, md=md, rising_pains=rising, new_phrases=phrases, intent_flags=flags)


def write_digest_file(digest: Digest, data_dir: str = "data") -> str:
    path = Path(data_dir) / "digests"
    path.mkdir(parents=True, exist_ok=True)
    out = path / f"{digest.date}.md"
    out.write_text(digest.md)
    return str(out)
