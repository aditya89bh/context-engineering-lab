"""Tests for the temporal-context-relevance benchmark and its presets."""

from __future__ import annotations

import pytest

from context_engineering_lab.benchmarks.temporal import (
    DECLARED_METRICS,
    TemporalBenchmark,
    TemporalConfig,
)
from context_engineering_lab.benchmarks.temporal_presets import (
    all_temporal_presets,
    drift_heavy,
    old_signal,
    recent_signal,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.temporal import SALIENCE_KEY, STALE_KEY
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY
from context_engineering_lab.strategies.temporal import OracleTemporalSelection


def config(**overrides: object) -> TemporalConfig:
    base = {
        "benchmark_id": "test-temporal",
        "version": "1.0",
        "construct": "test",
        "num_cases": 4,
        "sequence_length": 20,
        "num_relevant": 3,
        "num_distractors": 6,
        "num_stale": 3,
        "relevant_age": "recent",
        "distractor_age": "mixed",
        "drift": "none",
    }
    base.update(overrides)
    return TemporalConfig(**base)  # type: ignore[arg-type]


def test_generation_is_deterministic() -> None:
    bench = TemporalBenchmark(config(drift="abrupt"))
    first = bench.generate(3)
    second = bench.generate(3)
    assert [c.case_id for c in first] == [c.case_id for c in second]
    assert [
        [(str(i.id), i.timestamp, i.metadata[SALIENCE_KEY]) for i in c.candidates]
        for c in first
    ] == [
        [(str(i.id), i.timestamp, i.metadata[SALIENCE_KEY]) for i in c.candidates]
        for c in second
    ]


def test_case_has_one_item_per_position() -> None:
    bench = TemporalBenchmark(config())
    for case in bench.generate(1):
        assert len(case.candidates) == 20
        stamps = sorted(
            i.timestamp for i in case.candidates if i.timestamp is not None
        )
        assert stamps == [float(t) for t in range(20)]


def test_relevant_count_and_flags() -> None:
    bench = TemporalBenchmark(config(num_relevant=3))
    for case in bench.generate(1):
        assert len(case.relevant_ids) == 3
        for item in case.candidates:
            expected = item.id in case.relevant_ids
            assert bool(item.metadata[ORACLE_RELEVANCE_KEY]) is expected


def test_recent_band_places_relevant_at_newest() -> None:
    bench = TemporalBenchmark(config(relevant_age="recent", num_relevant=3))
    for case in bench.generate(1):
        rel_ts = sorted(
            i.timestamp
            for i in case.candidates
            if i.id in case.relevant_ids and i.timestamp is not None
        )
        assert rel_ts == [17.0, 18.0, 19.0]


def test_old_band_places_relevant_at_oldest() -> None:
    bench = TemporalBenchmark(config(relevant_age="old", num_relevant=3))
    for case in bench.generate(1):
        rel_ts = sorted(
            i.timestamp
            for i in case.candidates
            if i.id in case.relevant_ids and i.timestamp is not None
        )
        assert rel_ts == [0.0, 1.0, 2.0]


def test_stale_items_are_old_and_flagged_non_relevant() -> None:
    bench = TemporalBenchmark(config(relevant_age="recent", num_stale=3))
    for case in bench.generate(1):
        stale = [i for i in case.candidates if bool(i.metadata[STALE_KEY])]
        assert len(stale) == 3
        for item in stale:
            assert item.id not in case.relevant_ids


def test_no_drift_keeps_non_relevant_salience_low() -> None:
    bench = TemporalBenchmark(config(drift="none"))
    for case in bench.generate(1):
        for item in case.candidates:
            if item.id in case.relevant_ids:
                continue
            assert float(item.metadata[SALIENCE_KEY]) <= 0.25  # type: ignore[arg-type]


def test_abrupt_drift_creates_recent_high_salience_decoys() -> None:
    bench = TemporalBenchmark(config(relevant_age="old", drift="abrupt"))
    for case in bench.generate(1):
        decoys = [
            item
            for item in case.candidates
            if item.id not in case.relevant_ids
            and float(item.metadata[SALIENCE_KEY]) >= 0.9  # type: ignore[arg-type]
        ]
        assert decoys


def test_evaluate_returns_declared_metrics() -> None:
    bench = TemporalBenchmark(config())
    case = bench.generate(1)[0]
    ctx = OracleTemporalSelection().select(
        case.candidates, case.task, Budget(4, BudgetUnit.ITEMS)
    )
    scores = bench.evaluate(case, ctx)
    assert set(scores) == set(DECLARED_METRICS)


def test_presets_have_distinct_ids_and_metadata() -> None:
    presets = all_temporal_presets()
    ids = {str(p.id) for p in presets}
    assert ids == {"recent-signal", "old-signal", "drift-heavy"}
    for preset in presets:
        assert preset.config.construct
        assert preset.config.expected_failure_modes
        assert preset.budget_sweep


def test_preset_constructors_are_callable() -> None:
    assert recent_signal().config.relevant_age == "recent"
    assert old_signal().config.relevant_age == "old"
    assert drift_heavy().config.drift == "abrupt"


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        config(num_cases=0)
    with pytest.raises(ValueError):
        config(sequence_length=1)
    with pytest.raises(ValueError):
        config(relevant_age="ancient")
    with pytest.raises(ValueError):
        config(drift="slow")
    with pytest.raises(ValueError):
        config(num_relevant=10, num_distractors=10, num_stale=10)
