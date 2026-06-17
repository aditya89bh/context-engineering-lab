"""Winner-take-most attention allocation.

Concentrates most of the budget on the single highest-quality source and splits
the remainder evenly across the rest. It wins when the signal really is
concentrated in one source, and loses when signal is spread across several — then
it starves the others. It does not look at capacity, so betting the budget on a
small top source wastes it; that rigidity is the point of including it.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.attention._common import allocate_by_weights
from context_engineering_lab.core.attention import AllocationResult, Source
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.task import Task

#: Fraction of the budget steered to the single best source.
CONCENTRATION = 0.7


class WinnerTakeMostAllocation:
    """Steer most of the budget to the top-quality source."""

    def __init__(self, concentration: float = CONCENTRATION) -> None:
        if not 0.0 < concentration <= 1.0:
            raise ValueError("concentration must be in (0, 1]")
        self._concentration = concentration

    @property
    def concentration(self) -> float:
        """Fraction of the budget steered to the winner."""
        return self._concentration

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the allocator."""
        return StrategyId(f"winner-take-most-{self._concentration:g}")

    def allocate(
        self,
        sources: Sequence[Source],
        task: Task,
        budget: Budget,
    ) -> AllocationResult:
        """Give the top-quality source most of the budget; split the rest."""
        n = len(sources)
        if n == 1:
            weights = [1.0]
        else:
            winner = max(range(n), key=lambda i: (sources[i].quality, -i))
            others = (1.0 - self._concentration) / (n - 1)
            weights = [
                self._concentration if i == winner else others for i in range(n)
            ]
        return allocate_by_weights(
            str(self.id), sources, weights, budget, capacity_aware=False
        )
