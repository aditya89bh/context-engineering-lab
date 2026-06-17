"""Oracle retention: a ceiling, not a deployable policy.

``OracleRetentionPolicy`` cheats. It reads the privileged relevance marker a
benchmark writes into item metadata and keeps the ground-truth useful items
first, breaking ties by observable salience. No real memory has access to
ground-truth utility at retention time, so this policy is **not deployable**. It
exists solely as an upper bound: the best any policy could do on a benchmark that
exposes which items are useful. Compare real policies *against* it to see how much
headroom remains; never ship it.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import RetentionResult
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import salience_of
from context_engineering_lab.retention._common import retain_by_score
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY


def _score(item: Item) -> float:
    useful = 1.0 if bool(item.metadata.get(ORACLE_RELEVANCE_KEY, False)) else 0.0
    # Useful items (>= 1.0) always outrank non-useful (<= 0.5); salience breaks
    # ties within each group.
    return useful + 0.5 * salience_of(item, 0.0)


class OracleRetentionPolicy:
    """Keep ground-truth useful items first (upper bound only)."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the policy."""
        return StrategyId("oracle-retention")

    def retain(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> RetentionResult:
        """Keep useful-flagged items first, then fill within the budget."""
        return retain_by_score(str(self.id), items, budget, _score)
