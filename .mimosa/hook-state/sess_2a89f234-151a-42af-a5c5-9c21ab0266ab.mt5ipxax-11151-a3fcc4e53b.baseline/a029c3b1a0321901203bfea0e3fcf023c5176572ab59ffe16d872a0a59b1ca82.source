"""Ask-pattern detection and heuristic buying-intent scoring (1-5)."""

from __future__ import annotations

import re

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
