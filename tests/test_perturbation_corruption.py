"""Tests for Phase 10 corruption perturbations."""

from __future__ import annotations

import random

from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.temporal import SALIENCE_KEY
from context_engineering_lab.perturbations.corruption import (
    salience_corruption,
    source_quality_corruption,
)
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY
from tests.perturbation_helpers import sample_case


def _by_id(case: Case, item_id: str) -> Item:
    return next(item for item in case.candidates if item.id == ItemId(item_id))


def _num(value: JsonValue) -> float:
    assert isinstance(value, (int, float)) and not isinstance(value, bool)
    return float(value)


def test_salience_corruption_adds_no_items() -> None:
    original = sample_case()
    result = salience_corruption().apply(original, random.Random(0))
    assert result.items_added == 0
    assert result.items_modified == len(original.candidates)
    assert len(result.case.candidates) == len(original.candidates)


def test_salience_corruption_misleads_signal() -> None:
    result = salience_corruption(intensity=1.0).apply(sample_case(), random.Random(0))
    relevant = _by_id(result.case, "rel")
    irrelevant = _by_id(result.case, "old")
    assert _num(relevant.metadata[SALIENCE_KEY]) < 0.2
    assert _num(irrelevant.metadata[SALIENCE_KEY]) > 0.8


def test_source_quality_corruption_misleads_signal() -> None:
    result = source_quality_corruption(intensity=1.0).apply(
        sample_case(), random.Random(0)
    )
    relevant = _by_id(result.case, "rel")
    irrelevant = _by_id(result.case, "old")
    assert _num(relevant.metadata[SOURCE_QUALITY_KEY]) < 0.2
    assert _num(irrelevant.metadata[SOURCE_QUALITY_KEY]) > 0.8


def test_corruption_preserves_ground_truth() -> None:
    original = sample_case()
    result = salience_corruption().apply(original, random.Random(1))
    assert result.case.relevant_ids == original.relevant_ids
    assert result.case.required_ids == original.required_ids
    for item in result.case.candidates:
        before = _by_id(original, str(item.id))
        key = ORACLE_RELEVANCE_KEY
        assert item.metadata[key] == before.metadata[key]


def test_zero_intensity_is_near_identity() -> None:
    original = sample_case()
    result = salience_corruption(intensity=0.0).apply(original, random.Random(2))
    for item in result.case.candidates:
        before = _by_id(original, str(item.id))
        assert _num(item.metadata[SALIENCE_KEY]) == _num(before.metadata[SALIENCE_KEY])


def test_corruption_is_deterministic() -> None:
    original = sample_case()
    first = source_quality_corruption().apply(original, random.Random(3)).case
    second = source_quality_corruption().apply(original, random.Random(3)).case
    assert [i.metadata[SOURCE_QUALITY_KEY] for i in first.candidates] == [
        i.metadata[SOURCE_QUALITY_KEY] for i in second.candidates
    ]
