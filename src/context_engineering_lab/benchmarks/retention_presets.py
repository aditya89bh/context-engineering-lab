"""Named presets of the retention benchmark.

Three presets, each isolating one forgetting regime built from the
``retention-utility-preservation`` generator: a low-noise sanity floor, a
stale-accumulation stress, and a harmful-memory stress. Three is intentionally
enough; more presets would add combinations without adding insight.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.retention import (
    RetentionBenchmark,
    RetentionConfig,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit

_BUDGET_SWEEP: tuple[Budget, ...] = (
    Budget(2, BudgetUnit.ITEMS),
    Budget(4, BudgetUnit.ITEMS),
    Budget(8, BudgetUnit.ITEMS),
    Budget(16, BudgetUnit.ITEMS),
)


def low_noise_retention() -> RetentionBenchmark:
    """Clean signals: salience separates useful from harmful.

    Construct: with low noise, can a utility-aware policy keep useful information
    and drop harm? This is the sanity floor — salience and the hybrid blend should
    approach the oracle, while frequency and recency retain harmful items.
    """
    return RetentionBenchmark(
        RetentionConfig(
            benchmark_id="low-noise-retention",
            version="1.0",
            construct="retention with well-separated useful and harmful signals",
            num_cases=24,
            num_useful=4,
            num_required=2,
            num_stale=3,
            num_harmful=3,
            num_neutral=6,
            noise="low",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "frequency retains high-frequency harmful items",
                "recency retains recent harmful items and forgets old useful ones",
            ),
        )
    )


def stale_accumulation() -> RetentionBenchmark:
    """Memory fills with stale and neutral items as it grows.

    Construct: as stale and filler accumulate, does a policy still surface the
    useful items? Recency forgets stale (it is old) but also forgets old useful
    items; retain-all blows the budget while keeping everything stale.
    """
    return RetentionBenchmark(
        RetentionConfig(
            benchmark_id="stale-accumulation",
            version="1.0",
            construct="retention as stale and neutral memory accumulates",
            num_cases=24,
            num_useful=4,
            num_required=2,
            num_stale=10,
            num_harmful=2,
            num_neutral=10,
            noise="low",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "retain-all overruns the budget as stale items pile up",
                "recency forgets old useful items along with the stale ones",
            ),
        )
    )


def harmful_memory() -> RetentionBenchmark:
    """Dense harmful items with overlapping observable signals.

    Construct: when harmful items are plentiful and their salience overlaps the
    useful items (high noise), how well can a policy still forget harm? Single
    signals degrade; the hybrid blend should remain the best deployable policy,
    well below the oracle ceiling.
    """
    return RetentionBenchmark(
        RetentionConfig(
            benchmark_id="harmful-memory",
            version="1.0",
            construct="forgetting harm under heavy, signal-overlapping harmful load",
            num_cases=24,
            num_useful=4,
            num_required=2,
            num_stale=3,
            num_harmful=10,
            num_neutral=3,
            noise="high",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "frequency and recency retain many harmful items",
                "salience is unreliable when harmful salience overlaps useful",
                "no deployable policy matches the oracle under high noise",
            ),
        )
    )


def all_retention_presets() -> tuple[RetentionBenchmark, ...]:
    """Return all three retention presets."""
    return (
        low_noise_retention(),
        stale_accumulation(),
        harmful_memory(),
    )
