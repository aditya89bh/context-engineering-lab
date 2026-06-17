"""Tests for the Phase 6 reporting module."""

from __future__ import annotations

from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase6 import phase6_experiments
from context_engineering_lab.reporting.phase6_report import (
    render_experiment,
    render_report,
)


def _results() -> dict[str, object]:
    runner = ExperimentRunner()
    return {name: runner.run(exp) for name, exp in phase6_experiments().items()}


def test_render_report_has_header_and_limitations() -> None:
    report = render_report(_results())  # type: ignore[arg-type]
    assert "# Phase 6 report" in report
    assert "## limitations" in report
    assert "oracle-allocation" in report
    assert "distinct from selection" in report.lower()


def test_render_experiment_lists_provenance_and_tables() -> None:
    result = ExperimentRunner().run(phase6_experiments()["attention-concentrated"])
    section = render_experiment(result)
    assert "benchmark: `concentrated-signal`" in section
    assert "signal_capture_rate by allocator and budget" in section
    assert "wasted_attention_rate by allocator and budget" in section
    assert "ceiling, not deployable" in section


def test_report_is_deterministic() -> None:
    assert render_report(_results()) == render_report(_results())  # type: ignore[arg-type]
