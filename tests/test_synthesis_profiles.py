"""Tests for Phase 9 strategy profiles."""

from __future__ import annotations

import pytest

from context_engineering_lab.synthesis.aggregation import aggregate_results
from context_engineering_lab.synthesis.profiles import (
    generate_profile,
    generate_profiles,
    is_oracle_id,
    oracle_distance_for,
    oracle_primary_score,
    primary_scores,
)
from synthesis_helpers import simple_result


def _aggregation():  # type: ignore[no-untyped-def]
    selection = simple_result(
        "selection",
        {
            "recency": {"answer_support": {(1, 2): 0.4, (1, 4): 0.6}},
            "oracle": {"answer_support": {(1, 2): 1.0, (1, 4): 1.0}},
        },
    )
    attention = simple_result(
        "attention",
        {
            "recency": {"signal_capture_rate": {(1, 2): 0.2, (1, 4): 0.2}},
            "oracle-allocation": {"signal_capture_rate": {(1, 2): 0.9, (1, 4): 0.9}},
        },
    )
    return aggregate_results([selection, attention])


def test_primary_scores_uses_primary_metric() -> None:
    agg = _aggregation()
    scores = primary_scores(agg, "recency")
    assert scores["selection"] == ("answer_support", pytest.approx(0.5))
    assert scores["attention"] == ("signal_capture_rate", pytest.approx(0.2))


def test_profile_strengths_and_weaknesses() -> None:
    agg = _aggregation()
    profile = generate_profile(agg, "recency")
    assert profile.strengths[0].benchmark_id == "selection"
    assert profile.weaknesses[0].benchmark_id == "attention"
    assert profile.mean_primary == pytest.approx((0.5 + 0.2) / 2)


def test_profile_best_and_worst_budgets() -> None:
    agg = _aggregation()
    profile = generate_profile(agg, "recency")
    assert profile.best_budgets[0].budget_limit == 4
    assert profile.worst_budgets[0].budget_limit == 2
    assert profile.best_budgets[0].benchmark_count == 2


def test_oracle_detection_and_distance() -> None:
    agg = _aggregation()
    assert is_oracle_id("oracle-allocation")
    assert not is_oracle_id("recency")
    assert oracle_primary_score(agg, "selection") == pytest.approx(1.0)
    assert oracle_distance_for(agg, "recency") == pytest.approx((0.5 + 0.7) / 2)


def test_profile_records_oracle_distance() -> None:
    agg = _aggregation()
    profile = generate_profile(agg, "recency")
    assert profile.oracle_distance == pytest.approx(0.6)
    oracle_profile = generate_profile(agg, "oracle")
    assert oracle_profile.oracle_distance == pytest.approx(0.0)


def test_generate_profiles_covers_all_strategies() -> None:
    agg = _aggregation()
    profiles = generate_profiles(agg)
    assert {p.strategy_id for p in profiles} == {
        "recency",
        "oracle",
        "oracle-allocation",
    }
