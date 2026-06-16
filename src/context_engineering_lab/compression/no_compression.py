"""No-compression baseline.

Returns the content unchanged. It is the reference point that preserves all
information at full cost. Unlike every other strategy in the lab, it does **not**
honor the budget: when the content exceeds the budget it returns an over-budget
context (flagged via ``allow_overflow``). That is the point — it shows what
perfect retention costs, and its ``budget_utilization`` will exceed 1 whenever
compression was actually needed.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.compression._common import build_result, tokenize
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.compression import CompressionResult
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task


class NoCompression:
    """Keep all content; ignore the budget (reference baseline)."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the compressor."""
        return StrategyId("no-compression")

    def compress(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> CompressionResult:
        """Return the items unchanged, permitting budget overflow.

        Args:
            items: Items to (not) compress.
            task: Unused; present for interface conformance.
            budget: The budget; intentionally not enforced.

        Returns:
            A result whose context may exceed the budget.
        """
        kept = [tokenize(item.content) for item in items]
        return build_result(str(self.id), items, kept, budget, allow_overflow=True)
