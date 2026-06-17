"""Tests for the interaction (composition) metric functions."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.interaction_metrics import (
    compensation_effect,
    degradation_rate,
    interaction_gain,
    pipeline_efficiency,
)


def _ids(*names: str) -> frozenset[ItemId]:
    return frozenset(ItemId(name) for name in names)


def test_pipeline_efficiency_is_captured_per_budget() -> None:
    value = pipeline_efficiency(_ids("a", "b"), _ids("a", "c"), budget_limit=4)
    assert value == pytest.approx(0.25)


def test_pipeline_efficiency_rejects_non_positive_budget() -> None:
    with pytest.raises(ValueError, match="non-positive budget"):
        pipeline_efficiency(_ids("a"), _ids("a"), budget_limit=0)


def test_interaction_gain_is_signed_difference() -> None:
    assert interaction_gain(0.8, 0.5) == pytest.approx(0.3)
    assert interaction_gain(0.4, 0.6) == pytest.approx(-0.2)


def test_degradation_rate_is_relative_drop() -> None:
    assert degradation_rate(0.5, 0.8) == pytest.approx(0.375)


def test_degradation_rate_is_zero_when_pipeline_wins() -> None:
    assert degradation_rate(0.9, 0.8) == 0.0


def test_degradation_rate_rejects_non_positive_baseline() -> None:
    with pytest.raises(ValueError, match="non-positive baseline"):
        degradation_rate(0.5, 0.0)


def test_compensation_effect_margin_over_best_part() -> None:
    assert compensation_effect(0.7, [0.5, 0.6]) == pytest.approx(0.1)
    assert compensation_effect(0.55, [0.5, 0.6]) == pytest.approx(-0.05)


def test_compensation_effect_requires_constituents() -> None:
    with pytest.raises(ValueError, match="at least one constituent"):
        compensation_effect(0.7, [])
