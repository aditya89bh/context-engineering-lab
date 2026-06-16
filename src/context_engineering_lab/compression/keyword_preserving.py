"""Keyword-preserving compression.

A query-aware extractive compressor. It prioritizes tokens that appear in the
task query, then fills any remaining budget with the earliest remaining tokens,
preserving original order. It reads only the query (not the ground-truth fact
markers), so it is deployable: it preserves required facts well when the query
names them, but cannot recognize optional facts the query omits or tell a
distractor apart from filler.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.compression._common import (
    build_result,
    per_item_budgets,
    tokenize,
)
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.compression import CompressionResult
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task


def _keep_keywords(tokens: list[str], query_terms: frozenset[str], k: int) -> list[str]:
    ranked = sorted(
        range(len(tokens)),
        key=lambda i: (0 if tokens[i] in query_terms else 1, i),
    )
    kept_indices = sorted(ranked[:k])
    return [tokens[i] for i in kept_indices]


class KeywordPreservingCompression:
    """Keep query-matching tokens first, then earliest remaining tokens."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the compressor."""
        return StrategyId("keyword-preserving")

    def compress(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> CompressionResult:
        """Keep tokens by query overlap within each item's budget share."""
        query_terms = frozenset(task.query.split())
        budgets = per_item_budgets(budget.limit, len(items))
        kept = [
            _keep_keywords(tokenize(item.content), query_terms, k)
            for item, k in zip(items, budgets, strict=True)
        ]
        return build_result(str(self.id), items, kept, budget)
