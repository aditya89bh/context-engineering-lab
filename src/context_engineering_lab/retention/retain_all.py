"""Retain-all retention: the reference that never forgets.

``RetainAllPolicy`` keeps every item regardless of the memory budget. Like the
no-compression baseline, it deliberately *ignores* the budget: its produced
context may exceed the limit, so its ``memory_budget_utilization`` exceeds 1
whenever forgetting was actually needed. It is the reference against which
selective forgetting is judged — it shows what keeping everything costs.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import RetentionResult
from context_engineering_lab.core.task import Task
from context_engineering_lab.retention._common import retain_by_score


class RetainAllPolicy:
    """Keep everything; never forget (over-budget reference)."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the policy."""
        return StrategyId("retain-all")

    def retain(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> RetentionResult:
        """Keep every item, permitting the context to exceed the budget."""
        return retain_by_score(
            str(self.id), items, budget, lambda _item: 0.0, keep_all=True
        )
