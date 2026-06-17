"""Tests for temporal metric functions."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.temporal_metrics import (
    age_of_selected_context,
    relevant_age_gap,
    stale_selection_rate,
    temporal_relevance,
)


def ids(*names: str) -> frozenset[ItemId]:
    return frozenset(ItemId(n) for n in names)


def test_stale_selection_rate() -> None:
    assert stale_selection_rate(ids("a", "b"), ids("b")) == 0.5
    assert stale_selection_rate(ids("a"), ids("x")) == 0.0


def test_stale_selection_rate_undefined_for_empty_selection() -> None:
    with pytest.raises(ValueError):
        stale_selection_rate(ids(), ids("a"))


def test_age_of_selected_context() -> None:
    assert age_of_selected_context([2.0, 4.0], 10.0) == pytest.approx(0.3)


def test_age_of_selected_context_undefined_cases() -> None:
    with pytest.raises(ValueError):
        age_of_selected_context([], 10.0)
    with pytest.raises(ValueError):
        age_of_selected_context([1.0], 0.0)


def test_relevant_age_gap_zero_when_aligned() -> None:
    assert relevant_age_gap([4.0, 6.0], [5.0, 5.0], 10.0) == pytest.approx(0.0)


def test_relevant_age_gap_measures_distance() -> None:
    assert relevant_age_gap([10.0], [0.0], 10.0) == pytest.approx(1.0)


def test_relevant_age_gap_undefined_cases() -> None:
    with pytest.raises(ValueError):
        relevant_age_gap([], [1.0], 10.0)
    with pytest.raises(ValueError):
        relevant_age_gap([1.0], [], 10.0)
    with pytest.raises(ValueError):
        relevant_age_gap([1.0], [1.0], 0.0)


def test_temporal_relevance_counts_in_band() -> None:
    assert temporal_relevance([1.0, 5.0, 9.0], 4.0, 6.0) == pytest.approx(1 / 3)
    assert temporal_relevance([5.0, 5.0], 4.0, 6.0) == 1.0


def test_temporal_relevance_undefined_cases() -> None:
    with pytest.raises(ValueError):
        temporal_relevance([], 0.0, 1.0)
    with pytest.raises(ValueError):
        temporal_relevance([1.0], 6.0, 4.0)
