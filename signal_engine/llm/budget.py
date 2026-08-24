"""Hard monthly LLM spend cap. Jobs that exhaust the budget skip and report."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

# Published list prices per million tokens as of 2026-08 (USD).
# Kept here so the ledger works even when the user has zero LLM calls.
_PRICES = {
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-fable-5": (10.0, 50.0),
    "gemini-3.6-flash": (1.5, 7.5),
    "gemini-2.5-flash": (0.3, 2.5),
    "gemini-2.5-flash-lite": (0.1, 0.4),
    "kimi-k3": (3.0, 15.0),
}


@dataclass(frozen=True)
class CallCost:
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> CallCost:
    """Rough cost using published list price; the ledger records both tokens and cost."""
    rates = _PRICES.get(model)
    if rates is None:
        # Unknown model: assume mid-tier Sonnet pricing to fail safe toward conservation.
        rates = _PRICES["claude-sonnet-5"]
    in_rate, out_rate = rates
    cost = (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate
    return CallCost(model=model, input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost)


class BudgetExceeded(RuntimeError):
    """Raised when a job would push the monthly spend over the configured cap."""


def month_key() -> str:
    """Returns the current month key in YYYY-MM form."""
    from datetime import datetime, timezone

    return datetime.now(tz=timezone.utc).strftime("%Y-%m")


def spent_this_month(conn: sqlite3.Connection) -> float:
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?", (f"llm_spend:{month_key()}",)
    ).fetchone()
    if row is None:
        return 0.0
    return float(row["value"])


def _load_log(conn: sqlite3.Connection, key: str) -> list[dict]:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None or not row["value"]:
        return []
    try:
        return json.loads(row["value"])
    except json.JSONDecodeError:
        return []


def _save_log(conn: sqlite3.Connection, key: str, entries: list[dict]) -> None:
    """Atomic replace of the log blob (settings has only single-row semantics)."""
    payload = json.dumps(entries[-100:])
    row = conn.execute("SELECT 1 FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?)", (key, payload)
        )
    else:
        conn.execute("UPDATE settings SET value = ? WHERE key = ?", (payload, key))


def record_spend(conn: sqlite3.Connection, cost: CallCost) -> None:
    spend_key = f"llm_spend:{month_key()}"
    current = spent_this_month(conn)
    new_value = f"{current + cost.cost_usd:.6f}"
    row = conn.execute("SELECT 1 FROM settings WHERE key = ?", (spend_key,)).fetchone()
    if row is None:
        conn.execute("INSERT INTO settings(key, value) VALUES (?, ?)", (spend_key, new_value))
    else:
        conn.execute("UPDATE settings SET value = ? WHERE key = ?", (new_value, spend_key))
    log_key = f"llm_log:{month_key()}"
    entries = _load_log(conn, log_key)
    entries.append(
        {
            "model": cost.model,
            "in": cost.input_tokens,
            "out": cost.output_tokens,
            "usd": round(cost.cost_usd, 6),
        }
    )
    _save_log(conn, log_key, entries)
    conn.commit()


def call_within_budget(
    conn: sqlite3.Connection, cost: CallCost, cap: float
) -> bool:
    return spent_this_month(conn) + cost.cost_usd <= cap
