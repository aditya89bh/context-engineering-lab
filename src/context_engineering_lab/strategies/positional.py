"""Positional selection baselines.

Two order-only baselines that ignore content entirely: ``FirstNSelection`` keeps
the earliest candidates, ``LastNSelection`` keeps the latest. They are useful
lower bounds and probes for *position bias*: if a benchmark places its target
early or late, these baselines reveal that simple position heuristics can score
well for the wrong reason.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies._budget_fill import fill_within_budget


class FirstNSelection:
    """Select candidates in input order until the budget is exhausted."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId("first-n")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Admit candidates from the front of the sequence within budget.

        Args:
            candidates: Items available for selection.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context of the earliest items that fit.
        """
        return fill_within_budget(candidates, budget)


class LastNSelection:
    """Select candidates from the end of the input within the budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId("last-n")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Admit candidates from the back of the sequence within budget.

        The returned context is ordered latest-first.

        Args:
            candidates: Items available for selection.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context of the latest items that fit.
        """
        return fill_within_budget(reversed(candidates), budget)
