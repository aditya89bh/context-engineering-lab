"""Recency retention: keep the most recent items.

A baseline that forgets by age, keeping the newest items the budget allows. It is
included as a foil, not as the phase's main idea: on this benchmark recent items
are not necessarily useful (harmful items can be recent, useful items can be old),
so recency is expected to retain harm and forget old-but-useful information. Items
without a timestamp are treated as oldest.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import RetentionResult
from context_engineering_lab.core.task import Task
from context_engineering_lab.retention._common import retain_by_score

_OLDEST = float("-inf")


class RecencyRetentionPolicy:
    """Keep the most recent items that fit the memory budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the policy."""
        return StrategyId("recency-retention")

    def retain(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> RetentionResult:
        """Keep newest-first within the budget."""
        return retain_by_score(
            str(self.id),
            items,
            budget,
            lambda item: item.timestamp if item.timestamp is not None else _OLDEST,
        )
