"""Phase 6 experiment configurations: attention allocation across sources.

Four reproducible experiments, each pairing an attention preset with the same
allocator line-up so results are directly comparable. They are small and
deterministic. They produce controlled observations on these synthetic benchmarks
only; they do not support broad claims about attention mechanisms, and they
implement no scheduler, agent loop, or event system.
"""

from __future__ import annotations

from context_engineering_lab.attention import default_allocators
from context_engineering_lab.benchmarks.attention_presets import (
    balanced_sources,
    concentrated_signal,
    noisy_dominant_source,
)
from context_engineering_lab.core.attention import AllocatorStrategy
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.strategy import Strategy

#: Seeds every Phase 6 experiment runs over.
PHASE6_SEEDS: tuple[int, ...] = (1, 2, 3)


def default_strategies() -> tuple[Strategy, ...]:
    """Return the standard Phase 6 allocator line-up, wrapped as strategies.

    Spans a uniform baseline, size- and salience-proportional splits, a
    capacity-aware adaptive policy, a winner-take-most concentrator, and the
    oracle ceiling (which is **not deployable**).
    """
    return tuple(AllocatorStrategy(allocator) for allocator in default_allocators())


def attention_balanced() -> Experiment:
    """Allocators on comparably useful sources."""
    return Experiment(
        experiment_id=ExperimentId("attention-balanced"),
        benchmark=balanced_sources(),
        strategies=default_strategies(),
        seeds=PHASE6_SEEDS,
    )


def attention_concentrated() -> Experiment:
    """Allocators when the signal sits in one source."""
    return Experiment(
        experiment_id=ExperimentId("attention-concentrated"),
        benchmark=concentrated_signal(),
        strategies=default_strategies(),
        seeds=PHASE6_SEEDS,
    )


def attention_noisy_dominant() -> Experiment:
    """Allocators against a large, salient, low-signal trap source."""
    return Experiment(
        experiment_id=ExperimentId("attention-noisy-dominant"),
        benchmark=noisy_dominant_source(),
        strategies=default_strategies(),
        seeds=PHASE6_SEEDS,
    )


def attention_budget_sweep() -> Experiment:
    """Trace allocation quality with a finer budget ladder.

    Reuses the noisy-dominant preset (a 4-source case plus an oversized trap) but
    overrides the budget sweep with a finer ladder to locate where a tightening
    budget forces allocators to commit.
    """
    budgets = tuple(
        Budget(limit, BudgetUnit.ITEMS) for limit in (2, 4, 6, 8, 12, 16, 20, 24)
    )
    return Experiment(
        experiment_id=ExperimentId("attention-budget-sweep"),
        benchmark=noisy_dominant_source(),
        strategies=default_strategies(),
        seeds=PHASE6_SEEDS,
        budgets=budgets,
    )


def phase6_experiments() -> dict[str, Experiment]:
    """Return all Phase 6 experiments keyed by their experiment id."""
    experiments = (
        attention_balanced(),
        attention_concentrated(),
        attention_noisy_dominant(),
        attention_budget_sweep(),
    )
    return {str(exp.experiment_id): exp for exp in experiments}
