"""Adaptive attention allocation.

Weights sources by their observable *quality* score and, unlike the fixed
allocators, reacts to capacity: it never hands a source more budget than it can
fill, redistributing the slack to the next-best sources. Quality is a (noisy)
proxy for signal density that resists the salience trap, and the capacity-aware
redistribution avoids wasting budget on small high-quality sources. It is the
strongest *deployable* allocator here — but it reads only observable signals, so
it still falls short of the oracle when quality is an imperfect proxy.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.attention._common import allocate_by_weights
from context_engineering_lab.core.attention import AllocationResult, Source
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.task import Task


class AdaptiveAllocation:
    """Weight sources by observable quality, redistributing unfillable budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the allocator."""
        return StrategyId("adaptive-allocation")

    def allocate(
        self,
        sources: Sequence[Source],
        task: Task,
        budget: Budget,
    ) -> AllocationResult:
        """Weight each source by quality and apportion capacity-aware."""
        weights = [source.quality for source in sources]
        return allocate_by_weights(
            str(self.id), sources, weights, budget, capacity_aware=True
        )
