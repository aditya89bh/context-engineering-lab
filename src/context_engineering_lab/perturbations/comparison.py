"""Perturbation comparison utilities.

Given two :class:`~context_engineering_lab.synthesis.aggregation.Aggregation`
views — one from an unperturbed *baseline* benchmark and one from its *perturbed*
counterpart — these helpers line up matching ``(strategy, metric)`` cells and
compute the robustness metrics for each. Cost metrics are oriented (negated)
before the drop is measured, so a positive :attr:`PerturbationComparison.degradation`
always means "got worse". Neutral metrics (utilisation, ratios) are skipped.
"""

from __future__ import annotations

from dataclasses import dataclass

from context_engineering_lab.core.robustness_metrics import (
    degradation,
    robustness_score,
)
from context_engineering_lab.synthesis.aggregation import (
    Aggregation,
    Direction,
    direction,
    is_quality_metric,
)


@dataclass(frozen=True, slots=True)
class PerturbationComparison:
    """One ``(strategy, metric)`` baseline-vs-perturbed comparison.

    Args:
        benchmark_id: The unperturbed (baseline) benchmark id.
        perturbation_id: The perturbation applied to produce the perturbed run.
        strategy_id: The strategy compared.
        metric: The metric compared (a quality metric; never neutral).
        baseline_value: The raw mean-over-budgets baseline score (as reported).
        perturbed_value: The raw mean-over-budgets perturbed score (as reported).
        degradation: Oriented drop ``baseline - perturbed`` (positive is worse).
        robustness: Fraction of baseline retained, in ``[0.0, 1.0]``.
    """

    benchmark_id: str
    perturbation_id: str
    strategy_id: str
    metric: str
    baseline_value: float
    perturbed_value: float
    degradation: float
    robustness: float


def _oriented(metric: str, value: float) -> float:
    """Return ``value`` oriented so higher is better."""
    if direction(metric) is Direction.LOWER_IS_BETTER:
        return -value
    return value


def compare_perturbation(
    baseline: Aggregation,
    perturbed: Aggregation,
    *,
    baseline_benchmark: str,
    perturbed_benchmark: str,
    perturbation_id: str,
) -> list[PerturbationComparison]:
    """Compare every shared ``(strategy, metric)`` cell across two aggregations.

    Args:
        baseline: Aggregation containing the unperturbed benchmark's cells.
        perturbed: Aggregation containing the perturbed benchmark's cells.
        baseline_benchmark: The baseline benchmark id to read from ``baseline``.
        perturbed_benchmark: The perturbed benchmark id to read from ``perturbed``.
        perturbation_id: The perturbation that produced the perturbed run.

    Returns:
        One :class:`PerturbationComparison` per shared strategy and quality metric,
        sorted by ``(strategy_id, metric)``.
    """
    base_view = baseline.benchmark_aggregate(baseline_benchmark)
    pert_view = perturbed.benchmark_aggregate(perturbed_benchmark)
    strategies = sorted(set(base_view.strategies()) & set(pert_view.strategies()))
    metrics = sorted(set(base_view.metrics()) & set(pert_view.metrics()))

    comparisons: list[PerturbationComparison] = []
    for strategy_id in strategies:
        for metric in metrics:
            if not is_quality_metric(metric):
                continue
            base_value = baseline.mean_over_budgets(
                baseline_benchmark, strategy_id, metric
            )
            pert_value = perturbed.mean_over_budgets(
                perturbed_benchmark, strategy_id, metric
            )
            if base_value is None or pert_value is None:
                continue
            oriented_base = _oriented(metric, base_value)
            oriented_pert = _oriented(metric, pert_value)
            comparisons.append(
                PerturbationComparison(
                    benchmark_id=baseline_benchmark,
                    perturbation_id=perturbation_id,
                    strategy_id=strategy_id,
                    metric=metric,
                    baseline_value=base_value,
                    perturbed_value=pert_value,
                    degradation=degradation(oriented_base, oriented_pert),
                    robustness=robustness_score(oriented_base, oriented_pert),
                )
            )
    return comparisons
