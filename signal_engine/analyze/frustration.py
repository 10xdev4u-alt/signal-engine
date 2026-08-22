"""Frustration lexicon scoring, 0-3."""

from __future__ import annotations

from pathlib import Path

_LEXICON_PATH = Path(__file__).parent.parent / "data" / "frustration_lexicon.txt"
PHRASES: tuple[str, ...] = tuple(
    line for line in _LEXICON_PATH.read_text().splitlines() if line.strip()
)


def frustration_hits(text: str) -> list[str]:
    lowered = " " + " ".join(text.lower().split()) + " "
    return [phrase for phrase in PHRASES if phrase in lowered]


def frustration_level(text: str) -> int:
    """0 = none, 1 = one marker, 2 = a few, 3 = wall of despair."""
    hits = len(frustration_hits(text))
    if hits == 0:
        return 0
    if hits == 1:
        return 1
    if hits <= 3:
        return 2
    return 3
