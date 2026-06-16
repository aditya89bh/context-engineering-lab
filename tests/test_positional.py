"""Tests for the positional selection baselines."""

from __future__ import annotations

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies.positional import (
    FirstNSelection,
    LastNSelection,
)


def items(*names: str) -> list[Item]:
    return [Item(id=ItemId(n), content=n, length=1) for n in names]


def test_first_n_ids() -> None:
    assert FirstNSelection().id == StrategyId("first-n")


def test_first_n_keeps_earliest() -> None:
    ctx = FirstNSelection().select(
        items("a", "b", "c"), Task(query="q"), Budget(2, BudgetUnit.ITEMS)
    )
    assert [str(i.id) for i in ctx.items] == ["a", "b"]


def test_last_n_keeps_latest() -> None:
    ctx = LastNSelection().select(
        items("a", "b", "c"), Task(query="q"), Budget(2, BudgetUnit.ITEMS)
    )
    assert [str(i.id) for i in ctx.items] == ["c", "b"]


def test_positional_respects_budget() -> None:
    ctx = LastNSelection().select(
        items("a", "b", "c"), Task(query="q"), Budget(1, BudgetUnit.ITEMS)
    )
    assert [str(i.id) for i in ctx.items] == ["c"]
