"""Tests for the Phase 4 temporal experiment configurations."""

from __future__ import annotations

from context_engineering_lab.core.budget import BudgetUnit
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase4 import (
    PHASE4_SEEDS,
    default_strategies,
    phase4_experiments,
)


def test_phase4_has_four_named_experiments() -> None:
    experiments = phase4_experiments()
    assert set(experiments) == {
        "temporal-recent-signal",
        "temporal-old-signal",
        "temporal-drift",
        "temporal-budget-sweep",
    }


def test_default_strategies_line_up() -> None:
    ids = [str(s.id) for s in default_strategies()]
    assert ids == [
        "recency",
        "oldest-first",
        "sliding-window-5",
        "fixed-window-5",
        "age-weighted-hl4",
        "oracle-temporal",
    ]


def test_every_experiment_uses_three_seeds() -> None:
    for exp in phase4_experiments().values():
        assert exp.seeds == PHASE4_SEEDS == (1, 2, 3)


def test_budget_sweep_overrides_with_finer_ladder() -> None:
    sweep = phase4_experiments()["temporal-budget-sweep"]
    assert sweep.budgets is not None
    limits = [b.limit for b in sweep.budgets]
    assert limits == [1, 2, 3, 4, 6, 8, 12, 16]
    assert all(b.unit is BudgetUnit.ITEMS for b in sweep.budgets)


def test_experiments_run_and_produce_results() -> None:
    runner = ExperimentRunner()
    for exp in phase4_experiments().values():
        result = runner.run(exp)
        assert len(result.results) == 6
        assert result.metadata.run_id.value


def test_old_signal_oldest_first_beats_recency() -> None:
    runner = ExperimentRunner()
    result = runner.run(phase4_experiments()["temporal-old-signal"])
    by_id = {r.strategy_id: r for r in result.results}

    def mean_support(strategy: str) -> float:
        values = [
            m.value for m in by_id[strategy].metrics if m.name == "answer_support"
        ]
        return sum(values) / len(values)

    assert mean_support("oldest-first") > mean_support("recency")
