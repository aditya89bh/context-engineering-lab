"""Tests for Phase 9 failure analysis."""

from __future__ import annotations

import pytest

from context_engineering_lab.synthesis.aggregation import (
    Aggregation,
    aggregate_results,
)
from context_engineering_lab.synthesis.failure import (
    FailureMode,
    analyze_failures,
    benchmark_failures,
    budget_failures,
    metric_degradation,
)
from tests.synthesis_helpers import simple_result


def _aggregation() -> Aggregation:
    res = simple_result(
        "selection",
        {
            "oracle": {"answer_support": {(1, 2): 1.0, (1, 4): 1.0}},
            "weak": {"answer_support": {(1, 2): 0.2, (1, 4): 0.3}},
            "degrader": {
                "answer_support": {(1, 2): 0.9, (1, 4): 0.6},
                "harmful_retention_rate": {(1, 2): 0.1, (1, 4): 0.4},
            },
        },
    )
    return aggregate_results([res])


def test_budget_failures_flag_tight_collapse() -> None:
    agg = _aggregation()
    failures = budget_failures(agg)
    strategies = {f.strategy_id for f in failures}
    assert strategies == {"weak"}
    assert failures[0].mode is FailureMode.BUDGET_FAILURE


def test_benchmark_failures_flag_oracle_gap() -> None:
    agg = _aggregation()
    failures = benchmark_failures(agg)
    assert {f.strategy_id for f in failures} == {"weak"}
    assert failures[0].severity == pytest.approx(0.75)


def test_metric_degradation_detects_quality_and_cost() -> None:
    agg = _aggregation()
    failures = metric_degradation(agg)
    by_metric = {f.metric for f in failures if f.strategy_id == "degrader"}
    assert by_metric == {"answer_support", "harmful_retention_rate"}
    for failure in failures:
        assert failure.severity == pytest.approx(0.3)


def test_oracle_is_never_flagged() -> None:
    agg = _aggregation()
    everything = analyze_failures(agg)
    assert all(f.strategy_id != "oracle" for f in everything)
    assert {f.mode for f in everything} == {
        FailureMode.BUDGET_FAILURE,
        FailureMode.BENCHMARK_FAILURE,
        FailureMode.METRIC_DEGRADATION,
    }
