"""Tests for the Phase 8 naturalistic experiment configurations."""

from __future__ import annotations

from statistics import fmean

from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase8 import (
    PHASE8_SEEDS,
    curated_strategies,
    naturalistic_email,
    phase8_experiments,
    source_curated_strategies,
)


def _mean(result: ExperimentResult, strategy_id: str, metric: str) -> float:
    run = next(r for r in result.results if r.strategy_id == strategy_id)
    return fmean(m.value for m in run.metrics if m.name == metric)


def test_phase8_experiments_are_named() -> None:
    experiments = phase8_experiments()
    assert set(experiments) == {
        "naturalistic-email",
        "naturalistic-meeting",
        "naturalistic-support",
        "naturalistic-revision",
        "naturalistic-memory-log",
    }


def test_all_experiments_use_the_standard_seeds() -> None:
    for experiment in phase8_experiments().values():
        assert experiment.seeds == PHASE8_SEEDS


def test_curated_lineup_is_small_and_includes_oracle() -> None:
    ids = [str(s.id) for s in curated_strategies()]
    assert ids == [
        "recency",
        "keyword-overlap",
        "salience-retention",
        "temporal->selection",
        "retention->selection",
        "oracle",
    ]


def test_support_lineup_adds_attention_composition() -> None:
    ids = [str(s.id) for s in source_curated_strategies()]
    assert "attention->selection" in ids
    assert ids[:-1] == [str(s.id) for s in curated_strategies()]


def test_experiments_run_and_produce_results() -> None:
    runner = ExperimentRunner()
    for experiment in phase8_experiments().values():
        result = runner.run(experiment)
        assert result.results
        for run in result.results:
            assert run.metrics


def test_oracle_is_the_answer_ceiling_on_email() -> None:
    result = ExperimentRunner().run(naturalistic_email())
    assert _mean(result, "oracle", "answer_support") == 1.0


def test_salience_retention_cuts_conflict_versus_keyword_on_email() -> None:
    result = ExperimentRunner().run(naturalistic_email())
    keyword = _mean(result, "keyword-overlap", "conflict_selection_rate")
    salience = _mean(result, "salience-retention", "conflict_selection_rate")
    assert salience < keyword


def test_experiments_are_reproducible() -> None:
    runner = ExperimentRunner()
    first = runner.run(naturalistic_email())
    second = runner.run(naturalistic_email())
    assert first.metadata.run_id == second.metadata.run_id
