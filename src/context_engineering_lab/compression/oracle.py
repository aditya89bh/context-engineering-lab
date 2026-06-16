"""Oracle compression: a ceiling, not a deployable strategy.

``OracleCompression`` cheats. It reads the benchmark's ground-truth fact markers
and keeps only the target facts (required and optional), discarding distractors
and filler entirely, up to the budget. No real compressor knows which tokens are
the facts in advance, so this is **not deployable**. It exists purely as an upper
bound: maximal information retention at minimal size. Compare real compressors
against it to see the remaining headroom; never ship it.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.benchmarks.facts import is_target_fact
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


def _keep_target_facts(tokens: list[str], k: int) -> list[str]:
    target_indices = [i for i, token in enumerate(tokens) if is_target_fact(token)]
    kept_indices = sorted(target_indices[:k])
    return [tokens[i] for i in kept_indices]


class OracleCompression:
    """Keep only ground-truth target facts within the budget (ceiling)."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the compressor."""
        return StrategyId("oracle-compression")

    def compress(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> CompressionResult:
        """Keep target facts first, dropping distractors and filler.

        Args:
            items: Items whose target facts are identified by the benchmark's
                fact markers (see ``benchmarks/facts.py``).
            task: Unused; present for interface conformance.
            budget: The constraint the produced context satisfies.

        Returns:
            A context containing as many target facts as the budget allows and
            nothing else.
        """
        budgets = per_item_budgets(budget.limit, len(items))
        kept = [
            _keep_target_facts(tokenize(item.content), k)
            for item, k in zip(items, budgets, strict=True)
        ]
        return build_result(str(self.id), items, kept, budget)
