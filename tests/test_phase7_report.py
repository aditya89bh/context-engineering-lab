"""Tests for Phase 7 Markdown reporting."""

from __future__ import annotations

from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase7 import phase7_experiments
from context_engineering_lab.reporting.phase7_report import (
    render_experiment,
    render_report,
)


def _results() -> dict[str, ExperimentResult]:
    runner = ExperimentRunner()
    return {name: runner.run(exp) for name, exp in phase7_experiments().items()}


def test_render_experiment_contains_sections() -> None:
    result = next(iter(_results().values()))
    text = render_experiment(result)
    assert "selection_recall by strategy and budget" in text
    assert "harmful_retention_rate by strategy and budget" in text
    assert "interaction metrics (pipeline vs its constituent baselines)" in text
    assert "observations (this benchmark only)" in text


def test_render_report_has_header_and_limitations() -> None:
    text = render_report(_results())
    assert "# Phase 7 report: interactions between primitives" in text
    assert "## limitations" in text
    assert "oracle-pipeline" in text
    for name in (
        "interaction-balanced",
        "interaction-memory-pressure",
        "interaction-noisy-context",
        "interaction-budget-sweep",
    ):
        assert name in text


def test_report_is_deterministic() -> None:
    assert render_report(_results()) == render_report(_results())


def test_interaction_table_lists_pipelines() -> None:
    text = render_report(_results())
    assert "retention->selection" in text
    assert "temporal->selection" in text
