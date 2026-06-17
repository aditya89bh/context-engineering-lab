"""Tests for the minimal temporal utilities."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.temporal import (
    SALIENCE_KEY,
    age,
    item_age,
    latest_timestamp,
    relative_age,
    salience_of,
)


def item(name: str, timestamp: float | None, **meta: object) -> Item:
    return Item(id=ItemId(name), content=name, length=1, timestamp=timestamp,
                metadata=meta)  # type: ignore[arg-type]


def test_age_is_now_minus_timestamp() -> None:
    assert age(3.0, 10.0) == 7.0
    assert age(10.0, 10.0) == 0.0


def test_item_age_uses_timestamp() -> None:
    assert item_age(item("a", 4.0), 10.0) == 6.0


def test_item_age_missing_defaults_to_infinity() -> None:
    assert item_age(item("a", None), 10.0) == float("inf")
    assert item_age(item("a", None), 10.0, missing=-1.0) == -1.0


def test_relative_age_normalizes_and_clamps() -> None:
    assert relative_age(5.0, 10.0, 10.0) == 0.5
    assert relative_age(10.0, 10.0, 10.0) == 0.0
    assert relative_age(-100.0, 10.0, 10.0) == 1.0


def test_relative_age_requires_positive_span() -> None:
    with pytest.raises(ValueError):
        relative_age(1.0, 2.0, 0.0)


def test_salience_default_and_read() -> None:
    assert salience_of(item("a", 1.0)) == 1.0
    assert salience_of(item("a", 1.0, salience=0.3)) == pytest.approx(0.3)


def test_salience_ignores_non_numeric_and_bool() -> None:
    assert salience_of(item("a", 1.0, **{SALIENCE_KEY: True})) == 1.0
    assert salience_of(item("a", 1.0, salience="high"), default=0.5) == 0.5


def test_latest_timestamp() -> None:
    items = [item("a", 1.0), item("b", 5.0), item("c", None)]
    assert latest_timestamp(items) == 5.0
    assert latest_timestamp([item("a", None)], default=-1.0) == -1.0
