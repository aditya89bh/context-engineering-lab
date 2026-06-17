"""Uniform attention allocation.

Splits the budget evenly across sources, ignoring their size, quality, and
salience. It is the natural baseline and the one to beat: when sources differ in
how much signal they hold, an even split wastes budget on weak sources and starves
strong ones. It does not look at source capacity, so it can hand a small source
more budget than it can fill.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.attention._common import allocate_by_weights
from context_engineering_lab.core.attention import AllocationResult, Source
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.task import Task


class UniformAllocation:
    """Divide the budget evenly across all sources."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the allocator."""
        return StrategyId("uniform-allocation")

    def allocate(
        self,
        sources: Sequence[Source],
        task: Task,
        budget: Budget,
    ) -> AllocationResult:
        """Assign each source an equal weight."""
        weights = [1.0 for _ in sources]
        return allocate_by_weights(
            str(self.id), sources, weights, budget, capacity_aware=False
        )
