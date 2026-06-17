"""Tests for Phase 9 dominance analysis."""

from __future__ import annotations

import pytest

from context_engineering_lab.synthesis.aggregation import aggregate_results
from context_engineering_lab.synthesis.dominance import (
    compare_pair,
    dominance_matrix,
    dominance_records,
    dominates,
    non_dominated_strategies,
    oriented_quality_cells,
)
from synthesis_helpers import simple_result


def _retention_aggregation():  # type: ignore[no-untyped-def]
    res = simple_result(
        "retention",
        {
            "good": {
                "answer_support": {(1, 2): 0.9},
                "harmful_retention_rate": {(1, 2): 0.1},
                "budget_utilization": {(1, 2): 1.0},
            },
            "bad": {
                "answer_support": {(1, 2): 0.5},
                "harmful_retention_rate": {(1, 2): 0.4},
                "budget_utilization": {(1, 2): 1.0},
            },
        },
    )
    return aggregate_results([res])


def test_oriented_cells_negate_cost_and_drop_neutral() -> None:
    agg = _retention_aggregation()
    cells = oriented_quality_cells(agg, "good")
    assert cells[("retention", "answer_support", 2)] == pytest.approx(0.9)
    assert cells[("retention", "harmful_retention_rate", 2)] == pytest.approx(-0.1)
    assert ("retention", "budget_utilization", 2) not in cells


def test_compare_pair_counts_wins() -> None:
    agg = _retention_aggregation()
    comparison = compare_pair(agg, "good", "bad")
    assert comparison.wins == 2
    assert comparison.losses == 0
    assert comparison.shared == 2


def test_dominates_and_frontier() -> None:
    agg = _retention_aggregation()
    assert dominates(agg, "good", "bad")
    assert not dominates(agg, "bad", "good")
    assert non_dominated_strategies(agg) == ["good"]


def test_dominance_records_rank_by_net() -> None:
    agg = _retention_aggregation()
    records = dominance_records(agg)
    assert records[0].strategy_id == "good"
    assert records[0].net == 2
    assert records[-1].strategy_id == "bad"
    assert records[-1].net == -2
    assert records[0].win_rate == pytest.approx(1.0)


def test_disjoint_benchmarks_are_both_non_dominated() -> None:
    a = simple_result("selection", {"x": {"answer_support": {(1, 2): 0.1}}})
    b = simple_result("attention", {"y": {"signal_capture_rate": {(1, 2): 0.9}}})
    agg = aggregate_results([a, b])
    assert non_dominated_strategies(agg) == ["x", "y"]
    matrix = dominance_matrix(agg)
    assert matrix[("x", "y")].shared == 0
