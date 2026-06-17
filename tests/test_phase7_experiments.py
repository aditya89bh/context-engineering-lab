"""Tests for the Phase 7 interaction experiment configurations."""

from __future__ import annotations

from context_engineering_lab.core.budget import BudgetUnit
from context_engineering_lab.core.results import StrategyRunResult
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase7 import (
    PHASE7_SEEDS,
    default_strategies,
    phase7_experiments,
)


def test_phase7_has_four_named_experiments() -> None:
    experiments = phase7_experiments()
    assert set(experiments) == {
        "interaction-balanced",
        "interaction-memory-pressure",
        "interaction-noisy-context",
        "interaction-budget-sweep",
    }


def test_default_strategies_mix_baselines_and_pipelines() -> None:
    ids = [str(s.id) for s in default_strategies()]
    assert ids == [
        "keyword-overlap",
        "sliding-window-5",
        "frequency-retention",
        "adaptive-allocation",
        "temporal->selection",
        "attention->selection",
        "retention->attention",
        "temporal->retention",
        "retention->selection",
        "oracle-pipeline",
    ]


def test_every_experiment_uses_three_seeds() -> None:
    for exp in phase7_experiments().values():
        assert exp.seeds == PHASE7_SEEDS == (1, 2, 3)


def test_budget_sweep_overrides_with_finer_ladder() -> None:
    sweep = phase7_experiments()["interaction-budget-sweep"]
    assert sweep.budgets is not None
    limits = [b.limit for b in sweep.budgets]
    assert limits == [2, 4, 6, 8, 10, 12, 16, 20]
    assert all(b.unit is BudgetUnit.ITEMS for b in sweep.budgets)


def test_experiments_run_and_produce_results() -> None:
    runner = ExperimentRunner()
    for exp in phase7_experiments().values():
        result = runner.run(exp)
        assert len(result.results) == 10
        assert result.metadata.run_id.value


def _mean(
    by_id: dict[str, StrategyRunResult], strategy: str, metric: str
) -> float:
    values = [m.value for m in by_id[strategy].metrics if m.name == metric]
    return sum(values) / len(values)


def test_retention_stage_cuts_harmful_retention_versus_selection() -> None:
    runner = ExperimentRunner()
    result = runner.run(phase7_experiments()["interaction-memory-pressure"])
    by_id = {r.strategy_id: r for r in result.results}
    # A frequency-aware forgetting stage before selection removes harmful traps
    # that keyword selection alone keeps (they carry the query terms).
    assert _mean(by_id, "retention->selection", "harmful_retention_rate") < _mean(
        by_id, "keyword-overlap", "harmful_retention_rate"
    )


def test_oracle_pipeline_is_the_ceiling_on_recall() -> None:
    runner = ExperimentRunner()
    result = runner.run(phase7_experiments()["interaction-balanced"])
    by_id = {r.strategy_id: r for r in result.results}
    oracle = _mean(by_id, "oracle-pipeline", "selection_recall")
    for strategy in by_id:
        if strategy != "oracle-pipeline":
            assert _mean(by_id, strategy, "selection_recall") <= oracle + 1e-9
