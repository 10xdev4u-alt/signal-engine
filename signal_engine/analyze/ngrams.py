"""Deterministic signal extraction over collected posts and comments."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
STOPWORDS: frozenset[str] = frozenset(
    line for line in (_DATA / "stopwords.txt").read_text().splitlines() if line
)
_TOKEN_RE = re.compile(r"[a-z0-9']{2,}")


def tokenize(text: str) -> list[str]:
    return [_stem(t) for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


def _stem(token: str) -> str:
    """Fold simple plurals so chargeback/chargebacks land together."""
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def ngrams(tokens: list[str], size: int) -> list[tuple[str, ...]]:
    if len(tokens) < size:
        return []
    return [tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)]


def build_phrase_stats(conn) -> int:
    """Rebuild phrase_stats (1-3 grams per subreddit/day). Returns rows written."""
    counts: Counter = Counter()
    rows = conn.execute(
        "SELECT subreddit, title, selftext, created_utc FROM posts"
    ).fetchall()
    for row in rows:
        day = str(row["created_utc"])[:10]
        tokens = tokenize(f"{row['title']} {row['selftext']}")
        for size in (1, 2, 3):
            for gram in ngrams(tokens, size):
                counts[(row["subreddit"], day, " ".join(gram))] += 1
    for row in conn.execute("SELECT subreddit, body, created_utc FROM comments"):
        day = str(row["created_utc"])[:10]
        for size in (1, 2, 3):
            for gram in ngrams(tokenize(row["body"]), size):
                counts[(row["subreddit"], day, " ".join(gram))] += 1

    conn.execute("DELETE FROM phrase_stats")
    conn.executemany(
        "INSERT INTO phrase_stats(subreddit, phrase, day, count) VALUES (?, ?, ?, ?)",
        [(sub, phrase, day, n) for (sub, day, phrase), n in sorted(counts.items())],
    )
    conn.commit()
    return len(counts)
