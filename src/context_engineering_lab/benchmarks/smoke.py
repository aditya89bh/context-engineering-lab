"""Harness smoke benchmark.

A tiny synthetic needle-in-a-haystack task used ONLY to validate that the lab
can run a reproducible experiment end to end. Each case contains exactly one
target item and several distractors; the task is to retrieve the target, and a
strategy is scored on whether the target survived selection.

This is NOT a research benchmark. It exists to prove the plumbing works, not to
discriminate between strategies. Do not draw conclusions from its numbers.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence

from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId, ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.metrics import (
    answer_support,
    selection_precision,
    selection_recall,
)
from context_engineering_lab.core.task import Task
from context_engineering_lab.seeding import derive_seed

_NUM_CASES = 8
_NUM_DISTRACTORS = 5


class SmokeBenchmark:
    """A deterministic needle-in-a-haystack benchmark for harness validation."""

    @property
    def id(self) -> BenchmarkId:
        """Stable identifier for the benchmark."""
        return BenchmarkId("harness-smoke")

    @property
    def version(self) -> str:
        """Version string; bump when a change affects scores."""
        return "1.0"

    @property
    def declared_metrics(self) -> tuple[str, ...]:
        """Names of the metrics this benchmark reports."""
        return ("answer_support", "selection_recall", "selection_precision")

    @property
    def budget_sweep(self) -> tuple[Budget, ...]:
        """Budgets recommended for sweeping (in items)."""
        return (
            Budget(1, BudgetUnit.ITEMS),
            Budget(2, BudgetUnit.ITEMS),
            Budget(4, BudgetUnit.ITEMS),
        )

    def generate(self, seed: int) -> Sequence[Case]:
        """Generate deterministic cases from a seed.

        Args:
            seed: Root seed; all randomness derives from it.

        Returns:
            A list of cases, each with one target among distractors.
        """
        rng = random.Random(derive_seed(seed, "harness-smoke", self.version))
        cases: list[Case] = []
        for case_index in range(_NUM_CASES):
            target = Item(
                id=ItemId(f"case{case_index}-target"),
                content="the target fact",
                length=1,
                timestamp=rng.uniform(0.0, 100.0),
            )
            items = [target]
            for d in range(_NUM_DISTRACTORS):
                items.append(
                    Item(
                        id=ItemId(f"case{case_index}-distractor{d}"),
                        content="an irrelevant fact",
                        length=1,
                        timestamp=rng.uniform(0.0, 100.0),
                    )
                )
            rng.shuffle(items)
            cases.append(
                Case(
                    case_id=f"case{case_index}",
                    task=Task(query="retrieve the target fact"),
                    candidates=tuple(items),
                    relevant_ids=frozenset({target.id}),
                )
            )
        return cases

    def evaluate(self, case: Case, context: Context) -> Mapping[str, float]:
        """Score a context for a single case.

        Empty-selection convention: the formal
        :func:`~context_engineering_lab.core.metrics.selection_precision` treats
        an empty selection as *undefined* and raises. For harness convenience
        this benchmark records precision as ``0.0`` when nothing is selected, so
        a run never crashes on a degenerate (tiny-budget) selection. This is a
        reporting convenience, not a claim about precision at zero selection.

        Args:
            case: The case that produced the context.
            context: The strategy's output for the case.

        Returns:
            A mapping of declared metric names to values.
        """
        selected = context.item_ids
        precision = (
            selection_precision(case.relevant_ids, selected) if selected else 0.0
        )
        return {
            "answer_support": answer_support(case.required_ids, selected),
            "selection_recall": selection_recall(case.relevant_ids, selected),
            "selection_precision": precision,
        }
