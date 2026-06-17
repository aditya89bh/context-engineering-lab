"""Frequency retention: keep the most frequently accessed items.

Keeps items with the highest observable access-frequency count (metadata key
``frequency``). Frequency is a plausible utility proxy, but it is *not* immune to
harm: on this benchmark harmful items can be high-frequency (recurring noise), so
a frequency policy is expected to retain them. Ties break by item id.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import FREQUENCY_KEY, RetentionResult
from context_engineering_lab.core.task import Task
from context_engineering_lab.retention._common import retain_by_score


def _frequency(item: Item) -> float:
    value = item.metadata.get(FREQUENCY_KEY, 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


class FrequencyRetentionPolicy:
    """Keep the highest-frequency items that fit the memory budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the policy."""
        return StrategyId("frequency-retention")

    def retain(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> RetentionResult:
        """Keep highest-frequency-first within the budget."""
        return retain_by_score(str(self.id), items, budget, _frequency)
