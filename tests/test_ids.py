"""Tests for typed identifiers."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from context_engineering_lab.core.ids import BenchmarkId, ItemId, StrategyId


def test_identifier_str_and_value() -> None:
    item = ItemId("doc-1")
    assert item.value == "doc-1"
    assert str(item) == "doc-1"


def test_identifier_rejects_empty() -> None:
    with pytest.raises(ValueError):
        ItemId("")
    with pytest.raises(ValueError):
        ItemId("   ")


def test_identifier_is_frozen() -> None:
    item = ItemId("doc-1")
    with pytest.raises(FrozenInstanceError):
        item.value = "other"  # type: ignore[misc]


def test_distinct_types_compare_unequal() -> None:
    # Different identifier types never compare equal, even with the same value.
    left: object = ItemId("x")
    right: object = StrategyId("x")
    assert left != right
    assert ItemId("x") == ItemId("x")


def test_identifiers_are_hashable_by_type_and_value() -> None:
    assert hash(ItemId("x")) == hash(ItemId("x"))
    assert {ItemId("a"), BenchmarkId("a")} == {ItemId("a"), BenchmarkId("a")}
