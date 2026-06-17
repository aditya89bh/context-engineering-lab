"""Oracle attention allocation: a ceiling, not a deployable allocator.

``OracleAllocation`` cheats. It weights each source by the *true* number of signal
items it holds, read from the privileged relevance marker the benchmark writes
into item metadata, and apportions capacity-aware so it never wastes budget. No
real allocator knows where the signal is before looking, so this is **not
deployable**. It exists solely as an upper bound: the best a budget split could do
on a benchmark that exposes the ground-truth signal per source. Compare real
allocators *against* it to see how much headroom remains; never ship it.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.attention._common import allocate_by_weights
from context_engineering_lab.core.attention import AllocationResult, Source
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY


def _signal_count(source: Source) -> float:
    return float(
        sum(
            1
            for item in source.items
            if bool(item.metadata.get(ORACLE_RELEVANCE_KEY, False))
        )
    )


class OracleAllocation:
    """Weight sources by true signal count (upper bound only)."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the allocator."""
        return StrategyId("oracle-allocation")

    def allocate(
        self,
        sources: Sequence[Source],
        task: Task,
        budget: Budget,
    ) -> AllocationResult:
        """Weight each source by its ground-truth signal count."""
        weights = [_signal_count(source) for source in sources]
        return allocate_by_weights(
            str(self.id), sources, weights, budget, capacity_aware=True
        )
