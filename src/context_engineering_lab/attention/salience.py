"""Salience-proportional attention allocation.

Splits the budget in proportion to each source's *mean observable salience*. When
salience tracks signal this concentrates budget well, but salience can be gamed: a
noisy source whose distractors carry inflated salience will attract budget it does
not deserve. It reads only the observable salience signal, never ground truth.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.attention._common import allocate_by_weights
from context_engineering_lab.core.attention import AllocationResult, Source
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.task import Task


class SalienceAllocation:
    """Divide the budget in proportion to mean source salience."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the allocator."""
        return StrategyId("salience-allocation")

    def allocate(
        self,
        sources: Sequence[Source],
        task: Task,
        budget: Budget,
    ) -> AllocationResult:
        """Weight each source by the mean salience of its items."""
        weights = [source.mean_salience for source in sources]
        return allocate_by_weights(
            str(self.id), sources, weights, budget, capacity_aware=False
        )
