"""Tests for the naturalistic benchmark families and presets."""

from __future__ import annotations

import pytest

from context_engineering_lab.benchmarks.naturalistic import all_naturalistic_presets
from context_engineering_lab.benchmarks.naturalistic.email import EmailThreadBenchmark
from context_engineering_lab.benchmarks.naturalistic.meeting import (
    MeetingNotesBenchmark,
)
from context_engineering_lab.benchmarks.naturalistic.presets import (
    email_conflict_heavy,
    email_old_signal,
    meeting_action_items,
    memory_log_noisy,
    revision_current_truth,
    support_stale_fix,
)
from context_engineering_lab.benchmarks.naturalistic.records import (
    CONFLICTING_KEY,
    HARMFUL_KEY,
    SUPERSEDED_KEY,
    NaturalisticBenchmark,
    NaturalisticConfig,
)
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.temporal import SALIENCE_KEY
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection
from context_engineering_lab.strategies.oracle import (
    ORACLE_RELEVANCE_KEY,
    OracleSelection,
)

_ALL_FAMILIES = (
    email_old_signal,
    email_conflict_heavy,
    meeting_action_items,
    support_stale_fix,
    revision_current_truth,
    memory_log_noisy,
)


def _fingerprint(
    cases: list[Case],
) -> list[tuple[str, tuple[tuple[str, str, float | None, object], ...]]]:
    return [
        (
            case.case_id,
            tuple(
                (str(i.id), i.content, i.timestamp, i.metadata.get(SALIENCE_KEY))
                for i in case.candidates
            ),
        )
        for case in cases
    ]


@pytest.mark.parametrize("factory", _ALL_FAMILIES)
def test_generation_is_deterministic(factory) -> None:  # type: ignore[no-untyped-def]
    bench = factory()
    first = _fingerprint(list(bench.generate(1)))
    second = _fingerprint(list(bench.generate(1)))
    assert first == second


@pytest.mark.parametrize("factory", _ALL_FAMILIES)
def test_distinct_seeds_change_cases(factory) -> None:  # type: ignore[no-untyped-def]
    bench = factory()
    assert _fingerprint(list(bench.generate(1))) != _fingerprint(
        list(bench.generate(2))
    )


@pytest.mark.parametrize("factory", _ALL_FAMILIES)
def test_every_case_has_a_relevant_item(factory) -> None:  # type: ignore[no-untyped-def]
    bench = factory()
    for case in bench.generate(1):
        assert case.relevant_ids
        assert case.required_ids <= case.relevant_ids


@pytest.mark.parametrize("factory", _ALL_FAMILIES)
def test_evaluate_returns_declared_metrics(factory) -> None:  # type: ignore[no-untyped-def]
    bench = factory()
    case = next(iter(bench.generate(1)))
    budget = Budget(8, BudgetUnit.ITEMS)
    context = KeywordOverlapSelection().select(case.candidates, case.task, budget)
    scores = bench.evaluate(case, context)
    assert set(scores) == set(bench.declared_metrics)


@pytest.mark.parametrize("factory", _ALL_FAMILIES)
def test_oracle_supports_the_answer(factory) -> None:  # type: ignore[no-untyped-def]
    bench = factory()
    budget = Budget(12, BudgetUnit.ITEMS)
    oracle = OracleSelection()
    for case in bench.generate(1):
        context = oracle.select(case.candidates, case.task, budget)
        assert bench.evaluate(case, context)["answer_support"] == 1.0


@pytest.mark.parametrize("factory", _ALL_FAMILIES)
def test_relevant_items_are_findable_by_keywords(factory) -> None:  # type: ignore[no-untyped-def]
    bench = factory()
    budget = Budget(12, BudgetUnit.ITEMS)
    case = next(iter(bench.generate(1)))
    context = KeywordOverlapSelection().select(case.candidates, case.task, budget)
    assert case.relevant_ids & context.item_ids


def test_email_includes_conflicting_and_harmful() -> None:
    case = next(iter(email_old_signal().generate(1)))
    flags = [i.metadata for i in case.candidates]
    assert any(m.get(CONFLICTING_KEY) for m in flags)
    assert any(m.get(HARMFUL_KEY) for m in flags)
    assert any(m.get(ORACLE_RELEVANCE_KEY) for m in flags)


def test_meeting_includes_superseded_decisions() -> None:
    case = next(iter(meeting_action_items().generate(1)))
    assert any(i.metadata.get(SUPERSEDED_KEY) for i in case.candidates)


def test_support_is_source_based() -> None:
    case = next(iter(support_stale_fix().generate(1)))
    sources = {i.source for i in case.candidates}
    assert len([s for s in sources if s]) >= 3


def test_revision_marks_current_and_superseded() -> None:
    case = next(iter(revision_current_truth().generate(1)))
    assert any(i.metadata.get("current") for i in case.candidates)
    assert any(i.metadata.get(SUPERSEDED_KEY) for i in case.candidates)


def test_all_presets_declare_required_fields() -> None:
    presets = all_naturalistic_presets()
    assert len(presets) == 6
    ids = [str(p.id) for p in presets]
    assert len(ids) == len(set(ids))
    for preset in presets:
        cfg = preset.config
        assert cfg.version
        assert cfg.construct
        assert cfg.budget_sweep
        assert cfg.expected_failure_modes
        assert preset.declared_metrics


def test_email_keyword_overlap_keeps_conflict_higher_than_salience() -> None:
    bench = email_conflict_heavy()
    budget = Budget(4, BudgetUnit.ITEMS)
    keyword = KeywordOverlapSelection()
    conflict_rates: list[float] = []
    for case in bench.generate(1):
        context = keyword.select(case.candidates, case.task, budget)
        conflict_rates.append(bench.evaluate(case, context)["conflict_selection_rate"])
    assert max(conflict_rates) > 0.0


def test_invalid_config_rejected() -> None:
    with pytest.raises(ValueError):
        NaturalisticConfig(benchmark_id="x", version="1", construct="c", num_cases=0)


def test_invalid_family_knobs_rejected() -> None:
    cfg = NaturalisticConfig(benchmark_id="x", version="1", construct="c")
    with pytest.raises(ValueError):
        EmailThreadBenchmark(cfg, num_distractors=0)


def test_unknown_declared_metric_rejected() -> None:
    cfg = NaturalisticConfig(benchmark_id="x", version="1", construct="c")

    class _Bad(NaturalisticBenchmark):
        def __init__(self) -> None:
            super().__init__(cfg, ("not_a_metric",))

    with pytest.raises(ValueError):
        _Bad()


def test_meeting_benchmark_metric_set() -> None:
    bench = MeetingNotesBenchmark(
        NaturalisticConfig(benchmark_id="m", version="1", construct="c")
    )
    case = next(iter(bench.generate(1)))
    context = Context(items=(), budget=Budget(4, BudgetUnit.ITEMS))
    scores = bench.evaluate(case, context)
    assert scores["answer_support"] == 0.0
    assert "current_truth_support" in scores
