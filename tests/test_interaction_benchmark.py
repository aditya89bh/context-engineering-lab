"""Tests for the interaction benchmark generator and presets."""

from __future__ import annotations

import pytest

from context_engineering_lab.benchmarks.interaction import (
    DECLARED_METRICS,
    InteractionBenchmark,
    InteractionConfig,
)
from context_engineering_lab.benchmarks.interaction_presets import (
    all_interaction_presets,
    balanced_interaction,
    memory_pressure,
    noisy_context,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.context import Context
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection


def _config(**overrides: object) -> InteractionConfig:
    base: dict[str, object] = {
        "benchmark_id": "test-interaction",
        "version": "1.0",
        "construct": "unit test",
        "num_cases": 3,
        "num_sources": 3,
        "num_relevant": 6,
        "num_required": 2,
        "num_stale": 3,
        "num_harmful": 4,
        "num_distractor": 5,
        "source_imbalance": "high",
        "signal_concentration": "spread",
    }
    base.update(overrides)
    return InteractionConfig(**base)  # type: ignore[arg-type]


def test_generation_is_deterministic() -> None:
    benchmark = InteractionBenchmark(_config())
    first = benchmark.generate(7)
    second = benchmark.generate(7)
    assert [c.case_id for c in first] == [c.case_id for c in second]
    for a, b in zip(first, second, strict=True):
        assert [(i.id, i.timestamp, i.metadata) for i in a.candidates] == [
            (i.id, i.timestamp, i.metadata) for i in b.candidates
        ]


def test_different_seeds_differ() -> None:
    benchmark = InteractionBenchmark(_config())
    one = benchmark.generate(1)[0]
    two = benchmark.generate(2)[0]
    assert [i.metadata for i in one.candidates] != [
        i.metadata for i in two.candidates
    ]


def test_case_has_all_item_kinds() -> None:
    benchmark = InteractionBenchmark(_config())
    case = benchmark.generate(1)[0]
    assert len(case.candidates) == benchmark.config.memory_size
    assert len(case.relevant_ids) == 6
    assert len(case.required_ids) == 2
    assert case.required_ids <= case.relevant_ids


def test_sources_and_signals_are_present() -> None:
    benchmark = InteractionBenchmark(_config())
    case = benchmark.generate(1)[0]
    sources = {item.source for item in case.candidates}
    assert len([s for s in sources if s is not None]) >= 1
    for item in case.candidates:
        assert "salience" in item.metadata
        assert "frequency" in item.metadata
        assert "source_quality" in item.metadata


def test_relevant_items_carry_query_terms() -> None:
    benchmark = InteractionBenchmark(_config())
    case = benchmark.generate(1)[0]
    selector = KeywordOverlapSelection()
    context = selector.select(
        case.candidates, case.task, Budget(6, BudgetUnit.ITEMS)
    )
    # Relevant (and the harmful traps) carry the query terms, so a keyword
    # selector lands on the on-topic items, not the off-topic stale/distractors.
    overlap = set(context.item_ids) & case.relevant_ids
    assert overlap


def test_evaluate_reports_declared_metrics() -> None:
    benchmark = InteractionBenchmark(_config())
    case = benchmark.generate(1)[0]
    context = Context(
        items=case.candidates[:4], budget=Budget(4, BudgetUnit.ITEMS)
    )
    scores = benchmark.evaluate(case, context)
    assert set(scores) == set(DECLARED_METRICS)
    for value in scores.values():
        assert isinstance(value, float)


def test_evaluate_handles_empty_context() -> None:
    benchmark = InteractionBenchmark(_config())
    case = benchmark.generate(1)[0]
    context = Context(items=(), budget=Budget(4, BudgetUnit.ITEMS))
    scores = benchmark.evaluate(case, context)
    assert scores["selection_precision"] == 0.0
    assert scores["stale_selection_rate"] == 0.0


def test_evaluate_zero_harmful_rate_without_harmful_items() -> None:
    benchmark = InteractionBenchmark(_config(num_harmful=0))
    case = benchmark.generate(1)[0]
    context = Context(
        items=case.candidates[:4], budget=Budget(4, BudgetUnit.ITEMS)
    )
    assert benchmark.evaluate(case, context)["harmful_retention_rate"] == 0.0


def test_invalid_config_rejected() -> None:
    with pytest.raises(ValueError, match="num_sources"):
        _config(num_sources=1)
    with pytest.raises(ValueError, match="num_required"):
        _config(num_required=99)
    with pytest.raises(ValueError, match="signal_concentration"):
        _config(signal_concentration="sometimes")


def test_presets_are_named_and_versioned() -> None:
    presets = all_interaction_presets()
    assert {str(p.id) for p in presets} == {
        "balanced-interaction",
        "memory-pressure",
        "noisy-context",
    }
    for preset in presets:
        assert preset.version == "1.0"
        assert preset.config.expected_failure_modes


def test_preset_constructs_differ() -> None:
    balanced = balanced_interaction().config
    assert memory_pressure().config.num_harmful > balanced.num_harmful
    assert noisy_context().config.num_stale > balanced.num_stale
