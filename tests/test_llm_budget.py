"""Budget ledger tests: estimates, monthly accumulation, hard cap behavior."""

import pytest

from signal_engine.llm.budget import (
    BudgetExceeded,
    CallCost,
    estimate_cost,
    month_key,
    record_spend,
    spent_this_month,
)
from signal_engine.db import connect, migrate


@pytest.fixture()
def db(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    return conn


def test_estimate_cost_uses_list_prices():
    haiku = estimate_cost("claude-haiku-4-5-20251001", 1_000_000, 1_000_000)
    assert haiku.cost_usd == pytest.approx(1.0 + 5.0)
    sonnet = estimate_cost("claude-sonnet-5", 1_000_000, 1_000_000)
    assert sonnet.cost_usd == pytest.approx(2.0 + 10.0)


def test_estimate_cost_unknown_model_fails_safe():
    cost = estimate_cost("brand-new-mystery-model", 1_000_000, 1_000_000)
    assert cost.cost_usd == pytest.approx(2.0 + 10.0)  # uses Sonnet pricing


def test_month_key_format():
    assert len(month_key()) == 7
    assert month_key().count("-") == 1


def test_record_spend_accumulates_within_month(db):
    record_spend(db, CallCost("claude-sonnet-5", 1000, 500, 0.007))
    record_spend(db, CallCost("claude-sonnet-5", 2000, 1000, 0.014))
    assert spent_this_month(db) == pytest.approx(0.021, abs=1e-6)


def test_spent_starts_zero(db):
    assert spent_this_month(db) == 0.0


def test_log_ring_buffer_caps_at_100(db):
    for i in range(105):
        record_spend(db, CallCost("claude-sonnet-5", 10, 10, 0.0001))
    row = db.execute("SELECT value FROM settings WHERE key = ?", (f"llm_log:{month_key()}",)).fetchone()
    import json
    entries = json.loads(row["value"])
    assert len(entries) == 100
    assert entries[-1]["in"] == 10  # most recent survived
