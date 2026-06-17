"""Hybrid retention: combine salience, frequency, and recency.

A deployable policy that does not reduce to any single signal. It min-max
normalizes salience, frequency, and recency across the items in memory, then keeps
the items with the highest weighted sum. The default weights favor salience, then
frequency, then recency. Blending signals lets it temper any one of them — for
example down-weighting recurring-but-low-salience harm that frequency alone would
keep — but whether the blend beats the best single signal is an empirical
question the experiments measure, not a guarantee. Ties break by item id.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import FREQUENCY_KEY, RetentionResult
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import salience_of
from context_engineering_lab.retention._common import normalize, retain_by_score

#: Default blend weights for (salience, frequency, recency).
DEFAULT_WEIGHTS: tuple[float, float, float] = (0.5, 0.3, 0.2)


def _frequency(item: Item) -> float:
    value = item.metadata.get(FREQUENCY_KEY, 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _recency(item: Item) -> float:
    return item.timestamp if item.timestamp is not None else 0.0


class HybridRetentionPolicy:
    """Keep items by a normalized blend of salience, frequency, and recency."""

    def __init__(
        self, weights: tuple[float, float, float] = DEFAULT_WEIGHTS
    ) -> None:
        if any(w < 0 for w in weights):
            raise ValueError("weights must be non-negative")
        if sum(weights) <= 0:
            raise ValueError("weights must not all be zero")
        self._weights = weights

    @property
    def weights(self) -> tuple[float, float, float]:
        """The (salience, frequency, recency) blend weights."""
        return self._weights

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the policy."""
        w_s, w_f, w_r = self._weights
        return StrategyId(f"hybrid-retention-{w_s:g}-{w_f:g}-{w_r:g}")

    def retain(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> RetentionResult:
        """Keep highest-blended-score items within the budget."""
        salience = normalize([salience_of(item, 0.0) for item in items])
        frequency = normalize([_frequency(item) for item in items])
        recency = normalize([_recency(item) for item in items])
        w_s, w_f, w_r = self._weights
        scores: dict[ItemId, float] = {
            item.id: w_s * salience[i] + w_f * frequency[i] + w_r * recency[i]
            for i, item in enumerate(items)
        }
        return retain_by_score(
            str(self.id), items, budget, lambda item: scores[item.id]
        )
