"""Daily digest: one markdown page answering what hurt and who's asking."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

_RISING = (
    "SELECT c.id, c.label, c.mention_count, c.desperation_score,"
    " SUM(CASE WHEN COALESCE(p.created_utc, cm.created_utc) >= ?"
    " AND COALESCE(p.created_utc, cm.created_utc) < ? THEN 1 ELSE 0 END) AS fresh"
    " FROM pain_clusters c"
    " JOIN cluster_members m ON m.cluster_id = c.id"
    " LEFT JOIN posts p ON m.ref_type = 'post' AND p.id = m.ref_id"
    " LEFT JOIN comments cm ON m.ref_type = 'comment' AND cm.id = m.ref_id"
    " GROUP BY c.id HAVING fresh > 0"
    " ORDER BY fresh DESC, c.desperation_score DESC LIMIT 10"
)
_QUOTES = (
    "SELECT m.quote, COALESCE(p.permalink, cm.permalink) AS permalink"
    " FROM cluster_members m"
    " LEFT JOIN posts p ON m.ref_type = 'post' AND p.id = m.ref_id"
    " LEFT JOIN comments cm ON m.ref_type = 'comment' AND cm.id = m.ref_id"
    " WHERE m.cluster_id = ? AND COALESCE(p.permalink, cm.permalink) IS NOT NULL LIMIT 3"
)
_PHRASES = (
    "SELECT phrase, count FROM phrase_stats WHERE day = ? AND count >= 3"
    " AND length(phrase) - length(REPLACE(phrase, ' ', '')) <= 1"
    " AND phrase NOT IN (SELECT phrase FROM phrase_stats WHERE day >= ? AND day < ?)"
    " ORDER BY count DESC LIMIT 8"
)
_FLAGS_ANY = (
    "SELECT s.ref_type, s.ref_id, COALESCE(s.llm_score, s.heuristic_score) AS score,"
    " COALESCE(NULLIF(p.title, ''), substr(cm.body, 1, 140)) AS snippet,"
    " COALESCE(p.permalink, cm.permalink) AS permalink, s.scored_at"
    " FROM intent_scores s"
    " LEFT JOIN posts p ON s.ref_type = 'post' AND p.id = s.ref_id"
    " LEFT JOIN comments cm ON s.ref_type = 'comment' AND cm.id = s.ref_id"
    " WHERE COALESCE(s.llm_score, s.heuristic_score) >= 4"
    " AND COALESCE(p.permalink, cm.permalink) IS NOT NULL"
    " ORDER BY s.scored_at DESC LIMIT 25"
)
_FLAGS_UNTIL = (
    "SELECT s.ref_type, s.ref_id, COALESCE(s.llm_score, s.heuristic_score) AS score,"
    " COALESCE(NULLIF(p.title, ''), substr(cm.body, 1, 140)) AS snippet,"
    " COALESCE(p.permalink, cm.permalink) AS permalink, s.scored_at"
    " FROM intent_scores s"
    " LEFT JOIN posts p ON s.ref_type = 'post' AND p.id = s.ref_id"
    " LEFT JOIN comments cm ON s.ref_type = 'comment' AND cm.id = s.ref_id"
    " WHERE COALESCE(s.llm_score, s.heuristic_score) >= 4"
    " AND COALESCE(p.created_utc, cm.created_utc) < ?"
    " AND COALESCE(p.permalink, cm.permalink) IS NOT NULL"
    " ORDER BY s.scored_at DESC LIMIT 25"
)
_ERROR_COUNT = (
    "SELECT COUNT(*) AS c FROM fetch_log WHERE http_status >= 400"
    " AND ts >= datetime('now', '-1 day')"
)
_BREAKER = "SELECT value FROM settings WHERE key = 'last_breaker'"
_UPSERT_DIGEST = (
    "INSERT INTO digests(date, md, json) VALUES (?, ?, ?)"
    " ON CONFLICT(date) DO UPDATE SET md = excluded.md, json = excluded.json"
)


@dataclass
class Digest:
    date: str
    md: str
    rising_pains: list = field(default_factory=list)
    new_phrases: list = field(default_factory=list)
    intent_flags: list = field(default_factory=list)


def _next_day(date: str) -> str:
    return (dt.date.fromisoformat(date) + dt.timedelta(days=1)).isoformat()


def _rising_pains(conn: sqlite3.Connection, date: str) -> list[dict]:
    """Clusters with mentions created on `date` (UTC day bounds), ranked."""
    day_end = _next_day(date)
    rising_params = (date, day_end)
    result = []
    for row in conn.execute(_RISING, rising_params):
        cluster_id = row["id"]
        quotes = [dict(q) for q in conn.execute(_QUOTES, (cluster_id,))]
        result.append(
            {
                "label": row["label"],
                "mentions": row["mention_count"],
                "desperation": round(row["desperation_score"], 1),
                "quotes": quotes,
            }
        )
    return result


def _new_phrases(conn: sqlite3.Connection, date: str) -> list[dict]:
    """1-2 word phrases with >=3 hits today absent from the prior 14 days."""
    window_start = (dt.date.fromisoformat(date) - dt.timedelta(days=14)).isoformat()
    phrase_params = (date, window_start, date)
    rows = conn.execute(_PHRASES, phrase_params)
    return [{"phrase": r["phrase"], "count": r["count"]} for r in rows]


def _intent_flags(conn: sqlite3.Connection, date: str | None = None) -> list[dict]:
    """Score-4+ items; when `date` is given, only items created before it."""
    if date is None:
        rows = conn.execute(_FLAGS_ANY)
    else:
        created_before = _next_day(date)
        until_params = (created_before,)
        rows = conn.execute(_FLAGS_UNTIL, until_params)
    return [dict(r) for r in rows]


def build_digest(conn: sqlite3.Connection, date: str | None = None) -> Digest:
    today = dt.date.today().isoformat()
    date = date or today
    rising = _rising_pains(conn, date)
    phrases = _new_phrases(conn, date)
    flags = _intent_flags(conn, date=date)

    error_counts = conn.execute(_ERROR_COUNT)
    errors_24h = error_counts.fetchone()["c"]
    breaker_rows = conn.execute(_BREAKER)
    breaker_row = breaker_rows.fetchone()

    lines: list[str] = ["# Signal digest — " + date, "", "## Top rising pains", ""]
    if rising:
        for i, pain in enumerate(rising[:5], 1):
            lines.append(
                f"{i}. **{pain['label']}** — {pain['mentions']} mentions,"
                f" desperation {pain['desperation']}"
            )
            for quote in pain["quotes"]:
                link = quote["permalink"]
                lines.append("   > " + quote["quote"])
                lines.append(f"   > [{link}]({link})")
    else:
        lines.append("_Nothing rose on this day — quiet day._")
    lines += ["", "## New phrases (not seen in prior 14 days)", ""]
    lines += [f"- `{p['phrase']}` ×{p['count']}" for p in phrases] or [
        "_No new distinctive phrases._"
    ]
    lines += ["", "## Actively asking (intent 4–5)", ""]
    if flags:
        for flag in flags[:15]:
            link = flag["permalink"] or ""
            snippet = flag["snippet"]
            ref = flag["ref_id"]
            lines.append(f"- **[{flag['score']}]** {snippet} — [{ref}]({link})")
    else:
        lines.append("_Nobody is actively asking right now._")
    lines += ["", "## Engine health", ""]
    lines.append(f"- Fetch errors in last 24h: {errors_24h}")
    if breaker_row is not None and breaker_row["value"]:
        lines.append("- Last breaker event: " + breaker_row["value"])

    md = "\n".join(lines)
    payload = json.dumps(
        {
            "rising_pains": rising,
            "new_phrases": phrases,
            "intent_flags": flags,
            "errors_24h": errors_24h,
        }
    )
    digest_params = (date, md, payload)
    conn.execute(_UPSERT_DIGEST, digest_params)
    conn.commit()
    return Digest(
        date=date, md=md, rising_pains=rising, new_phrases=phrases, intent_flags=flags
    )


def write_digest_file(digest: Digest, data_dir: str = "data") -> str:
    path = Path(data_dir) / "digests"
    path.mkdir(parents=True, exist_ok=True)
    out = path / (digest.date + ".md")
    out.write_text(digest.md, encoding="utf-8")
    return str(out)
