"""Tests for Phase 10 robustness metrics and perturbation comparison."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.robustness_metrics import (
    degradation,
    degradation_under_conflict,
    degradation_under_noise,
    robustness_score,
)
from context_engineering_lab.perturbations.comparison import compare_perturbation
from context_engineering_lab.synthesis.aggregation import (
    Aggregation,
    aggregate_results,
)
from tests.synthesis_helpers import simple_result


def test_degradation_is_signed_drop() -> None:
    assert degradation(0.8, 0.5) == pytest.approx(0.3)
    assert degradation(0.5, 0.5) == 0.0
    assert degradation(0.4, 0.6) == pytest.approx(-0.2)


def test_degradation_aliases_match_degradation() -> None:
    assert degradation_under_noise(0.9, 0.4) == degradation(0.9, 0.4)
    assert degradation_under_conflict(0.9, 0.4) == degradation(0.9, 0.4)


def test_robustness_score_fraction_retained() -> None:
    assert robustness_score(0.8, 0.4) == pytest.approx(0.5)
    assert robustness_score(1.0, 1.0) == 1.0
    assert robustness_score(1.0, 0.0) == 0.0


def test_robustness_score_is_clamped() -> None:
    assert robustness_score(0.5, 1.0) == 1.0
    assert robustness_score(0.5, -0.5) == 0.0


def test_robustness_score_non_positive_baseline() -> None:
    assert robustness_score(0.0, 0.0) == 1.0
    assert robustness_score(0.0, -0.1) == 0.0
    assert robustness_score(-0.1, -0.3) == 0.0


def _aggregations() -> tuple[Aggregation, Aggregation]:
    baseline = aggregate_results(
        [
            simple_result(
                "bench",
                {
                    "s": {
                        "selection_recall": {(1, 2): 0.8},
                        "harmful_retention_rate": {(1, 2): 0.1},
                        "budget_utilization": {(1, 2): 1.0},
                    }
                },
            )
        ]
    )
    perturbed = aggregate_results(
        [
            simple_result(
                "bench+distractor-injection",
                {
                    "s": {
                        "selection_recall": {(1, 2): 0.4},
                        "harmful_retention_rate": {(1, 2): 0.3},
                        "budget_utilization": {(1, 2): 1.0},
                    }
                },
            )
        ]
    )
    return baseline, perturbed


def test_compare_perturbation_quality_metric() -> None:
    baseline, perturbed = _aggregations()
    comparisons = compare_perturbation(
        baseline,
        perturbed,
        baseline_benchmark="bench",
        perturbed_benchmark="bench+distractor-injection",
        perturbation_id="distractor-injection",
    )
    recall = next(c for c in comparisons if c.metric == "selection_recall")
    assert recall.degradation == pytest.approx(0.4)
    assert recall.robustness == pytest.approx(0.5)
    assert recall.baseline_value == pytest.approx(0.8)
    assert recall.perturbed_value == pytest.approx(0.4)


def test_compare_perturbation_orients_cost_metric() -> None:
    baseline, perturbed = _aggregations()
    comparisons = compare_perturbation(
        baseline,
        perturbed,
        baseline_benchmark="bench",
        perturbed_benchmark="bench+distractor-injection",
        perturbation_id="distractor-injection",
    )
    harmful = next(c for c in comparisons if c.metric == "harmful_retention_rate")
    assert harmful.degradation == pytest.approx(0.2)
    assert harmful.robustness == 0.0


def test_compare_perturbation_skips_neutral_metrics() -> None:
    baseline, perturbed = _aggregations()
    comparisons = compare_perturbation(
        baseline,
        perturbed,
        baseline_benchmark="bench",
        perturbed_benchmark="bench+distractor-injection",
        perturbation_id="distractor-injection",
    )
    metrics = {c.metric for c in comparisons}
    assert "budget_utilization" not in metrics
