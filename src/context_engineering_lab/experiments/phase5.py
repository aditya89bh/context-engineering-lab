"""Phase 5 experiment configurations: forgetting under memory budgets.

Four reproducible experiments, each pairing a retention preset with the same
policy line-up so results are directly comparable. They are small and
deterministic. They produce controlled observations on these synthetic benchmarks
only; they do not support broad claims about memory systems in general, and they
implement no memory store or persistence.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.retention_presets import (
    harmful_memory,
    low_noise_retention,
    stale_accumulation,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.retention import PolicyStrategy
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.retention import default_policies

#: Seeds every Phase 5 experiment runs over.
PHASE5_SEEDS: tuple[int, ...] = (1, 2, 3)


def default_strategies() -> tuple[Strategy, ...]:
    """Return the standard Phase 5 retention policy line-up, wrapped as strategies.

    Spans a retain-all reference, single-signal policies (recency, frequency,
    salience), a hybrid blend, and the oracle ceiling (which is **not
    deployable**).
    """
    return tuple(PolicyStrategy(policy) for policy in default_policies())


def retention_baselines() -> Experiment:
    """Policies on the low-noise preset."""
    return Experiment(
        experiment_id=ExperimentId("retention-baselines"),
        benchmark=low_noise_retention(),
        strategies=default_strategies(),
        seeds=PHASE5_SEEDS,
    )


def retention_stale_accumulation() -> Experiment:
    """Probe retention as stale and neutral memory accumulates."""
    return Experiment(
        experiment_id=ExperimentId("stale-accumulation"),
        benchmark=stale_accumulation(),
        strategies=default_strategies(),
        seeds=PHASE5_SEEDS,
    )


def retention_harmful_memory() -> Experiment:
    """Stress forgetting under dense, signal-overlapping harmful items."""
    return Experiment(
        experiment_id=ExperimentId("harmful-memory"),
        benchmark=harmful_memory(),
        strategies=default_strategies(),
        seeds=PHASE5_SEEDS,
    )


def retention_budget_sweep() -> Experiment:
    """Trace the retention-quality curve with a finer memory-budget ladder.

    Reuses the harmful-memory preset (20 items) but overrides the budget sweep
    with a finer ladder to locate where shrinking memory breaks utility recovery.
    """
    budgets = tuple(
        Budget(limit, BudgetUnit.ITEMS) for limit in (1, 2, 3, 4, 6, 8, 12, 16)
    )
    return Experiment(
        experiment_id=ExperimentId("retention-budget-sweep"),
        benchmark=harmful_memory(),
        strategies=default_strategies(),
        seeds=PHASE5_SEEDS,
        budgets=budgets,
    )


def phase5_experiments() -> dict[str, Experiment]:
    """Return all Phase 5 experiments keyed by their experiment id."""
    experiments = (
        retention_baselines(),
        retention_stale_accumulation(),
        retention_harmful_memory(),
        retention_budget_sweep(),
    )
    return {str(exp.experiment_id): exp for exp in experiments}
