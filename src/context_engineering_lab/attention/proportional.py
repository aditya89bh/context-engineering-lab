"""Size-proportional attention allocation.

Splits the budget in proportion to each source's *size* (item count). It assumes
bigger sources hold more signal — true when sources are uniform-density, but a
trap when a large source is mostly noise. It does not look at source capacity
beyond size, so it spends in proportion to volume regardless of quality.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.attention._common import allocate_by_weights
from context_engineering_lab.core.attention import AllocationResult, Source
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.task import Task


class ProportionalAllocation:
    """Divide the budget in proportion to source size."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the allocator."""
        return StrategyId("proportional-allocation")

    def allocate(
        self,
        sources: Sequence[Source],
        task: Task,
        budget: Budget,
    ) -> AllocationResult:
        """Weight each source by its item count."""
        weights = [float(source.size) for source in sources]
        return allocate_by_weights(
            str(self.id), sources, weights, budget, capacity_aware=False
        )
