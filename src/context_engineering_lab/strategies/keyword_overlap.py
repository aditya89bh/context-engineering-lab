"""Keyword-overlap selection.

A simple content-aware salience baseline: score each candidate by the number of
distinct query terms it contains, then select the highest-scoring candidates that
fit the budget. Ties are broken deterministically by item id so the strategy is
reproducible. This is the simplest stand-in for "relevance" and a useful contrast
to the content-blind positional and recency baselines.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.strategies._budget_fill import fill_within_budget

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall(text.lower()))


class KeywordOverlapSelection:
    """Select candidates by query-term overlap, highest overlap first."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId("keyword-overlap")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Rank candidates by query-term overlap, then fill within budget.

        Args:
            candidates: Items available for selection.
            task: Supplies the query whose terms define overlap.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context of the highest-overlap items that fit, ties broken by id.
        """
        query_terms = _tokens(task.query)

        def overlap(item: Item) -> int:
            return len(query_terms & _tokens(item.content))

        ordered = sorted(
            candidates,
            key=lambda item: (-overlap(item), str(item.id)),
        )
        return fill_within_budget(ordered, budget)
