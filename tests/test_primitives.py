"""Tests for core primitives: items, budgets, contexts, tasks."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.budget import Budget, BudgetUnit, item_cost
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task


def make_item(name: str, length: int = 3, content: str = "abcd") -> Item:
    return Item(id=ItemId(name), content=content, length=length)


def test_item_rejects_negative_length() -> None:
    with pytest.raises(ValueError):
        Item(id=ItemId("x"), content="c", length=-1)


def test_budget_rejects_non_positive_limit() -> None:
    with pytest.raises(ValueError):
        Budget(0)
    with pytest.raises(ValueError):
        Budget(-5, BudgetUnit.TOKENS)


def test_item_cost_per_unit() -> None:
    item = make_item("a", length=7, content="hello")
    assert item_cost(item, BudgetUnit.ITEMS) == 1
    assert item_cost(item, BudgetUnit.TOKENS) == 7
    assert item_cost(item, BudgetUnit.CHARACTERS) == 5


def test_budget_admits() -> None:
    budget = Budget(10, BudgetUnit.TOKENS)
    assert budget.admits(used=4, additional=6)
    assert not budget.admits(used=4, additional=7)


def test_context_within_budget() -> None:
    budget = Budget(2, BudgetUnit.ITEMS)
    ctx = Context(items=(make_item("a"), make_item("b")), budget=budget)
    assert len(ctx) == 2
    assert ctx.total_cost == 2
    assert not ctx.is_over_budget
    assert ctx.item_ids == {ItemId("a"), ItemId("b")}


def test_context_rejects_overflow_by_default() -> None:
    budget = Budget(1, BudgetUnit.ITEMS)
    with pytest.raises(ValueError):
        Context(items=(make_item("a"), make_item("b")), budget=budget)


def test_context_allows_explicit_overflow() -> None:
    budget = Budget(1, BudgetUnit.ITEMS)
    ctx = Context(
        items=(make_item("a"), make_item("b")),
        budget=budget,
        allow_overflow=True,
    )
    assert ctx.is_over_budget


def test_task_defaults() -> None:
    task = Task(query="what is the target?")
    assert task.query == "what is the target?"
    assert dict(task.payload) == {}
