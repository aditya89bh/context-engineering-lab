"""Tests for the Phase 5 reporting module."""

from __future__ import annotations

from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase5 import phase5_experiments
from context_engineering_lab.reporting.phase5_report import (
    render_experiment,
    render_report,
)


def _results() -> dict[str, object]:
    runner = ExperimentRunner()
    return {name: runner.run(exp) for name, exp in phase5_experiments().items()}


def test_render_report_has_header_and_limitations() -> None:
    report = render_report(_results())  # type: ignore[arg-type]
    assert "# Phase 5 report" in report
    assert "## limitations" in report
    assert "oracle-retention" in report
    assert "not a" in report.lower()


def test_render_experiment_lists_provenance_and_tables() -> None:
    result = ExperimentRunner().run(phase5_experiments()["retention-baselines"])
    section = render_experiment(result)
    assert "benchmark: `low-noise-retention`" in section
    assert "useful_retention_rate by policy and budget" in section
    assert "harmful_retention_rate by policy and budget" in section
    assert "ceiling, not deployable" in section


def test_report_is_deterministic() -> None:
    assert render_report(_results()) == render_report(_results())  # type: ignore[arg-type]
