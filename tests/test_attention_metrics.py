"""Tests for attention-allocation metric functions."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.attention_metrics import (
    allocation_efficiency,
    signal_capture_rate,
    source_coverage,
    wasted_attention_rate,
)
from context_engineering_lab.core.ids import ItemId


def ids(*names: str) -> frozenset[ItemId]:
    return frozenset(ItemId(n) for n in names)


def test_allocation_efficiency() -> None:
    assert allocation_efficiency(ids("g1", "g2"), ids("g1", "x")) == 0.5
    assert allocation_efficiency(ids("g1"), ids("g1")) == 1.0


def test_allocation_efficiency_undefined_for_empty_selection() -> None:
    with pytest.raises(ValueError):
        allocation_efficiency(ids("g1"), ids())


def test_signal_capture_rate() -> None:
    assert signal_capture_rate(ids("g1", "g2", "g3", "g4"), ids("g1", "g2")) == 0.5


def test_signal_capture_rate_undefined_without_signal() -> None:
    with pytest.raises(ValueError):
        signal_capture_rate(ids(), ids("g1"))


def test_wasted_attention_rate_counts_distractors_and_slack() -> None:
    # 1 of 2 signal captured, budget 4 -> (4 - 1) / 4
    assert wasted_attention_rate(ids("g1", "g2"), ids("g1", "x"), 4) == 0.75
    # all signal captured, budget equals capture -> 0 waste
    assert wasted_attention_rate(ids("g1", "g2"), ids("g1", "g2"), 2) == 0.0


def test_wasted_attention_rate_undefined_for_nonpositive_budget() -> None:
    with pytest.raises(ValueError):
        wasted_attention_rate(ids("g1"), ids("g1"), 0)


def test_source_coverage() -> None:
    assert source_coverage({"s0", "s1"}, {"s0", "s1", "s2", "s3"}) == 0.5
    assert source_coverage({"s0"}, {"s0"}) == 1.0


def test_source_coverage_undefined_without_sources() -> None:
    with pytest.raises(ValueError):
        source_coverage(set(), set())
