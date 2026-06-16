"""Tests for the oracle ceiling strategy."""

from __future__ import annotations

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies.oracle import (
    ORACLE_RELEVANCE_KEY,
    OracleSelection,
)


def item(name: str, *, relevant: bool) -> Item:
    return Item(
        id=ItemId(name),
        content=name,
        length=1,
        metadata={ORACLE_RELEVANCE_KEY: relevant},
    )


def test_id() -> None:
    assert OracleSelection().id == StrategyId("oracle")


def test_selects_relevant_first_under_tight_budget() -> None:
    candidates = [
        item("d0", relevant=False),
        item("d1", relevant=False),
        item("target", relevant=True),
    ]
    ctx = OracleSelection().select(
        candidates, Task(query="q"), Budget(1, BudgetUnit.ITEMS)
    )
    assert [str(i.id) for i in ctx.items] == ["target"]


def test_is_an_upper_bound_for_recall() -> None:
    candidates = [
        item("t0", relevant=True),
        item("d0", relevant=False),
        item("t1", relevant=True),
        item("d1", relevant=False),
    ]
    ctx = OracleSelection().select(
        candidates, Task(query="q"), Budget(2, BudgetUnit.ITEMS)
    )
    selected = {str(i.id) for i in ctx.items}
    assert selected == {"t0", "t1"}
