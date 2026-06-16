"""Random selection baseline.

Selects a random subset of candidates that fits the budget. Randomness is
*content-addressed*: the per-call seed is derived from the strategy's base seed
and the ids of the candidates, so the same candidates always yield the same
selection regardless of when or where the strategy runs. This keeps experiments
reproducible while still giving a genuine random reference point.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.seeding import DEFAULT_SEED, derive_seed
from context_engineering_lab.strategies._budget_fill import fill_within_budget


class RandomSelection:
    """Select a deterministic-but-arbitrary subset within the budget.

    Args:
        seed: Base seed for the content-addressed per-call randomness.
    """

    def __init__(self, seed: int = DEFAULT_SEED) -> None:
        self._seed = seed

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId("random")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Shuffle candidates deterministically, then fill within budget.

        Args:
            candidates: Items available for selection.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context of a reproducible random subset that fits.
        """
        fingerprint = "|".join(str(item.id) for item in candidates)
        rng = random.Random(derive_seed(self._seed, "random-selection", fingerprint))
        shuffled = list(candidates)
        rng.shuffle(shuffled)
        return fill_within_budget(shuffled, budget)
