"""Tests for the compression-fact-preservation benchmark and presets."""

from __future__ import annotations

import pytest

from context_engineering_lab.benchmarks import facts
from context_engineering_lab.benchmarks.compression import (
    DECLARED_METRICS,
    CompressionBenchmark,
    CompressionConfig,
)
from context_engineering_lab.benchmarks.compression_presets import (
    all_compression_presets,
    dense_distractor_compression,
    easy_compression,
    late_signal_compression,
)
from context_engineering_lab.compression.no_compression import NoCompression
from context_engineering_lab.compression.oracle import OracleCompression
from context_engineering_lab.core.budget import Budget, BudgetUnit


def config(**overrides: object) -> CompressionConfig:
    base = {
        "benchmark_id": "test-compression",
        "version": "1.0",
        "construct": "test",
        "num_cases": 5,
        "content_length": 20,
        "num_required_facts": 2,
        "num_optional_facts": 2,
        "num_distractor_facts": 3,
        "target_position": "early",
    }
    base.update(overrides)
    return CompressionConfig(**base)  # type: ignore[arg-type]


def budget(limit: int) -> Budget:
    return Budget(limit, BudgetUnit.TOKENS)


def test_generation_is_deterministic() -> None:
    bench = CompressionBenchmark(config(target_position="distributed"))
    first = bench.generate(3)
    second = bench.generate(3)
    assert [c.candidates[0].content for c in first] == [
        c.candidates[0].content for c in second
    ]


def test_each_case_has_required_and_distractor_facts() -> None:
    bench = CompressionBenchmark(config())
    for case in bench.generate(1):
        content = case.candidates[0].content
        assert len(facts.required_facts(content)) == 2
        assert len(facts.target_facts(content)) == 4
        assert len(facts.distractor_facts(content)) == 3


def test_query_lists_required_facts() -> None:
    bench = CompressionBenchmark(config())
    for case in bench.generate(1):
        content = case.candidates[0].content
        assert set(case.task.query.split()) == facts.required_facts(content)


def test_early_position_places_targets_at_front() -> None:
    bench = CompressionBenchmark(
        config(target_position="early", num_distractor_facts=0)
    )
    for case in bench.generate(1):
        tokens = case.candidates[0].content.split()
        fact_positions = [i for i, t in enumerate(tokens) if facts.is_target_fact(t)]
        # Allowing for inserted sentence separators, targets are near the front.
        assert min(fact_positions) == 0


def test_late_position_places_targets_at_back() -> None:
    bench = CompressionBenchmark(config(target_position="late", num_distractor_facts=0))
    for case in bench.generate(1):
        tokens = [t for t in case.candidates[0].content.split() if t != "."]
        fact_positions = [i for i, t in enumerate(tokens) if facts.is_target_fact(t)]
        assert max(fact_positions) == len(tokens) - 1


def test_distractor_density_preset_has_more_distractors() -> None:
    sparse = easy_compression().config.num_distractor_facts
    dense = dense_distractor_compression().config.num_distractor_facts
    assert dense > sparse


def test_evaluate_returns_declared_metrics() -> None:
    bench = CompressionBenchmark(config())
    case = bench.generate(1)[0]
    result = OracleCompression().compress(case.candidates, case.task, budget(8))
    scores = bench.evaluate(case, result.context)
    assert set(scores) == set(DECLARED_METRICS)


def test_oracle_preserves_all_targets_and_drops_distractors() -> None:
    bench = CompressionBenchmark(config())
    total_info = 0.0
    total_distractor = 0.0
    cases = bench.generate(1)
    for case in cases:
        context = (
            OracleCompression().compress(case.candidates, case.task, budget(16)).context
        )
        scores = bench.evaluate(case, context)
        total_info += scores["information_retention"]
        total_distractor += scores["distractor_retention"]
    assert total_info == float(len(cases))  # full retention
    assert total_distractor == 0.0  # no distractors retained


def test_no_compression_overflows_but_retains_everything() -> None:
    bench = CompressionBenchmark(config())
    case = bench.generate(1)[0]
    context = NoCompression().compress(case.candidates, case.task, budget(4)).context
    scores = bench.evaluate(case, context)
    assert scores["information_retention"] == 1.0
    assert scores["compression_ratio"] == 1.0
    assert scores["budget_utilization"] > 1.0


def test_presets_have_distinct_ids_and_constructs() -> None:
    presets = all_compression_presets()
    ids = {str(p.id) for p in presets}
    assert ids == {
        "easy-compression",
        "late-signal-compression",
        "dense-distractor-compression",
    }
    for preset in presets:
        assert preset.config.construct
        assert preset.config.expected_failure_modes
        assert preset.budget_sweep


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        config(num_cases=0)
    with pytest.raises(ValueError):
        config(target_position="sideways")
    with pytest.raises(ValueError):
        config(content_length=2, num_distractor_facts=10)


def test_late_signal_preset_targets_are_late() -> None:
    assert late_signal_compression().config.target_position == "late"
