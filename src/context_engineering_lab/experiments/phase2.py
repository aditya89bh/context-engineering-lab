"""Phase 2 experiment configurations: selection under budget pressure.

Four reproducible experiments, each pairing a selection preset with the same set
of strategies so results are directly comparable. They are deliberately small
and deterministic. They produce controlled observations on these benchmarks
only; they do not support broad claims about context engineering in general.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.selection_presets import (
    easy_selection,
    high_distractor_selection,
    position_biased_selection,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection
from context_engineering_lab.strategies.oracle import OracleSelection
from context_engineering_lab.strategies.positional import (
    FirstNSelection,
    LastNSelection,
)
from context_engineering_lab.strategies.random_selection import RandomSelection
from context_engineering_lab.strategies.recency import RecencySelection

#: Seeds every Phase 2 experiment runs over.
PHASE2_SEEDS: tuple[int, ...] = (1, 2, 3)


def default_strategies() -> tuple[Strategy, ...]:
    """Return the standard Phase 2 strategy line-up, in a stable order.

    Includes content-blind baselines (lower bounds), a content-aware baseline,
    and the oracle (an upper bound; not deployable).
    """
    return (
        FirstNSelection(),
        LastNSelection(),
        RecencySelection(),
        RandomSelection(),
        KeywordOverlapSelection(),
        OracleSelection(),
    )


def selection_baselines_easy() -> Experiment:
    """Baselines on the low-interference preset."""
    return Experiment(
        experiment_id=ExperimentId("selection-baselines-easy"),
        benchmark=easy_selection(),
        strategies=default_strategies(),
        seeds=PHASE2_SEEDS,
    )


def selection_position_bias() -> Experiment:
    """Probe position bias with a consistently late target."""
    return Experiment(
        experiment_id=ExperimentId("selection-position-bias"),
        benchmark=position_biased_selection(),
        strategies=default_strategies(),
        seeds=PHASE2_SEEDS,
    )


def selection_distractor_stress() -> Experiment:
    """Stress selection under heavy, look-alike distractor load."""
    return Experiment(
        experiment_id=ExperimentId("selection-distractor-stress"),
        benchmark=high_distractor_selection(),
        strategies=default_strategies(),
        seeds=PHASE2_SEEDS,
    )


def selection_budget_sweep() -> Experiment:
    """Map the budget-performance curve with a finer budget sweep.

    Reuses the high-distractor preset (16 candidates) but overrides the budget
    sweep with a finer ladder to locate where reducing the budget breaks the
    task.
    """
    budgets = tuple(
        Budget(limit, BudgetUnit.ITEMS) for limit in (1, 2, 3, 4, 6, 8, 12, 16)
    )
    return Experiment(
        experiment_id=ExperimentId("selection-budget-sweep"),
        benchmark=high_distractor_selection(),
        strategies=default_strategies(),
        seeds=PHASE2_SEEDS,
        budgets=budgets,
    )


def phase2_experiments() -> dict[str, Experiment]:
    """Return all Phase 2 experiments keyed by their experiment id."""
    experiments = (
        selection_baselines_easy(),
        selection_position_bias(),
        selection_distractor_stress(),
        selection_budget_sweep(),
    )
    return {str(exp.experiment_id): exp for exp in experiments}
