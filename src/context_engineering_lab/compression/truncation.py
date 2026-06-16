"""Truncation compressors.

The simplest possible compressors: keep a prefix (``head``) or a suffix
(``tail``) of each item's tokens, up to its share of the budget. They read no
content and no query, so they succeed only when the task-relevant tokens happen
to sit at the kept end. They are the lower bounds compression is measured
against.
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


class HeadTruncationCompression:
    """Keep the first ``k`` tokens of each item."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the compressor."""
        return StrategyId("head-truncation")

    def compress(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> CompressionResult:
        """Keep each item's leading tokens within its budget share."""
        budgets = per_item_budgets(budget.limit, len(items))
        kept = [
            tokenize(item.content)[:k]
            for item, k in zip(items, budgets, strict=True)
        ]
        return build_result(str(self.id), items, kept, budget)


class TailTruncationCompression:
    """Keep the last ``k`` tokens of each item."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the compressor."""
        return StrategyId("tail-truncation")

    def compress(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> CompressionResult:
        """Keep each item's trailing tokens within its budget share."""
        budgets = per_item_budgets(budget.limit, len(items))
        kept = [
            tokenize(item.content)[-k:] if k > 0 else []
            for item, k in zip(items, budgets, strict=True)
        ]
        return build_result(str(self.id), items, kept, budget)
