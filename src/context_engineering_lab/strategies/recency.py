"""Recency selection: the trivial baseline.

Selects the most recent items (by timestamp) that fit within the budget. Items
without a timestamp are treated as oldest. This baseline exists only to exercise
the harness and to serve as a reference point for future strategies (see
``docs/benchmarks.md`` on baselines); it makes no research claim.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies._budget_fill import fill_within_budget

_OLDEST = float("-inf")


class RecencySelection:
    """Greedily select the most recent items that fit the budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId("recency")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Select newest-first until the budget cannot admit the next item.

        Args:
            candidates: Items available for selection.
            task: Unused by this baseline; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context of the most recent items that fit within the budget,
            preserved in newest-to-oldest order.
        """
        ordered = sorted(
            candidates,
            key=lambda item: item.timestamp if item.timestamp is not None else _OLDEST,
            reverse=True,
        )
        return fill_within_budget(ordered, budget)
