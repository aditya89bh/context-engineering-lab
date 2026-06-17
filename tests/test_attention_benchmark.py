"""Tests for the attention-source-allocation benchmark and presets."""

from __future__ import annotations

import pytest

from context_engineering_lab.attention import OracleAllocation, UniformAllocation
from context_engineering_lab.benchmarks.attention import (
    DECLARED_METRICS,
    AttentionBenchmark,
    AttentionConfig,
)
from context_engineering_lab.benchmarks.attention_presets import (
    all_attention_presets,
    balanced_sources,
    concentrated_signal,
    noisy_dominant_source,
)
from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY, group_sources
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.temporal import SALIENCE_KEY
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY


def _config(**overrides: object) -> AttentionConfig:
    base: dict[str, object] = {
        "benchmark_id": "test-attention",
        "version": "1.0",
        "construct": "unit test",
        "num_cases": 3,
        "num_sources": 4,
        "source_size": 6,
        "quality_imbalance": "high",
        "signal_concentration": "concentrated",
    }
    base.update(overrides)
    return AttentionConfig(**base)  # type: ignore[arg-type]


def test_generation_is_deterministic() -> None:
    bench = AttentionBenchmark(_config())
    first = bench.generate(7)
    second = bench.generate(7)
    assert [c.case_id for c in first] == [c.case_id for c in second]
    assert [[str(i.id) for i in c.candidates] for c in first] == [
        [str(i.id) for i in c.candidates] for c in second
    ]
    assert [
        [i.metadata.get(SALIENCE_KEY) for i in c.candidates] for c in first
    ] == [[i.metadata.get(SALIENCE_KEY) for i in c.candidates] for c in second]


def test_case_has_expected_sources_and_signal() -> None:
    bench = AttentionBenchmark(_config())
    case = bench.generate(1)[0]
    sources = group_sources(case.candidates)
    assert len(sources) == 4
    assert case.relevant_ids  # at least one signal item
    for item in case.candidates:
        assert item.source is not None
        assert SOURCE_QUALITY_KEY in item.metadata
        assert SALIENCE_KEY in item.metadata


def test_concentrated_signal_lands_in_one_source() -> None:
    case = AttentionBenchmark(_config()).generate(2)[0]
    sources = group_sources(case.candidates)
    signal_per_source = [
        sum(
            1
            for item in source.items
            if bool(item.metadata.get(ORACLE_RELEVANCE_KEY))
        )
        for source in sources
    ]
    # The richest source holds strictly more signal than any other.
    top = max(signal_per_source)
    assert signal_per_source.count(top) == 1


def test_noisy_dominant_adds_large_salient_low_quality_trap() -> None:
    bench = AttentionBenchmark(_config(noisy_dominant=True, dominant_size_factor=3))
    case = bench.generate(3)[0]
    sources = group_sources(case.candidates)
    assert len(sources) == 5  # 4 regular + 1 trap
    trap = max(sources, key=lambda s: s.size)
    assert trap.size == 6 * 3
    assert trap.mean_salience > 0.6  # shouts
    assert trap.quality < 0.3  # but is honestly low quality
    trap_signal = sum(
        1 for item in trap.items if bool(item.metadata.get(ORACLE_RELEVANCE_KEY))
    )
    assert trap_signal <= 1  # holds little signal


def test_evaluate_returns_declared_metrics() -> None:
    bench = AttentionBenchmark(_config())
    case = bench.generate(6)[0]
    budget = Budget(8, BudgetUnit.ITEMS)
    context = (
        OracleAllocation()
        .allocate(group_sources(case.candidates), case.task, budget)
        .context
    )
    metrics = bench.evaluate(case, context)
    assert set(metrics) == set(DECLARED_METRICS)
    assert set(metrics) == set(bench.declared_metrics)


def test_oracle_captures_at_least_as_much_as_uniform() -> None:
    bench = AttentionBenchmark(_config())
    case = bench.generate(8)[0]
    budget = Budget(8, BudgetUnit.ITEMS)
    sources = group_sources(case.candidates)
    oracle_ctx = OracleAllocation().allocate(sources, case.task, budget).context
    uniform_ctx = UniformAllocation().allocate(sources, case.task, budget).context
    oracle = bench.evaluate(case, oracle_ctx)
    uniform = bench.evaluate(case, uniform_ctx)
    assert oracle["signal_capture_rate"] >= uniform["signal_capture_rate"]


def test_config_validation() -> None:
    with pytest.raises(ValueError):
        _config(num_sources=1)
    with pytest.raises(ValueError):
        _config(source_size=0)
    with pytest.raises(ValueError):
        _config(quality_imbalance="medium")
    with pytest.raises(ValueError):
        _config(signal_concentration="clustered")
    with pytest.raises(ValueError):
        _config(budget_sweep=())


def test_presets_declare_metadata() -> None:
    presets = all_attention_presets()
    assert len(presets) == 3
    ids = {str(p.id) for p in presets}
    assert ids == {"balanced-sources", "concentrated-signal", "noisy-dominant-source"}
    for preset in presets:
        assert preset.version
        assert preset.config.construct
        assert preset.config.expected_failure_modes
        assert preset.budget_sweep


def test_named_presets_build() -> None:
    assert str(balanced_sources().id) == "balanced-sources"
    assert str(concentrated_signal().id) == "concentrated-signal"
    assert noisy_dominant_source().config.noisy_dominant is True
