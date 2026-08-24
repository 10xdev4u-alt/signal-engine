"""Ask-pattern detection and heuristic buying-intent scoring (1-5)."""

from __future__ import annotations

import re
from datetime import UTC

STRONG_PATTERNS: tuple[tuple[str, str], ...] = (
    ("tool_seek", r"\bwhat (?:tool|app|service|software|platform)\b"),
    ("recommend", r"\brecommend(?:ations?)?\b"),
    ("best_way", r"\bbest way to\b"),
    ("how_do_i_fix", r"\bhow do i (?:fix|stop|get rid of|avoid)\b"),
    ("anyone_know", r"\banyone know\b"),
    ("looking_for_rec", r"\blooking for .{0,30}(?:tool|app|service|recommendation)"),
    ("what_should_i", r"\bwhat should i (?:use|do|buy|get)\b"),
)
MONEY_SEEK_PATTERNS: tuple[tuple[str, str], ...] = (
    ("worth_paying", r"\bworth paying\b"),
    ("would_you_pay", r"\bwould you pay\b"),
    ("pay_someone", r"\bpay (?:someone|a pro|for a service)\b"),
    ("hiring_out", r"\bhiring someone to\b"),
)
QUESTION_STARTERS = ("how ", "what ", "why ", "is there", "does anyone", "has anyone")


def detect_asks(text: str) -> list[str]:
    """Names of matched ask/money patterns, in declaration order."""
    lowered = text.lower()
    return [
        name
        for group in (STRONG_PATTERNS, MONEY_SEEK_PATTERNS)
        for name, pattern in group
        if re.search(pattern, lowered)
    ]


def intent_score(text: str) -> int:
    """Heuristic buying-intent score clamped to 1..5.

    Base 1; +1 question-shaped; +2 strong seek pattern; +1 money-seek.
    """
    stripped = text.strip().lower()
    score = 1
    if stripped.endswith("?") or stripped.startswith(QUESTION_STARTERS):
        score += 1
    asks = set(detect_asks(text))
    if asks & {name for name, _ in STRONG_PATTERNS}:
        score += 2
    if asks & {name for name, _ in MONEY_SEEK_PATTERNS}:
        score += 1
    return min(5, max(1, score))


def record_intent(conn) -> int:
    """Score every post/comment not yet scored. Returns rows written."""
    written = 0
    rows = conn.execute(
        "SELECT id, title, selftext FROM posts WHERE id NOT IN "
        "(SELECT ref_id FROM intent_scores WHERE ref_type = 'post')"
    ).fetchall()
    for row in rows:
        score = intent_score(f"{row['title']} {row['selftext']}")
        if score >= 2:
            conn.execute(
                "INSERT INTO intent_scores(ref_type, ref_id, heuristic_score) "
                "VALUES ('post', ?, ?) ON CONFLICT(ref_type, ref_id) DO UPDATE SET "
                "heuristic_score = excluded.heuristic_score",
                (row["id"], score),
            )
            written += 1
    for row in conn.execute(
        "SELECT id, body FROM comments WHERE id NOT IN "
        "(SELECT ref_id FROM intent_scores WHERE ref_type = 'comment')"
    ):
        score = intent_score(row["body"])
        if score >= 2:
            conn.execute(
                "INSERT INTO intent_scores(ref_type, ref_id, heuristic_score) "
                "VALUES ('comment', ?, ?) ON CONFLICT(ref_type, ref_id) DO UPDATE SET "
                "heuristic_score = excluded.heuristic_score",
                (row["id"], score),
            )
            written += 1
    conn.commit()
    return written


_SELECT_HEURISTIC_HIGH = (
    "SELECT ref_type, ref_id, heuristic_score FROM intent_scores"
    " WHERE heuristic_score >= 3 AND llm_score IS NULL LIMIT ?"
)
_SELECT_POST_TEXT = (
    "SELECT title, selftext FROM posts WHERE id = ?"
)
_SELECT_COMMENT_TEXT = "SELECT body AS title FROM comments WHERE id = ?"
_UPDATE_LLM_SCORE = (
    "UPDATE intent_scores SET llm_score = ?, scored_at = ?"
    " WHERE ref_type = ? AND ref_id = ?"
)

_LLM_RESCORE_SYSTEM = (
    "You score Reddit posts or comments for active buying intent on a 1-5 scale. "
    "Return only the integer 1, 2, 3, 4, or 5. 1 = no intent, 5 = clearly asking "
    "for a recommendation with money on the table."
)
_LLM_RESCORE_USER_TEMPLATE = (
    "Heuristic score from keyword rules: {heuristic}\n\n"
    "Text:\n\"\"\"\n{text}\n\"\"\"\n\n"
    "Return only the integer score."
)


def _llm_rescore_one(provider, text: str, heuristic: int) -> int:
    """Ask the LLM for a 1-5 score; degrade to the heuristic on any error."""
    try:
        body = provider.complete(
            _LLM_RESCORE_SYSTEM,
            _LLM_RESCORE_USER_TEMPLATE.format(heuristic=heuristic, text=text[:1500]),
            max_tokens=8,
        )
        body = body.strip().strip("'\"")
        digits = "".join(ch for ch in body if ch.isdigit())[:1] or "0"
        score = int(digits)
    except (ValueError, Exception):
        return heuristic
    if not 1 <= score <= 5:
        return heuristic
    return score


def rescore_with_llm(conn, provider, cap: float = 1.0, max_items: int = 25) -> int:
    """Re-score intent items that scored 3+ heuristically using the LLM.

    Skipped when the provider is NullProvider or the budget is exhausted.
    Updates `llm_score` so the digest queue can use
    `COALESCE(llm_score, heuristic_score)`. Caps at `max_items` per call
    so cron runs are bounded.
    """
    from datetime import datetime

    from signal_engine.llm.base import NullProvider
    from signal_engine.llm.budget import (
        call_within_budget,
        estimate_cost,
        record_spend,
        spent_this_month,
    )

    if isinstance(provider, NullProvider):
        return 0
    if spent_this_month(conn) >= cap:
        return 0
    targets = list(
        conn.execute(_SELECT_HEURISTIC_HIGH, (max_items,))
    )
    rescored = 0
    now = datetime.now(tz=UTC).isoformat(timespec="seconds")
    for row in targets:
        ref_type = row["ref_type"]
        ref_id = row["ref_id"]
        heuristic = row["heuristic_score"]
        if ref_type == "post":
            text_row = conn.execute(_SELECT_POST_TEXT, (ref_id,)).fetchone()
        else:
            text_row = conn.execute(_SELECT_COMMENT_TEXT, (ref_id,)).fetchone()
        if not text_row:
            continue
        # Posts have title + selftext columns; comments use the `title`
        # alias for body. Use try/except because sqlite3.Row exposes
        # keys() but not the `in` operator we want here.
        is_post = ref_type == "post"
        text = text_row["title"] or ""
        try:
            if is_post and text_row["selftext"]:
                text += text_row["selftext"]
        except (IndexError, KeyError):
            pass
        cost = estimate_cost(provider.model, 200, 5)
        if not call_within_budget(conn, cost, cap):
            break
        score = _llm_rescore_one(provider, text, heuristic)
        record_spend(conn, cost)
        conn.execute(
            _UPDATE_LLM_SCORE, (score, now, ref_type, ref_id)
        )
        rescored += 1
        if rescored >= max_items:
            break
    conn.commit()
    return rescored

