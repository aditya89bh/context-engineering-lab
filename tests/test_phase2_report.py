"""Tests for the Phase 2 Markdown report."""

from __future__ import annotations

from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase2 import phase2_experiments
from context_engineering_lab.reporting.phase2_report import (
    render_experiment,
    render_report,
)


def _run_all() -> dict[str, object]:
    runner = ExperimentRunner()
    return {name: runner.run(exp) for name, exp in phase2_experiments().items()}


def test_render_experiment_contains_provenance_and_tables() -> None:
    result = ExperimentRunner().run(phase2_experiments()["selection-baselines-easy"])
    text = render_experiment(result)
    assert "## selection-baselines-easy" in text
    assert "benchmark: `easy-selection`" in text
    assert "answer_support by strategy and budget" in text
    assert "| strategy |" in text
    assert "oracle" in text


def test_render_report_includes_all_experiments_and_limitations() -> None:
    results = _run_all()
    text = render_report(results)  # type: ignore[arg-type]
    for name in phase2_experiments():
        assert f"## {name}" in text
    assert "limitations" in text
    assert "not a deployable strategy" in text


def test_report_is_deterministic() -> None:
    first = render_report(_run_all())  # type: ignore[arg-type]
    second = render_report(_run_all())  # type: ignore[arg-type]
    assert first == second
