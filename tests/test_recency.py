"""Tests for the recency selection baseline."""

from __future__ import annotations

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies.recency import RecencySelection


def item(name: str, timestamp: float | None, length: int = 1) -> Item:
    return Item(id=ItemId(name), content=name, length=length, timestamp=timestamp)


def test_id() -> None:
    assert RecencySelection().id == StrategyId("recency")


def test_selects_most_recent_within_item_budget() -> None:
    candidates = [item("old", 1.0), item("mid", 2.0), item("new", 3.0)]
    ctx = RecencySelection().select(
        candidates, Task(query="q"), Budget(2, BudgetUnit.ITEMS)
    )
    assert [str(i.id) for i in ctx.items] == ["new", "mid"]
    assert not ctx.is_over_budget


def test_respects_token_budget() -> None:
    candidates = [item("a", 1.0, length=3), item("b", 2.0, length=3)]
    ctx = RecencySelection().select(
        candidates, Task(query="q"), Budget(3, BudgetUnit.TOKENS)
    )
    assert [str(i.id) for i in ctx.items] == ["b"]
    assert ctx.total_cost == 3


def test_items_without_timestamp_are_oldest() -> None:
    candidates = [item("no_ts", None), item("ts", 5.0)]
    ctx = RecencySelection().select(
        candidates, Task(query="q"), Budget(1, BudgetUnit.ITEMS)
    )
    assert [str(i.id) for i in ctx.items] == ["ts"]
