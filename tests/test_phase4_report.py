"""Tests for the Phase 4 reporting module."""

from __future__ import annotations

from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase4 import phase4_experiments
from context_engineering_lab.reporting.phase4_report import (
    render_experiment,
    render_report,
)


def _results() -> dict[str, object]:
    runner = ExperimentRunner()
    return {name: runner.run(exp) for name, exp in phase4_experiments().items()}


def test_render_report_has_header_and_limitations() -> None:
    report = render_report(_results())  # type: ignore[arg-type]
    assert "# Phase 4 report" in report
    assert "## limitations" in report
    assert "oracle-temporal" in report
    assert "no forgetting" in report.lower()


def test_render_experiment_lists_provenance_and_tables() -> None:
    result = ExperimentRunner().run(phase4_experiments()["temporal-recent-signal"])
    section = render_experiment(result)
    assert "benchmark: `recent-signal`" in section
    assert "answer_support by strategy and budget" in section
    assert "relevant_age_gap by strategy and budget" in section
    assert "ceiling, not" in section


def test_report_is_deterministic() -> None:
    assert render_report(_results()) == render_report(_results())  # type: ignore[arg-type]
