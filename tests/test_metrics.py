"""Tests for selection metric functions."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.metrics import (
    answer_support,
    selection_precision,
    selection_recall,
)


def ids(*names: str) -> frozenset[ItemId]:
    return frozenset(ItemId(n) for n in names)


def test_selection_precision() -> None:
    assert selection_precision(ids("a", "b"), ids("a", "x")) == 0.5
    assert selection_precision(ids("a"), ids("a")) == 1.0


def test_selection_precision_undefined_for_empty_selection() -> None:
    with pytest.raises(ValueError):
        selection_precision(ids("a"), ids())


def test_selection_recall() -> None:
    assert selection_recall(ids("a", "b"), ids("a")) == 0.5
    assert selection_recall(ids("a", "b"), ids("a", "b", "c")) == 1.0


def test_selection_recall_undefined_without_relevant() -> None:
    with pytest.raises(ValueError):
        selection_recall(ids(), ids("a"))


def test_answer_support() -> None:
    assert answer_support(ids("a", "b"), ids("a", "b", "c")) == 1.0
    assert answer_support(ids("a", "b"), ids("a")) == 0.0


def test_answer_support_undefined_without_required() -> None:
    with pytest.raises(ValueError):
        answer_support(ids(), ids("a"))
