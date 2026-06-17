"""Tests for the naturalistic-scenario metrics."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.naturalistic_metrics import (
    conflict_selection_rate,
    current_truth_support,
    superseded_fact_retention,
)


def _ids(*names: str) -> frozenset[ItemId]:
    return frozenset(ItemId(name) for name in names)


def test_current_truth_support_is_recall_over_current() -> None:
    current = _ids("a", "b", "c", "d")
    selected = _ids("a", "b", "x")
    assert current_truth_support(current, selected) == 0.5


def test_current_truth_support_undefined_without_current() -> None:
    with pytest.raises(ValueError):
        current_truth_support(frozenset(), _ids("a"))


def test_superseded_fact_retention_counts_kept_superseded() -> None:
    superseded = _ids("o1", "o2", "o3", "o4")
    selected = _ids("o1", "current")
    assert superseded_fact_retention(superseded, selected) == 0.25


def test_superseded_fact_retention_undefined_without_superseded() -> None:
    with pytest.raises(ValueError):
        superseded_fact_retention(frozenset(), _ids("a"))


def test_conflict_selection_rate_is_share_of_selection() -> None:
    selected = _ids("a", "b", "k1", "k2")
    conflicting = _ids("k1", "k2", "k3")
    assert conflict_selection_rate(selected, conflicting) == 0.5


def test_conflict_selection_rate_zero_when_no_conflict_selected() -> None:
    assert conflict_selection_rate(_ids("a", "b"), _ids("k")) == 0.0


def test_conflict_selection_rate_undefined_for_empty_selection() -> None:
    with pytest.raises(ValueError):
        conflict_selection_rate(frozenset(), _ids("k"))
