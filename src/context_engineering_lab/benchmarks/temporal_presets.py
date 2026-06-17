"""Named presets of the temporal benchmark.

Three presets, each isolating one temporal regime. They share the
``temporal-context-relevance`` generator but fix its knobs to probe a specific
question: is recency a good heuristic when the signal is fresh, when it is old,
and when an observable signal drifts away from the truth? Three is intentionally
enough; more presets would add combinations without adding insight.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.temporal import (
    TemporalBenchmark,
    TemporalConfig,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit

_BUDGET_SWEEP: tuple[Budget, ...] = (
    Budget(1, BudgetUnit.ITEMS),
    Budget(2, BudgetUnit.ITEMS),
    Budget(4, BudgetUnit.ITEMS),
    Budget(8, BudgetUnit.ITEMS),
)


def recent_signal() -> TemporalBenchmark:
    """Signal is fresh: the relevant items are the most recent.

    Construct: when relevance really is recent, recency-style strategies (and the
    sliding window) should track the oracle, while oldest-first and the fixed
    leading window look in the wrong era.
    """
    return TemporalBenchmark(
        TemporalConfig(
            benchmark_id="recent-signal",
            version="1.0",
            construct="temporal retrieval when the relevant signal is recent",
            num_cases=24,
            sequence_length=20,
            num_relevant=3,
            num_distractors=8,
            num_stale=4,
            relevant_age="recent",
            distractor_age="mixed",
            drift="none",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "oldest-first and the fixed leading window miss the recent signal",
                "recency, sliding-window, and age-weighted should track the oracle",
            ),
        )
    )


def old_signal() -> TemporalBenchmark:
    """Signal is stale-looking but still relevant: the relevant items are old.

    Construct: when relevance is old and recent items are distractors, recency
    and the sliding window fail; oldest-first and the fixed leading window
    succeed. This is the direct counter-example to "recency is always good".
    """
    return TemporalBenchmark(
        TemporalConfig(
            benchmark_id="old-signal",
            version="1.0",
            construct="temporal retrieval when the relevant signal is old",
            num_cases=24,
            sequence_length=20,
            num_relevant=3,
            num_distractors=8,
            num_stale=4,
            relevant_age="old",
            distractor_age="recent",
            drift="none",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "recency and sliding-window chase recent distractors, missing the "
                "old signal",
                "oldest-first and the fixed leading window recover the old signal",
            ),
        )
    )


def drift_heavy() -> TemporalBenchmark:
    """Observable salience drifts to recent decoys while truth is spread out.

    Construct: relevance is spread across time, but an abrupt drift gives recent
    distractors high observable salience. This probes sensitivity to temporal
    drift: age-weighted selection (which trusts salience) is pulled toward the
    decoys, and only the oracle reliably recovers the spread-out signal.
    """
    return TemporalBenchmark(
        TemporalConfig(
            benchmark_id="drift-heavy",
            version="1.0",
            construct="sensitivity to abrupt temporal drift in the salience signal",
            num_cases=24,
            sequence_length=24,
            num_relevant=4,
            num_distractors=10,
            num_stale=4,
            relevant_age="mixed",
            distractor_age="recent",
            drift="abrupt",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "age-weighted is pulled toward recent high-salience decoys",
                "recency captures only the recent half of a spread-out signal",
                "no deployable strategy matches the oracle under abrupt drift",
            ),
        )
    )


def all_temporal_presets() -> tuple[TemporalBenchmark, ...]:
    """Return all three temporal presets."""
    return (
        recent_signal(),
        old_signal(),
        drift_heavy(),
    )
