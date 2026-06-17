"""Tests for the retention-utility-preservation benchmark and presets."""

from __future__ import annotations

import pytest

from context_engineering_lab.benchmarks.retention import (
    DECLARED_METRICS,
    HARMFUL_KEY,
    REQUIRED_KEY,
    RetentionBenchmark,
    RetentionConfig,
)
from context_engineering_lab.benchmarks.retention_presets import (
    all_retention_presets,
    harmful_memory,
    low_noise_retention,
    stale_accumulation,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.temporal import SALIENCE_KEY, STALE_KEY
from context_engineering_lab.retention import OracleRetentionPolicy, RetainAllPolicy
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY


def _config(**overrides: object) -> RetentionConfig:
    base: dict[str, object] = {
        "benchmark_id": "test-retention",
        "version": "1.0",
        "construct": "unit test",
        "num_cases": 3,
        "num_useful": 4,
        "num_required": 2,
        "num_stale": 3,
        "num_harmful": 3,
        "num_neutral": 6,
        "noise": "low",
    }
    base.update(overrides)
    return RetentionConfig(**base)  # type: ignore[arg-type]


def test_generation_is_deterministic() -> None:
    bench = RetentionBenchmark(_config())
    first = bench.generate(7)
    second = bench.generate(7)
    assert [c.case_id for c in first] == [c.case_id for c in second]
    assert [tuple(str(i.id) for i in c.candidates) for c in first] == [
        tuple(str(i.id) for i in c.candidates) for c in second
    ]
    assert [
        [i.metadata.get(SALIENCE_KEY) for i in c.candidates] for c in first
    ] == [[i.metadata.get(SALIENCE_KEY) for i in c.candidates] for c in second]


def test_case_has_expected_kind_counts() -> None:
    bench = RetentionBenchmark(_config())
    case = bench.generate(1)[0]
    assert len(case.candidates) == bench.config.memory_size
    useful = [i for i in case.candidates if i.metadata.get(ORACLE_RELEVANCE_KEY)]
    harmful = [i for i in case.candidates if i.metadata.get(HARMFUL_KEY)]
    stale = [i for i in case.candidates if i.metadata.get(STALE_KEY)]
    required = [i for i in case.candidates if i.metadata.get(REQUIRED_KEY)]
    assert len(useful) == 4
    assert len(harmful) == 3
    assert len(stale) == 3
    assert len(required) == 2
    assert case.relevant_ids == frozenset(i.id for i in useful)
    assert case.required_ids == frozenset(i.id for i in required)


def test_required_is_subset_of_useful() -> None:
    case = RetentionBenchmark(_config()).generate(2)[0]
    assert case.required_ids <= case.relevant_ids


def test_every_item_has_observable_signals() -> None:
    case = RetentionBenchmark(_config()).generate(3)[0]
    for item in case.candidates:
        assert SALIENCE_KEY in item.metadata
        assert "frequency" in item.metadata
        assert item.timestamp is not None


def test_timestamps_are_unique_and_dense() -> None:
    case = RetentionBenchmark(_config()).generate(4)[0]
    stamps = sorted(i.timestamp for i in case.candidates if i.timestamp is not None)
    n = len(case.candidates)
    assert stamps == [float(k) for k in range(n)]


def test_harmful_items_are_recent_useful_spread() -> None:
    case = RetentionBenchmark(_config()).generate(5)[0]
    n = len(case.candidates)
    harmful_ts = [
        i.timestamp for i in case.candidates if i.metadata.get(HARMFUL_KEY)
    ]
    # Harmful items occupy the most recent slots, decoupling harm from age.
    assert min(t for t in harmful_ts if t is not None) >= n - 3


def test_evaluate_returns_declared_metrics() -> None:
    bench = RetentionBenchmark(_config())
    case = bench.generate(6)[0]
    budget = Budget(4, BudgetUnit.ITEMS)
    context = OracleRetentionPolicy().retain(case.candidates, case.task, budget).context
    metrics = bench.evaluate(case, context)
    assert set(metrics) == set(DECLARED_METRICS)
    assert set(metrics) == set(bench.declared_metrics)


def test_oracle_outscores_retain_all_on_precision() -> None:
    bench = RetentionBenchmark(_config())
    case = bench.generate(8)[0]
    budget = Budget(4, BudgetUnit.ITEMS)
    oracle_ctx = (
        OracleRetentionPolicy().retain(case.candidates, case.task, budget).context
    )
    retain_ctx = (
        RetainAllPolicy().retain(case.candidates, case.task, budget).context
    )
    oracle = bench.evaluate(case, oracle_ctx)
    retain = bench.evaluate(case, retain_ctx)
    assert oracle["retention_precision"] >= retain["retention_precision"]
    assert oracle["harmful_retention_rate"] <= retain["harmful_retention_rate"]


def test_config_validation() -> None:
    with pytest.raises(ValueError):
        _config(num_useful=0)
    with pytest.raises(ValueError):
        _config(num_required=5)
    with pytest.raises(ValueError):
        _config(noise="medium")
    with pytest.raises(ValueError):
        _config(budget_sweep=())


def test_presets_declare_metadata() -> None:
    presets = all_retention_presets()
    assert len(presets) == 3
    ids = {str(p.id) for p in presets}
    assert ids == {"low-noise-retention", "stale-accumulation", "harmful-memory"}
    for preset in presets:
        assert preset.version
        assert preset.config.construct
        assert preset.config.expected_failure_modes
        assert preset.budget_sweep


def test_named_presets_build() -> None:
    assert str(low_noise_retention().id) == "low-noise-retention"
    assert str(stale_accumulation().id) == "stale-accumulation"
    assert str(harmful_memory().id) == "harmful-memory"
    assert harmful_memory().config.noise == "high"
