"""Tests for the Phase 8 naturalistic Markdown report."""

from __future__ import annotations

from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase8 import (
    naturalistic_email,
    naturalistic_support,
    phase8_experiments,
)
from context_engineering_lab.reporting.phase8_report import (
    render_experiment,
    render_report,
)


def test_render_experiment_has_expected_sections() -> None:
    result = ExperimentRunner().run(naturalistic_email())
    text = render_experiment(result)
    assert "## naturalistic-email" in text
    assert "benchmark: `email-old-signal`" in text
    assert "run_id:" in text
    assert "answer_support by strategy and budget" in text
    assert "conflict / superseded / harmful / stale" in text
    assert "observations (this scenario only)" in text
    assert "ceiling, not deployable" in text


def test_support_report_lists_attention_strategy() -> None:
    result = ExperimentRunner().run(naturalistic_support())
    text = render_experiment(result)
    assert "attention->selection" in text


def test_render_report_has_header_and_limitations() -> None:
    runner = ExperimentRunner()
    results = {name: runner.run(exp) for name, exp in phase8_experiments().items()}
    text = render_report(results)
    assert text.startswith("# Phase 8 report")
    assert "## limitations" in text
    assert "not real" in text
    assert "no llm" in text.lower()


def test_render_report_is_deterministic() -> None:
    runner = ExperimentRunner()
    first = {name: runner.run(exp) for name, exp in phase8_experiments().items()}
    second = {name: runner.run(exp) for name, exp in phase8_experiments().items()}
    assert render_report(first) == render_report(second)
