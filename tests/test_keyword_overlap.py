"""Tests for keyword-overlap selection."""

from __future__ import annotations

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection


def item(name: str, content: str) -> Item:
    return Item(id=ItemId(name), content=content, length=1)


def test_id() -> None:
    assert KeywordOverlapSelection().id == StrategyId("keyword-overlap")


def test_prefers_higher_overlap() -> None:
    candidates = [
        item("none", "completely unrelated text"),
        item("some", "the alpha signal"),
        item("most", "alpha beta gamma signal"),
    ]
    ctx = KeywordOverlapSelection().select(
        candidates,
        Task(query="alpha beta gamma signal"),
        Budget(1, BudgetUnit.ITEMS),
    )
    assert [str(i.id) for i in ctx.items] == ["most"]


def test_tie_break_is_deterministic_by_id() -> None:
    candidates = [
        item("b", "alpha signal"),
        item("a", "alpha signal"),
    ]
    ctx = KeywordOverlapSelection().select(
        candidates, Task(query="alpha signal"), Budget(1, BudgetUnit.ITEMS)
    )
    assert [str(i.id) for i in ctx.items] == ["a"]


def test_respects_budget() -> None:
    candidates = [
        item("a", "alpha"),
        item("b", "alpha"),
        item("c", "alpha"),
    ]
    ctx = KeywordOverlapSelection().select(
        candidates, Task(query="alpha"), Budget(2, BudgetUnit.ITEMS)
    )
    assert len(ctx.items) == 2
