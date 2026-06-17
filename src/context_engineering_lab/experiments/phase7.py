"""Phase 7 experiment configurations: interactions between primitives.

Four reproducible experiments, each pairing an interaction preset with the same
line-up of *primitive-only baselines* and *composed pipelines* so a composition
can be read directly against its constituents. They are small and deterministic.
They produce controlled observations on these synthetic benchmarks only; they do
not support broad claims about how context systems behave, and they add no
scheduler, agent loop, or event system.

The line-up is item-budget: every baseline and every shipped pipeline ends in a
stage that respects an item budget, so a single budget sweep compares them
fairly. The compression-ending pipelines in
:mod:`context_engineering_lab.compositions` are token-budget and are exercised in
tests, not in this suite.
"""

from __future__ import annotations

from context_engineering_lab.attention.adaptive import AdaptiveAllocation
from context_engineering_lab.benchmarks.interaction_presets import (
    balanced_interaction,
    memory_pressure,
    noisy_context,
)
from context_engineering_lab.compositions import (
    item_budget_compositions,
    oracle_pipeline,
)
from context_engineering_lab.core.attention import AllocatorStrategy
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.retention import PolicyStrategy
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.retention.frequency import FrequencyRetentionPolicy
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection
from context_engineering_lab.strategies.temporal import SlidingWindowSelection

#: Seeds every Phase 7 experiment runs over.
PHASE7_SEEDS: tuple[int, ...] = (1, 2, 3)


def primitive_baselines() -> tuple[Strategy, ...]:
    """Return the primitive-only baselines, one per composable family.

    A keyword selector, a recency-window temporal selector, a frequency-based
    retention policy, and a capacity-aware attention allocator. These are exactly
    the stages the Phase 7 pipelines chain, so a pipeline can be compared against
    each of its parts run alone.
    """
    return (
        KeywordOverlapSelection(),
        SlidingWindowSelection(),
        PolicyStrategy(FrequencyRetentionPolicy()),
        AllocatorStrategy(AdaptiveAllocation()),
    )


def default_strategies() -> tuple[Strategy, ...]:
    """Return baselines, composed pipelines, and the oracle ceiling."""
    return (
        *primitive_baselines(),
        *item_budget_compositions(),
        oracle_pipeline(),
    )


def interaction_balanced() -> Experiment:
    """Baselines and pipelines when traps and stale items are sparse."""
    return Experiment(
        experiment_id=ExperimentId("interaction-balanced"),
        benchmark=balanced_interaction(),
        strategies=default_strategies(),
        seeds=PHASE7_SEEDS,
    )


def interaction_memory_pressure() -> Experiment:
    """Baselines and pipelines against many harmful traps under tight budgets."""
    return Experiment(
        experiment_id=ExperimentId("interaction-memory-pressure"),
        benchmark=memory_pressure(),
        strategies=default_strategies(),
        seeds=PHASE7_SEEDS,
    )


def interaction_noisy_context() -> Experiment:
    """Baselines and pipelines under dense stale and distractor noise."""
    return Experiment(
        experiment_id=ExperimentId("interaction-noisy-context"),
        benchmark=noisy_context(),
        strategies=default_strategies(),
        seeds=PHASE7_SEEDS,
    )


def interaction_budget_sweep() -> Experiment:
    """Trace interaction effects with a finer budget ladder.

    Reuses the memory-pressure preset (dense harmful traps) but overrides the
    budget sweep with a finer ladder to locate where a tightening budget changes
    which composition dominates.
    """
    budgets = tuple(
        Budget(limit, BudgetUnit.ITEMS) for limit in (2, 4, 6, 8, 10, 12, 16, 20)
    )
    return Experiment(
        experiment_id=ExperimentId("interaction-budget-sweep"),
        benchmark=memory_pressure(),
        strategies=default_strategies(),
        seeds=PHASE7_SEEDS,
        budgets=budgets,
    )


def phase7_experiments() -> dict[str, Experiment]:
    """Return all Phase 7 experiments keyed by their experiment id."""
    experiments = (
        interaction_balanced(),
        interaction_memory_pressure(),
        interaction_noisy_context(),
        interaction_budget_sweep(),
    )
    return {str(exp.experiment_id): exp for exp in experiments}
