"""Tests for Phase 10 injection perturbations."""

from __future__ import annotations

import random

from context_engineering_lab.benchmarks.naturalistic.records import (
    CONFLICTING_KEY,
    SUPERSEDED_KEY,
)
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.temporal import STALE_KEY
from context_engineering_lab.perturbations.injection import (
    contradiction_injection,
    distractor_injection,
    stale_amplification,
)
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY
from tests.perturbation_helpers import sample_case


def _added(case: Case, original: Case) -> list[Item]:
    original_ids = {item.id for item in original.candidates}
    return [item for item in case.candidates if item.id not in original_ids]


def test_distractor_injection_adds_count_items() -> None:
    pert = distractor_injection(count=5)
    original = sample_case()
    result = pert.apply(original, random.Random(0))
    assert result.items_added == 5
    assert result.items_modified == 0
    assert len(result.case.candidates) == len(original.candidates) + 5


def test_distractor_injection_preserves_ground_truth() -> None:
    original = sample_case()
    result = distractor_injection(count=4).apply(original, random.Random(1))
    assert result.case.relevant_ids == original.relevant_ids
    assert result.case.required_ids == original.required_ids
    for item in _added(result.case, original):
        assert item.metadata[ORACLE_RELEVANCE_KEY] is False


def test_distractor_content_carries_query_terms() -> None:
    original = sample_case()
    result = distractor_injection(count=3).apply(original, random.Random(2))
    for item in _added(result.case, original):
        assert "deploy" in item.content


def test_contradiction_injection_flags_conflicting() -> None:
    original = sample_case()
    result = contradiction_injection(count=3).apply(original, random.Random(3))
    added = _added(result.case, original)
    assert len(added) == 3
    for item in added:
        assert item.metadata[CONFLICTING_KEY] is True
        assert item.metadata[ORACLE_RELEVANCE_KEY] is False


def test_stale_amplification_flags_stale_and_superseded() -> None:
    original = sample_case()
    result = stale_amplification(count=4).apply(original, random.Random(4))
    added = _added(result.case, original)
    assert len(added) == 4
    for item in added:
        assert item.metadata[STALE_KEY] is True
        assert item.metadata[SUPERSEDED_KEY] is True


def test_stale_amplification_echoes_existing_stale_content() -> None:
    original = sample_case()
    result = stale_amplification(count=2).apply(original, random.Random(5))
    added = _added(result.case, original)
    assert all(item.content == "deploy rollback procedure legacy" for item in added)


def test_injection_is_deterministic() -> None:
    original = sample_case()
    first = distractor_injection(count=4).apply(original, random.Random(7)).case
    second = distractor_injection(count=4).apply(original, random.Random(7)).case
    assert [(i.id, i.content, i.metadata) for i in first.candidates] == [
        (i.id, i.content, i.metadata) for i in second.candidates
    ]


def test_injected_ids_are_unique() -> None:
    original = sample_case()
    result = distractor_injection(count=6).apply(original, random.Random(8))
    ids = [item.id for item in result.case.candidates]
    assert len(ids) == len(set(ids))
