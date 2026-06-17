"""Phase 4 experiment configurations: temporal context under budget pressure.

Four reproducible experiments, each pairing a temporal preset with the same
strategy line-up so results are directly comparable. They are small and
deterministic. They produce controlled observations on these synthetic
benchmarks only; they do not support broad claims about temporal reasoning in
general, and they implement no forgetting or retention policy.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.temporal_presets import (
    drift_heavy,
    old_signal,
    recent_signal,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.strategies.recency import RecencySelection
from context_engineering_lab.strategies.temporal import (
    AgeWeightedSelection,
    FixedWindowSelection,
    OldestFirstSelection,
    OracleTemporalSelection,
    SlidingWindowSelection,
)

#: Seeds every Phase 4 experiment runs over.
PHASE4_SEEDS: tuple[int, ...] = (1, 2, 3)


def default_strategies() -> tuple[Strategy, ...]:
    """Return the standard Phase 4 temporal strategy line-up, in a stable order.

    Spans the recency baseline, its temporal foils (oldest-first, sliding and
    fixed windows), an age-aware weighting that reads observable salience, and
    the oracle ceiling (which is **not deployable**).
    """
    return (
        RecencySelection(),
        OldestFirstSelection(),
        SlidingWindowSelection(),
        FixedWindowSelection(),
        AgeWeightedSelection(),
        OracleTemporalSelection(),
    )


def temporal_recent_signal() -> Experiment:
    """Strategies on the recent-signal preset."""
    return Experiment(
        experiment_id=ExperimentId("temporal-recent-signal"),
        benchmark=recent_signal(),
        strategies=default_strategies(),
        seeds=PHASE4_SEEDS,
    )


def temporal_old_signal() -> Experiment:
    """Probe whether recency fails when the relevant signal is old."""
    return Experiment(
        experiment_id=ExperimentId("temporal-old-signal"),
        benchmark=old_signal(),
        strategies=default_strategies(),
        seeds=PHASE4_SEEDS,
    )


def temporal_drift() -> Experiment:
    """Stress strategies under abrupt temporal drift in the salience signal."""
    return Experiment(
        experiment_id=ExperimentId("temporal-drift"),
        benchmark=drift_heavy(),
        strategies=default_strategies(),
        seeds=PHASE4_SEEDS,
    )


def temporal_budget_sweep() -> Experiment:
    """Trace the budget-performance curve with a finer budget ladder.

    Reuses the drift-heavy preset (24 items) but overrides the budget sweep with
    a finer ladder to locate where shrinking the budget breaks temporal recovery.
    """
    budgets = tuple(
        Budget(limit, BudgetUnit.ITEMS) for limit in (1, 2, 3, 4, 6, 8, 12, 16)
    )
    return Experiment(
        experiment_id=ExperimentId("temporal-budget-sweep"),
        benchmark=drift_heavy(),
        strategies=default_strategies(),
        seeds=PHASE4_SEEDS,
        budgets=budgets,
    )


def phase4_experiments() -> dict[str, Experiment]:
    """Return all Phase 4 experiments keyed by their experiment id."""
    experiments = (
        temporal_recent_signal(),
        temporal_old_signal(),
        temporal_drift(),
        temporal_budget_sweep(),
    )
    return {str(exp.experiment_id): exp for exp in experiments}
