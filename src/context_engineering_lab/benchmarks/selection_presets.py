"""Named presets of the selection benchmark.

Three presets, each isolating one construct. They share the
``selection-signal-retrieval`` generator but fix its knobs to probe a specific
question. Three is intentionally enough; more presets would add combinations
without adding insight.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.selection import (
    SelectionBenchmark,
    SelectionConfig,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit


def easy_selection() -> SelectionBenchmark:
    """Low interference: few, dissimilar distractors, random target position.

    Construct: can a strategy retrieve an obvious target when little stands in
    the way? This is the sanity floor; most strategies should do well once the
    budget is not tiny.
    """
    return SelectionBenchmark(
        SelectionConfig(
            benchmark_id="easy-selection",
            version="1.0",
            construct="basic signal retrieval with low distractor interference",
            num_cases=24,
            num_distractors=4,
            target_position="random",
            distractor_similarity="low",
            budget_sweep=(
                Budget(1, BudgetUnit.ITEMS),
                Budget(2, BudgetUnit.ITEMS),
                Budget(3, BudgetUnit.ITEMS),
                Budget(5, BudgetUnit.ITEMS),
            ),
            expected_failure_modes=(
                "position-blind baselines miss the target only at budget 1",
                "keyword-overlap should track the oracle closely",
            ),
        )
    )


def position_biased_selection() -> SelectionBenchmark:
    """Target always late: exposes position bias in order-only baselines.

    Construct: does a baseline succeed for the wrong reason? With the target
    placed late, ``first-n`` should fail at small budgets while ``last-n`` and
    ``recency`` succeed, even though none of them read content.
    """
    return SelectionBenchmark(
        SelectionConfig(
            benchmark_id="position-biased-selection",
            version="1.0",
            construct="position bias of order-only baselines (target placed late)",
            num_cases=24,
            num_distractors=7,
            target_position="late",
            distractor_similarity="low",
            budget_sweep=(
                Budget(1, BudgetUnit.ITEMS),
                Budget(2, BudgetUnit.ITEMS),
                Budget(4, BudgetUnit.ITEMS),
                Budget(8, BudgetUnit.ITEMS),
            ),
            expected_failure_modes=(
                "first-n misses the late target until the budget is large",
                "last-n and recency succeed by position, not by relevance",
            ),
        )
    )


def high_distractor_selection() -> SelectionBenchmark:
    """Many look-alike distractors: stresses content-based selection.

    Construct: how do precision and recall degrade under heavy distractor load
    when distractors share every signal term? Keyword overlap can no longer tell
    target from distractor; only the oracle (a ceiling) is reliable.
    """
    return SelectionBenchmark(
        SelectionConfig(
            benchmark_id="high-distractor-selection",
            version="1.0",
            construct="selection under heavy, content-similar distractor load",
            num_cases=24,
            num_distractors=15,
            target_position="random",
            distractor_similarity="high",
            budget_sweep=(
                Budget(1, BudgetUnit.ITEMS),
                Budget(2, BudgetUnit.ITEMS),
                Budget(4, BudgetUnit.ITEMS),
                Budget(8, BudgetUnit.ITEMS),
            ),
            expected_failure_modes=(
                "keyword-overlap cannot separate target from look-alike distractors",
                "non-oracle strategies retrieve the target mostly by chance",
            ),
        )
    )


def all_selection_presets() -> tuple[SelectionBenchmark, ...]:
    """Return all three selection presets."""
    return (
        easy_selection(),
        position_biased_selection(),
        high_distractor_selection(),
    )
