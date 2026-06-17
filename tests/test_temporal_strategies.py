"""Tests for the temporal selection strategies."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY
from context_engineering_lab.strategies.temporal import (
    AgeWeightedSelection,
    FixedWindowSelection,
    OldestFirstSelection,
    OracleTemporalSelection,
    SlidingWindowSelection,
)

TASK = Task(query="retrieve")


def item(t: int, **meta: object) -> Item:
    return Item(id=ItemId(f"t{t}"), content=f"e{t}", length=1, timestamp=float(t),
                metadata=meta)  # type: ignore[arg-type]


def line(n: int = 10) -> list[Item]:
    return [item(t) for t in range(n)]


def budget(limit: int) -> Budget:
    return Budget(limit, BudgetUnit.ITEMS)


def ids(ctx: object) -> set[str]:
    return {str(i.id) for i in ctx.items}  # type: ignore[attr-defined]


def test_oldest_first_picks_oldest() -> None:
    ctx = OldestFirstSelection().select(line(), TASK, budget(2))
    assert ids(ctx) == {"t0", "t1"}


def test_oldest_first_orders_oldest_to_newest() -> None:
    ctx = OldestFirstSelection().select(line(), TASK, budget(3))
    assert [str(i.id) for i in ctx.items] == ["t0", "t1", "t2"]


def test_sliding_window_keeps_recent_window_only() -> None:
    strat = SlidingWindowSelection(window=3)
    ctx = strat.select(line(), TASK, budget(5))
    assert ids(ctx) == {"t7", "t8", "t9"}
    assert [str(i.id) for i in ctx.items] == ["t9", "t8", "t7"]


def test_fixed_window_keeps_leading_window_only() -> None:
    strat = FixedWindowSelection(window=3)
    ctx = strat.select(line(), TASK, budget(5))
    assert ids(ctx) == {"t0", "t1", "t2"}


def test_window_strategies_reject_bad_window() -> None:
    with pytest.raises(ValueError):
        SlidingWindowSelection(window=0)
    with pytest.raises(ValueError):
        FixedWindowSelection(window=0)


def test_window_ids_encode_size() -> None:
    assert str(SlidingWindowSelection(7).id) == "sliding-window-7"
    assert str(FixedWindowSelection(4).id) == "fixed-window-4"


def test_age_weighted_prefers_salient_old_over_fresh_dull() -> None:
    items = [
        item(2, salience=1.0),
        item(9, salience=0.05),
    ]
    ctx = AgeWeightedSelection(half_life=8.0).select(items, TASK, budget(1))
    assert ids(ctx) == {"t2"}


def test_age_weighted_reduces_to_recency_with_uniform_salience() -> None:
    ctx = AgeWeightedSelection().select(line(), TASK, budget(1))
    assert ids(ctx) == {"t9"}


def test_age_weighted_rejects_bad_half_life() -> None:
    with pytest.raises(ValueError):
        AgeWeightedSelection(half_life=0.0)


def test_oracle_temporal_picks_relevant_first() -> None:
    items = [
        item(0, **{ORACLE_RELEVANCE_KEY: True}),
        item(8, **{ORACLE_RELEVANCE_KEY: False}),
        item(9, **{ORACLE_RELEVANCE_KEY: False}),
    ]
    ctx = OracleTemporalSelection().select(items, TASK, budget(1))
    assert ids(ctx) == {"t0"}


def test_oracle_temporal_breaks_ties_by_recency() -> None:
    items = [
        item(1, **{ORACLE_RELEVANCE_KEY: True}),
        item(7, **{ORACLE_RELEVANCE_KEY: True}),
    ]
    ctx = OracleTemporalSelection().select(items, TASK, budget(1))
    assert ids(ctx) == {"t7"}


def test_strategies_respect_budget() -> None:
    for strat in (
        OldestFirstSelection(),
        SlidingWindowSelection(),
        FixedWindowSelection(),
        AgeWeightedSelection(),
        OracleTemporalSelection(),
    ):
        ctx = strat.select(line(), TASK, budget(2))
        assert len(ctx) <= 2
        assert not ctx.is_over_budget
