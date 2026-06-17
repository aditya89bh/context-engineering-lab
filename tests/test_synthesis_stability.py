"""Tests for Phase 9 stability analysis."""

from __future__ import annotations

import pytest

from context_engineering_lab.synthesis.aggregation import aggregate_results
from context_engineering_lab.synthesis.stability import (
    budget_sensitivity,
    ranking_volatilities,
    ranking_volatility,
    seed_variance,
    stability_reports,
    strategy_stability,
)
from synthesis_helpers import simple_result


def _seeded_aggregation():  # type: ignore[no-untyped-def]
    res = simple_result(
        "selection",
        {
            "a": {
                "answer_support": {
                    (1, 2): 0.2,
                    (2, 2): 0.4,
                    (1, 4): 0.8,
                    (2, 4): 1.0,
                }
            }
        },
    )
    return aggregate_results([res])


def test_seed_variance_and_budget_sensitivity() -> None:
    agg = _seeded_aggregation()
    assert seed_variance(agg, "a") == pytest.approx(0.1)
    assert budget_sensitivity(agg, "a") == pytest.approx(0.6)
    report = strategy_stability(agg, "a")
    assert report.seed_variance == pytest.approx(0.1)


def test_ranking_volatility_detects_flip() -> None:
    flipped = simple_result(
        "selection",
        {
            "a": {"answer_support": {(1, 2): 0.3, (1, 4): 0.9}},
            "b": {"answer_support": {(1, 2): 0.5, (1, 4): 0.6}},
        },
    )
    agg = aggregate_results([flipped])
    volatility = ranking_volatility(agg, "selection")
    assert volatility is not None
    assert volatility.volatility == pytest.approx(1.0)


def test_ranking_volatility_stable_order() -> None:
    stable = simple_result(
        "temporal",
        {
            "a": {"answer_support": {(1, 2): 0.2, (1, 4): 0.3}},
            "b": {"answer_support": {(1, 2): 0.5, (1, 4): 0.6}},
        },
    )
    agg = aggregate_results([stable])
    volatility = ranking_volatility(agg, "temporal")
    assert volatility is not None
    assert volatility.volatility == pytest.approx(0.0)


def test_reports_and_volatilities_cover_everything() -> None:
    agg = _seeded_aggregation()
    assert {r.strategy_id for r in stability_reports(agg)} == {"a"}
    assert {v.benchmark_id for v in ranking_volatilities(agg)} == {"selection"}
