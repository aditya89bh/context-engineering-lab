"""Tests for the Phase 10 robustness report."""

from __future__ import annotations

from context_engineering_lab.benchmarks.naturalistic.presets import email_old_signal
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase10 import (
    RobustnessSpec,
    robustness_experiments,
    robustness_specs,
)
from context_engineering_lab.perturbations.aggregation import (
    GroupComparison,
    OracleGapShift,
    RobustnessAggregation,
)
from context_engineering_lab.perturbations.comparison import PerturbationComparison
from context_engineering_lab.reporting.phase10_report import (
    render_from_results,
    render_report,
)
from context_engineering_lab.synthesis.aggregation import aggregate_results


def _synthetic() -> tuple[RobustnessAggregation, list[RobustnessSpec]]:
    comparison = PerturbationComparison(
        benchmark_id="email-old-signal",
        perturbation_id="distractor-injection",
        strategy_id="keyword-overlap",
        metric="selection_recall",
        baseline_value=0.8,
        perturbed_value=0.4,
        degradation=0.4,
        robustness=0.5,
    )
    shift = OracleGapShift(
        group="distractor-stress",
        benchmark_id="email-old-signal",
        perturbation_id="distractor-injection",
        strategy_id="keyword-overlap",
        metric="answer_support",
        baseline_gap=0.1,
        perturbed_gap=0.5,
        gap_increase=0.4,
    )
    group_row = GroupComparison(group="distractor-stress", comparison=comparison)
    robustness = RobustnessAggregation(
        aggregation=aggregate_results([]),
        comparisons=(group_row,),
        oracle_shifts=(shift,),
    )
    spec = RobustnessSpec(
        group="distractor-stress",
        benchmark=email_old_signal(),
        strategies=(),
        perturbations=("distractor-injection",),
    )
    return robustness, [spec]


def test_report_has_expected_sections() -> None:
    robustness, specs = _synthetic()
    report = render_report(robustness, specs)
    assert "# Phase 10 robustness report" in report
    assert "## perturbations applied" in report
    assert "## degradation by perturbation" in report
    assert "## strategy sensitivity" in report
    assert "## oracle gap under perturbation" in report
    assert "## observations" in report


def test_report_renders_comparison_values() -> None:
    robustness, specs = _synthetic()
    report = render_report(robustness, specs)
    assert "keyword-overlap" in report
    assert "selection_recall" in report
    assert "0.400" in report


def test_observations_name_strategy_benchmark_perturbation_metric() -> None:
    robustness, specs = _synthetic()
    report = render_report(robustness, specs)
    observations = report.split("## observations", 1)[1]
    assert "keyword-overlap" in observations
    assert "email-old-signal" in observations
    assert "distractor-injection" in observations
    assert "selection_recall" in observations


def test_render_from_results_is_deterministic() -> None:
    runner = ExperimentRunner()
    spec = next(s for s in robustness_specs() if s.group == "distractor-stress")
    experiments = robustness_experiments()
    names = [spec.baseline_name()]
    names += [spec.perturbed_name(p) for p in spec.perturbations]
    results = [runner.run(experiments[name]) for name in names]
    first = render_from_results(results, [spec])
    second = render_from_results(results, [spec])
    assert first == second
    assert first.startswith("# Phase 10 robustness report")
