"""Tests for the deterministic random selection baseline."""

from __future__ import annotations

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies.random_selection import RandomSelection


def items(count: int) -> list[Item]:
    return [Item(id=ItemId(f"i{n}"), content=str(n), length=1) for n in range(count)]


def test_id() -> None:
    assert RandomSelection().id == StrategyId("random")


def test_respects_budget() -> None:
    ctx = RandomSelection(seed=1).select(
        items(10), Task(query="q"), Budget(3, BudgetUnit.ITEMS)
    )
    assert len(ctx.items) == 3
    assert not ctx.is_over_budget


def test_is_deterministic_for_same_candidates() -> None:
    candidates = items(10)
    budget = Budget(4, BudgetUnit.ITEMS)
    first = RandomSelection(seed=7).select(candidates, Task(query="q"), budget)
    second = RandomSelection(seed=7).select(candidates, Task(query="q"), budget)
    assert [str(i.id) for i in first.items] == [str(i.id) for i in second.items]


def test_different_seeds_can_differ() -> None:
    candidates = items(12)
    budget = Budget(4, BudgetUnit.ITEMS)
    a = RandomSelection(seed=1).select(candidates, Task(query="q"), budget)
    b = RandomSelection(seed=2).select(candidates, Task(query="q"), budget)
    assert {str(i.id) for i in a.items} != {str(i.id) for i in b.items}
