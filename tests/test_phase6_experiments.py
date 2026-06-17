"""Tests for the Phase 6 attention experiment configurations."""

from __future__ import annotations

from context_engineering_lab.core.budget import BudgetUnit
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase6 import (
    PHASE6_SEEDS,
    default_strategies,
    phase6_experiments,
)


def test_phase6_has_four_named_experiments() -> None:
    experiments = phase6_experiments()
    assert set(experiments) == {
        "attention-balanced",
        "attention-concentrated",
        "attention-noisy-dominant",
        "attention-budget-sweep",
    }


def test_default_strategies_line_up() -> None:
    ids = [str(s.id) for s in default_strategies()]
    assert ids == [
        "uniform-allocation",
        "proportional-allocation",
        "salience-allocation",
        "adaptive-allocation",
        "winner-take-most-0.7",
        "oracle-allocation",
    ]


def test_every_experiment_uses_three_seeds() -> None:
    for exp in phase6_experiments().values():
        assert exp.seeds == PHASE6_SEEDS == (1, 2, 3)


def test_budget_sweep_overrides_with_finer_ladder() -> None:
    sweep = phase6_experiments()["attention-budget-sweep"]
    assert sweep.budgets is not None
    limits = [b.limit for b in sweep.budgets]
    assert limits == [2, 4, 6, 8, 12, 16, 20, 24]
    assert all(b.unit is BudgetUnit.ITEMS for b in sweep.budgets)


def test_experiments_run_and_produce_results() -> None:
    runner = ExperimentRunner()
    for exp in phase6_experiments().values():
        result = runner.run(exp)
        assert len(result.results) == 6
        assert result.metadata.run_id.value


def test_uniform_is_competitive_on_balanced_sources() -> None:
    runner = ExperimentRunner()
    result = runner.run(phase6_experiments()["attention-balanced"])
    by_id = {r.strategy_id: r for r in result.results}

    def mean(strategy: str, metric: str) -> float:
        values = [m.value for m in by_id[strategy].metrics if m.name == metric]
        return sum(values) / len(values)

    # Winner-take-most starves the other useful sources when signal is spread.
    assert mean("uniform-allocation", "signal_capture_rate") > mean(
        "winner-take-most-0.7", "signal_capture_rate"
    )


def test_proportional_wastes_attention_on_noisy_dominant() -> None:
    runner = ExperimentRunner()
    result = runner.run(phase6_experiments()["attention-noisy-dominant"])
    by_id = {r.strategy_id: r for r in result.results}

    def mean(strategy: str, metric: str) -> float:
        values = [m.value for m in by_id[strategy].metrics if m.name == metric]
        return sum(values) / len(values)

    assert mean("proportional-allocation", "wasted_attention_rate") > mean(
        "adaptive-allocation", "wasted_attention_rate"
    )


def test_oracle_is_the_ceiling_on_signal_capture() -> None:
    runner = ExperimentRunner()
    result = runner.run(phase6_experiments()["attention-concentrated"])
    by_id = {r.strategy_id: r for r in result.results}

    def mean_capture(strategy: str) -> float:
        values = [
            m.value
            for m in by_id[strategy].metrics
            if m.name == "signal_capture_rate"
        ]
        return sum(values) / len(values)

    oracle = mean_capture("oracle-allocation")
    for strategy in by_id:
        if strategy != "oracle-allocation":
            assert mean_capture(strategy) <= oracle + 1e-9
