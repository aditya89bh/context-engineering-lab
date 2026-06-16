"""Oracle selection: a ceiling, not a deployable strategy.

``OracleSelection`` cheats. It reads a privileged relevance marker that a
benchmark writes into item metadata and selects flagged items first. No real
system has access to ground-truth relevance at selection time, so this strategy
is **not deployable**. It exists solely as an upper bound: the best any selector
could do on a benchmark that exposes which items are relevant. Compare real
strategies *against* the oracle to see how much headroom remains, never ship it.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies._budget_fill import fill_within_budget

#: Metadata key a benchmark sets to ``True`` on items that are ground-truth
#: relevant. Only the oracle is permitted to read it.
ORACLE_RELEVANCE_KEY = "oracle_relevant"


def _is_relevant(item: Item) -> bool:
    return bool(item.metadata.get(ORACLE_RELEVANCE_KEY, False))


class OracleSelection:
    """Select ground-truth relevant items first (upper bound only)."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId("oracle")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Order relevant-flagged items first, then fill within budget.

        Args:
            candidates: Items available for selection. Relevant items are
                identified by the :data:`ORACLE_RELEVANCE_KEY` metadata flag.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context that includes as many relevant items as the budget allows,
            before any irrelevant items.
        """
        ordered = sorted(candidates, key=lambda item: 0 if _is_relevant(item) else 1)
        return fill_within_budget(ordered, budget)
