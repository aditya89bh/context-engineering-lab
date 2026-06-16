"""Tests for Phase 2 experiment configurations."""

from __future__ import annotations

from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase2 import (
    PHASE2_SEEDS,
    default_strategies,
    phase2_experiments,
    selection_budget_sweep,
)


def test_phase2_experiments_are_named_as_expected() -> None:
    experiments = phase2_experiments()
    assert set(experiments) == {
        "selection-baselines-easy",
        "selection-position-bias",
        "selection-distractor-stress",
        "selection-budget-sweep",
    }


def test_each_experiment_runs_multiple_strategies_and_seeds() -> None:
    for experiment in phase2_experiments().values():
        assert experiment.seeds == PHASE2_SEEDS
        assert len(experiment.strategies) == len(default_strategies())


def test_budget_sweep_overrides_benchmark_budgets() -> None:
    experiment = selection_budget_sweep()
    assert experiment.budgets is not None
    assert [b.limit for b in experiment.budgets] == [1, 2, 3, 4, 6, 8, 12, 16]


def test_experiments_run_and_are_deterministic() -> None:
    experiment = phase2_experiments()["selection-baselines-easy"]
    first = ExperimentRunner().run(experiment)
    second = ExperimentRunner().run(experiment)
    assert first.to_dict() == second.to_dict()
    # 6 strategies in the line-up.
    assert len(first.results) == 6
