"""Tests for Phase 3 experiment configurations."""

from __future__ import annotations

from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase3 import (
    PHASE3_SEEDS,
    compression_budget_sweep,
    default_strategies,
    phase3_experiments,
)


def test_phase3_experiments_are_named_as_expected() -> None:
    experiments = phase3_experiments()
    assert set(experiments) == {
        "compression-baselines-easy",
        "compression-late-signal",
        "compression-distractor-density",
        "compression-budget-sweep",
    }


def test_each_experiment_runs_multiple_strategies_and_seeds() -> None:
    for experiment in phase3_experiments().values():
        assert experiment.seeds == PHASE3_SEEDS
        assert len(experiment.strategies) == len(default_strategies())


def test_budget_sweep_overrides_benchmark_budgets() -> None:
    experiment = compression_budget_sweep()
    assert experiment.budgets is not None
    assert [b.limit for b in experiment.budgets] == [2, 4, 6, 8, 12, 16, 24, 32]


def test_experiments_run_and_are_deterministic() -> None:
    experiment = phase3_experiments()["compression-baselines-easy"]
    first = ExperimentRunner().run(experiment)
    second = ExperimentRunner().run(experiment)
    assert first.to_dict() == second.to_dict()
    assert len(first.results) == 6


def test_oracle_compression_leads_information_retention() -> None:
    result = ExperimentRunner().run(
        phase3_experiments()["compression-distractor-density"]
    )
    by_strategy = {r.strategy_id: r for r in result.results}
    oracle_values = [
        m.value
        for m in by_strategy["oracle-compression"].metrics
        if m.name == "information_retention"
    ]
    head_values = [
        m.value
        for m in by_strategy["head-truncation"].metrics
        if m.name == "information_retention"
    ]
    assert min(oracle_values) >= max(head_values)
