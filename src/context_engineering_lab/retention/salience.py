"""Salience retention: keep the most salient items.

Keeps items with the highest observable salience score (metadata key
``salience``). On this benchmark salience is the signal most aligned with
usefulness — harmful items tend to be low-salience — so a salience policy is
expected to forget harm well, though it can still keep stale-but-salient items.
Ties break by item id.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import RetentionResult
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import salience_of
from context_engineering_lab.retention._common import retain_by_score


class SalienceRetentionPolicy:
    """Keep the highest-salience items that fit the memory budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the policy."""
        return StrategyId("salience-retention")

    def retain(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> RetentionResult:
        """Keep highest-salience-first within the budget."""
        return retain_by_score(
            str(self.id), items, budget, lambda item: salience_of(item, 0.0)
        )
