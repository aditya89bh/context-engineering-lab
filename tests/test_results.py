"""Tests for result models, metadata, and round-trip serialization."""

from __future__ import annotations

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.metadata import (
    build_run_metadata,
    compute_run_id,
)
from context_engineering_lab.core.results import (
    ExperimentResult,
    MetricValue,
    StrategyRunResult,
)


def make_result() -> ExperimentResult:
    budgets = (Budget(2, BudgetUnit.ITEMS), Budget(4, BudgetUnit.ITEMS))
    metadata = build_run_metadata(
        experiment_id="exp",
        benchmark_id="bench",
        benchmark_version="1.0",
        strategy_ids=("recency",),
        seeds=(1, 2),
        budgets=budgets,
        code_version="0.0.0",
    )
    metric = MetricValue(
        name="answer_support",
        value=0.5,
        seed=1,
        budget_limit=2,
        budget_unit="items",
        sample_size=10,
        stddev=0.1,
    )
    run = StrategyRunResult(strategy_id="recency", metrics=(metric,))
    return ExperimentResult(metadata=metadata, results=(run,))


def test_run_id_is_deterministic() -> None:
    budgets = (Budget(2, BudgetUnit.ITEMS),)
    first = compute_run_id("e", "b", "1.0", ("recency",), (1, 2), budgets)
    second = compute_run_id("e", "b", "1.0", ("recency",), (1, 2), budgets)
    assert first == second


def test_run_id_changes_with_config() -> None:
    budgets = (Budget(2, BudgetUnit.ITEMS),)
    base = compute_run_id("e", "b", "1.0", ("recency",), (1,), budgets)
    other = compute_run_id("e", "b", "1.0", ("recency",), (2,), budgets)
    assert base != other


def test_experiment_result_round_trip() -> None:
    result = make_result()
    restored = ExperimentResult.from_dict(result.to_dict())
    assert restored == result
