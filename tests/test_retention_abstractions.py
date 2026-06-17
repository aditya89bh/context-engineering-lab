"""Tests for the retention abstractions and the policy/strategy adapter."""

from __future__ import annotations

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import (
    PolicyStrategy,
    RetentionDecision,
    RetentionResult,
    RetentionStats,
)
from context_engineering_lab.core.task import Task
from context_engineering_lab.retention import RecencyRetentionPolicy, RetainAllPolicy


def _items(n: int) -> tuple[Item, ...]:
    return tuple(
        Item(id=ItemId(f"i{k}"), content="x", length=1, timestamp=float(k))
        for k in range(n)
    )


def test_stats_memory_budget_utilization() -> None:
    stats = RetentionStats("p", considered=10, retained=4, forgotten=6, budget_limit=8)
    assert stats.memory_budget_utilization == 0.5


def test_stats_utilization_zero_budget_is_zero() -> None:
    stats = RetentionStats("p", considered=1, retained=1, forgotten=0, budget_limit=0)
    assert stats.memory_budget_utilization == 0.0


def test_result_retained_and_forgotten_ids() -> None:
    decisions = (
        RetentionDecision(ItemId("a"), retained=True, score=1.0),
        RetentionDecision(ItemId("b"), retained=False, score=0.0),
    )
    result = RetentionResult(
        context=Context(items=(), budget=Budget(2, BudgetUnit.ITEMS)),
        decisions=decisions,
        stats=RetentionStats("p", 2, 1, 1, 2),
    )
    assert result.retained_ids == frozenset({ItemId("a")})
    assert result.forgotten_ids == frozenset({ItemId("b")})


def test_policy_strategy_id_passthrough() -> None:
    adapter = PolicyStrategy(RecencyRetentionPolicy())
    assert str(adapter.id) == "recency-retention"
    assert isinstance(adapter.policy, RecencyRetentionPolicy)


def test_policy_strategy_select_matches_retain_context() -> None:
    policy = RecencyRetentionPolicy()
    adapter = PolicyStrategy(policy)
    items = _items(5)
    task = Task(query="q")
    budget = Budget(2, BudgetUnit.ITEMS)
    selected = adapter.select(items, task, budget)
    retained = policy.retain(items, task, budget).context
    assert selected.item_ids == retained.item_ids


def test_retain_all_decisions_cover_every_item() -> None:
    items = _items(4)
    budget = Budget(2, BudgetUnit.ITEMS)
    result = RetainAllPolicy().retain(items, Task(query="q"), budget)
    assert len(result.decisions) == 4
    assert result.retained_ids == {item.id for item in items}
    assert result.stats.forgotten == 0
