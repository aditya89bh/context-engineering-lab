"""Tests for the selection-signal-retrieval benchmark and its presets."""

from __future__ import annotations

import pytest

from context_engineering_lab.benchmarks.selection import (
    DECLARED_METRICS,
    SIGNAL_TERMS,
    SelectionBenchmark,
    SelectionConfig,
)
from context_engineering_lab.benchmarks.selection_presets import (
    all_selection_presets,
    easy_selection,
    high_distractor_selection,
    position_biased_selection,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection
from context_engineering_lab.strategies.oracle import (
    ORACLE_RELEVANCE_KEY,
    OracleSelection,
)


def config(**overrides: object) -> SelectionConfig:
    base = {
        "benchmark_id": "test-sel",
        "version": "1.0",
        "construct": "test",
        "num_cases": 5,
        "num_distractors": 4,
        "target_position": "early",
        "distractor_similarity": "low",
    }
    base.update(overrides)
    return SelectionConfig(**base)  # type: ignore[arg-type]


def test_generation_is_deterministic() -> None:
    bench = SelectionBenchmark(config(target_position="random"))
    first = bench.generate(3)
    second = bench.generate(3)
    assert [c.case_id for c in first] == [c.case_id for c in second]
    assert [
        [str(i.id) for i in c.candidates] for c in first
    ] == [[str(i.id) for i in c.candidates] for c in second]


def test_each_case_has_expected_candidate_count_and_targets() -> None:
    bench = SelectionBenchmark(config(num_distractors=4, num_targets=1))
    for case in bench.generate(1):
        assert len(case.candidates) == 5
        assert len(case.relevant_ids) == 1
        assert case.relevant_ids <= {i.id for i in case.candidates}


def test_early_position_places_target_first() -> None:
    bench = SelectionBenchmark(config(target_position="early"))
    for case in bench.generate(1):
        first_item = case.candidates[0]
        assert first_item.id in case.relevant_ids


def test_late_position_places_target_last() -> None:
    bench = SelectionBenchmark(config(target_position="late"))
    for case in bench.generate(1):
        last_item = case.candidates[-1]
        assert last_item.id in case.relevant_ids


def test_low_similarity_distractors_share_no_signal_terms() -> None:
    bench = SelectionBenchmark(config(distractor_similarity="low"))
    signal = set(SIGNAL_TERMS)
    for case in bench.generate(1):
        for item in case.candidates:
            if item.id in case.relevant_ids:
                continue
            assert not (set(item.content.split()) & signal)


def test_high_similarity_distractors_share_all_signal_terms() -> None:
    bench = SelectionBenchmark(config(distractor_similarity="high"))
    signal = set(SIGNAL_TERMS)
    for case in bench.generate(1):
        for item in case.candidates:
            if item.id in case.relevant_ids:
                continue
            assert signal <= set(item.content.split())


def test_targets_carry_oracle_flag() -> None:
    bench = SelectionBenchmark(config())
    for case in bench.generate(1):
        for item in case.candidates:
            expected = item.id in case.relevant_ids
            assert bool(item.metadata[ORACLE_RELEVANCE_KEY]) is expected


def test_evaluate_returns_declared_metrics() -> None:
    bench = SelectionBenchmark(config())
    case = bench.generate(1)[0]
    context = OracleSelection().select(
        case.candidates, case.task, Budget(2, BudgetUnit.ITEMS)
    )
    scores = bench.evaluate(case, context)
    assert set(scores) == set(DECLARED_METRICS)
    assert all(0.0 <= v <= 1.0 for v in scores.values())


def test_oracle_beats_keyword_overlap_under_high_distractors() -> None:
    bench = high_distractor_selection()
    budget = Budget(1, BudgetUnit.ITEMS)
    oracle_support = 0.0
    keyword_support = 0.0
    cases = bench.generate(1)
    for case in cases:
        oracle_ctx = OracleSelection().select(case.candidates, case.task, budget)
        keyword_ctx = KeywordOverlapSelection().select(
            case.candidates, case.task, budget
        )
        oracle_support += bench.evaluate(case, oracle_ctx)["answer_support"]
        keyword_support += bench.evaluate(case, keyword_ctx)["answer_support"]
    assert oracle_support == float(len(cases))
    assert oracle_support > keyword_support


def test_presets_have_distinct_ids_and_constructs() -> None:
    presets = all_selection_presets()
    ids = {str(p.id) for p in presets}
    assert ids == {
        "easy-selection",
        "position-biased-selection",
        "high-distractor-selection",
    }
    for preset in presets:
        assert preset.config.construct
        assert preset.config.expected_failure_modes


def test_preset_budget_sweeps_are_nonempty() -> None:
    for preset in (
        easy_selection(),
        position_biased_selection(),
        high_distractor_selection(),
    ):
        assert preset.budget_sweep


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        config(num_cases=0)
    with pytest.raises(ValueError):
        config(target_position="sideways")
    with pytest.raises(ValueError):
        config(distractor_similarity="extreme")
