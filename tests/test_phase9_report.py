"""Tests for Phase 9 synthesis reporting."""

from __future__ import annotations

from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.reporting.phase9_report import (
    render_from_results,
    render_report,
)
from context_engineering_lab.synthesis.aggregation import aggregate_results
from tests.synthesis_helpers import simple_result


def _results() -> list[ExperimentResult]:
    selection = simple_result(
        "selection",
        {
            "oracle": {"answer_support": {(1, 2): 1.0, (1, 4): 1.0}},
            "recency": {"answer_support": {(1, 2): 0.3, (1, 4): 0.6}},
            "keyword-overlap": {"answer_support": {(1, 2): 0.5, (1, 4): 0.7}},
        },
    )
    attention = simple_result(
        "attention",
        {
            "oracle-allocation": {"signal_capture_rate": {(1, 2): 0.9, (1, 4): 0.9}},
            "recency": {"signal_capture_rate": {(1, 2): 0.2, (1, 4): 0.2}},
        },
    )
    return [selection, attention]


def test_report_has_all_sections() -> None:
    report = render_from_results(_results())
    for heading in (
        "# Phase 9 report: cross-benchmark synthesis",
        "## provenance",
        "## strategy profiles",
        "## dominance",
        "## oracle gap",
        "## failures",
        "## stability",
        "## limitations",
    ):
        assert heading in report


def test_report_lists_strategies_and_frontier() -> None:
    report = render_from_results(_results())
    assert "recency" in report
    assert "Non-dominated frontier:" in report
    assert "oracle" in report.lower()


def test_report_is_deterministic() -> None:
    results = _results()
    assert render_from_results(results) == render_from_results(results)


def test_render_report_matches_aggregate() -> None:
    results = _results()
    aggregation = aggregate_results(results)
    assert render_report(aggregation) == render_from_results(results)
