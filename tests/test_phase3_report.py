"""Tests for the Phase 3 Markdown report."""

from __future__ import annotations

from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase3 import phase3_experiments
from context_engineering_lab.reporting.phase3_report import (
    render_experiment,
    render_report,
)


def _run_all() -> dict[str, ExperimentResult]:
    runner = ExperimentRunner()
    return {name: runner.run(exp) for name, exp in phase3_experiments().items()}


def test_render_experiment_contains_provenance_and_tables() -> None:
    result = ExperimentRunner().run(phase3_experiments()["compression-baselines-easy"])
    text = render_experiment(result)
    assert "## compression-baselines-easy" in text
    assert "benchmark: `easy-compression`" in text
    assert "information_retention by strategy and budget" in text
    assert "compression_ratio by strategy and budget" in text
    assert "oracle-compression" in text


def test_render_report_includes_all_experiments_and_limitations() -> None:
    text = render_report(_run_all())
    for name in phase3_experiments():
        assert f"## {name}" in text
    assert "limitations" in text
    assert "not a deployable strategy" in text
    assert "no LLM" in text


def test_report_is_deterministic() -> None:
    assert render_report(_run_all()) == render_report(_run_all())
