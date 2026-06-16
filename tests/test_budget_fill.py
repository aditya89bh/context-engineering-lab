"""Tests for the shared budget-fill helper."""

from __future__ import annotations

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.strategies._budget_fill import fill_within_budget


def item(name: str, length: int = 1) -> Item:
    return Item(id=ItemId(name), content=name, length=length)


def test_fills_in_order_until_budget_exhausted() -> None:
    ordered = [item("a"), item("b"), item("c")]
    ctx = fill_within_budget(ordered, Budget(2, BudgetUnit.ITEMS))
    assert [str(i.id) for i in ctx.items] == ["a", "b"]


def test_skips_items_that_do_not_fit_but_keeps_later_smaller_items() -> None:
    ordered = [item("big", length=5), item("small", length=1)]
    ctx = fill_within_budget(ordered, Budget(2, BudgetUnit.TOKENS))
    assert [str(i.id) for i in ctx.items] == ["small"]
    assert not ctx.is_over_budget
