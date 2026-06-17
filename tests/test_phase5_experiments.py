"""Tests for the Phase 5 retention experiment configurations."""

from __future__ import annotations

from context_engineering_lab.core.budget import BudgetUnit
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase5 import (
    PHASE5_SEEDS,
    default_strategies,
    phase5_experiments,
)


def test_phase5_has_four_named_experiments() -> None:
    experiments = phase5_experiments()
    assert set(experiments) == {
        "retention-baselines",
        "stale-accumulation",
        "harmful-memory",
        "retention-budget-sweep",
    }


def test_default_strategies_line_up() -> None:
    ids = [str(s.id) for s in default_strategies()]
    assert ids == [
        "retain-all",
        "recency-retention",
        "frequency-retention",
        "salience-retention",
        "hybrid-retention-0.5-0.3-0.2",
        "oracle-retention",
    ]


def test_every_experiment_uses_three_seeds() -> None:
    for exp in phase5_experiments().values():
        assert exp.seeds == PHASE5_SEEDS == (1, 2, 3)


def test_budget_sweep_overrides_with_finer_ladder() -> None:
    sweep = phase5_experiments()["retention-budget-sweep"]
    assert sweep.budgets is not None
    limits = [b.limit for b in sweep.budgets]
    assert limits == [1, 2, 3, 4, 6, 8, 12, 16]
    assert all(b.unit is BudgetUnit.ITEMS for b in sweep.budgets)


def test_experiments_run_and_produce_results() -> None:
    runner = ExperimentRunner()
    for exp in phase5_experiments().values():
        result = runner.run(exp)
        assert len(result.results) == 6
        assert result.metadata.run_id.value


def test_salience_forgets_harm_better_than_frequency_low_noise() -> None:
    runner = ExperimentRunner()
    result = runner.run(phase5_experiments()["retention-baselines"])
    by_id = {r.strategy_id: r for r in result.results}

    def mean(strategy: str, metric: str) -> float:
        values = [m.value for m in by_id[strategy].metrics if m.name == metric]
        return sum(values) / len(values)

    assert mean("salience-retention", "harmful_retention_rate") < mean(
        "frequency-retention", "harmful_retention_rate"
    )


def test_oracle_is_the_ceiling_on_forgetting_efficiency() -> None:
    runner = ExperimentRunner()
    result = runner.run(phase5_experiments()["harmful-memory"])
    by_id = {r.strategy_id: r for r in result.results}

    def mean_efficiency(strategy: str) -> float:
        values = [
            m.value
            for m in by_id[strategy].metrics
            if m.name == "forgetting_efficiency"
        ]
        return sum(values) / len(values)

    oracle = mean_efficiency("oracle-retention")
    for strategy in by_id:
        if strategy != "oracle-retention":
            assert mean_efficiency(strategy) <= oracle
