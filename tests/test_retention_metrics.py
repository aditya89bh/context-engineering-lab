"""Tests for retention (forgetting) metric functions."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.retention_metrics import (
    forgetting_efficiency,
    harmful_retention_rate,
    memory_budget_utilization,
    retention_precision,
    retention_recall,
    useful_retention_rate,
)


def ids(*names: str) -> frozenset[ItemId]:
    return frozenset(ItemId(n) for n in names)


def test_retention_precision() -> None:
    assert retention_precision(ids("u1", "u2"), ids("u1", "x")) == 0.5
    assert retention_precision(ids("u1"), ids("u1")) == 1.0


def test_retention_precision_undefined_for_empty_retention() -> None:
    with pytest.raises(ValueError):
        retention_precision(ids("u1"), ids())


def test_retention_recall_over_required() -> None:
    assert retention_recall(ids("r1", "r2"), ids("r1")) == 0.5


def test_retention_recall_undefined_without_required() -> None:
    with pytest.raises(ValueError):
        retention_recall(ids(), ids("r1"))


def test_useful_retention_rate() -> None:
    assert useful_retention_rate(ids("u1", "u2", "u3", "u4"), ids("u1", "u2")) == 0.5


def test_useful_retention_rate_undefined_without_useful() -> None:
    with pytest.raises(ValueError):
        useful_retention_rate(ids(), ids("u1"))


def test_harmful_retention_rate() -> None:
    assert harmful_retention_rate(ids("h1", "h2"), ids("h1", "u1")) == 0.5


def test_harmful_retention_rate_undefined_without_harmful() -> None:
    with pytest.raises(ValueError):
        harmful_retention_rate(ids(), ids("h1"))


def test_memory_budget_utilization() -> None:
    assert memory_budget_utilization(4, 8) == 0.5
    assert memory_budget_utilization(16, 8) == 2.0


def test_memory_budget_utilization_undefined_cases() -> None:
    with pytest.raises(ValueError):
        memory_budget_utilization(1, 0)
    with pytest.raises(ValueError):
        memory_budget_utilization(-1, 8)


def test_forgetting_efficiency_is_difference_of_rates() -> None:
    useful = ids("u1", "u2")
    harmful = ids("h1", "h2")
    retained = ids("u1", "u2", "h1")
    assert forgetting_efficiency(useful, harmful, retained) == pytest.approx(0.5)


def test_forgetting_efficiency_handles_empty_harmful() -> None:
    assert forgetting_efficiency(ids("u1", "u2"), ids(), ids("u1")) == pytest.approx(
        0.5
    )


def test_forgetting_efficiency_undefined_without_useful() -> None:
    with pytest.raises(ValueError):
        forgetting_efficiency(ids(), ids("h1"), ids("h1"))
