"""Failure-mode models.

A :class:`FailureObservation` records a single, mechanically detected way a
strategy fell short on a benchmark: it collapsed under a tight budget, trailed the
oracle by a wide margin, or got *worse* as its budget grew. These are descriptive
flags computed from the aggregated cells, not judgements about real systems.

Detection utilities live alongside these models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from context_engineering_lab.synthesis.aggregation import (
    Aggregation,
    Direction,
    direction,
    is_quality_metric,
)
from context_engineering_lab.synthesis.profiles import (
    is_oracle_id,
    oracle_primary_score,
)

#: Default minimum drop (in oriented units) to flag a metric degradation.
DEFAULT_MIN_DEGRADATION = 0.01

#: Default primary-metric score below which the tightest budget is a failure.
DEFAULT_BUDGET_THRESHOLD = 0.5

#: Default oracle gap above which a benchmark counts as underperformed.
DEFAULT_GAP_THRESHOLD = 0.3


class FailureMode(Enum):
    """A category of mechanically detected shortfall."""

    BUDGET_FAILURE = "budget_failure"
    BENCHMARK_FAILURE = "benchmark_failure"
    METRIC_DEGRADATION = "metric_degradation"


@dataclass(frozen=True, slots=True)
class FailureObservation:
    """One detected failure of a strategy on a benchmark.

    Args:
        strategy_id: The strategy.
        benchmark_id: The benchmark.
        mode: Which failure category was detected.
        metric: The metric the observation is about.
        severity: A non-negative magnitude (meaning depends on ``mode``: the
            shortfall below a threshold, the gap to the oracle, or the size of
            the degradation as budget grows).
        detail: A short, mechanical description of the observation.
    """

    strategy_id: str
    benchmark_id: str
    mode: FailureMode
    metric: str
    severity: float
    detail: str


def _primary_by_budget(
    aggregation: Aggregation, benchmark_id: str, strategy_id: str, metric: str
) -> dict[int, float]:
    return {
        cell.budget_limit: cell.mean
        for cell in aggregation.filter(
            benchmark_id=benchmark_id, strategy_id=strategy_id, metric=metric
        )
    }


def budget_failures(
    aggregation: Aggregation,
    *,
    threshold: float = DEFAULT_BUDGET_THRESHOLD,
) -> list[FailureObservation]:
    """Flag strategies whose primary metric collapses at the tightest budget.

    Args:
        aggregation: The aggregated cells.
        threshold: Primary-metric score below which the tightest budget fails.

    Returns:
        Observations sorted by ``(strategy, benchmark)``.
    """
    observations: list[FailureObservation] = []
    for strategy_id in aggregation.strategies():
        if is_oracle_id(strategy_id):
            continue
        for benchmark_id in aggregation.benchmarks():
            metric = aggregation.benchmark_aggregate(benchmark_id).primary_metric()
            if metric is None:
                continue
            by_budget = _primary_by_budget(
                aggregation, benchmark_id, strategy_id, metric
            )
            if not by_budget:
                continue
            tight = min(by_budget)
            score = by_budget[tight]
            if score < threshold:
                observations.append(
                    FailureObservation(
                        strategy_id=strategy_id,
                        benchmark_id=benchmark_id,
                        mode=FailureMode.BUDGET_FAILURE,
                        metric=metric,
                        severity=threshold - score,
                        detail=(
                            f"{metric} {score:.3f} at tightest budget {tight} "
                            f"(< {threshold:.2f})"
                        ),
                    )
                )
    observations.sort(key=lambda o: (o.strategy_id, o.benchmark_id))
    return observations


def benchmark_failures(
    aggregation: Aggregation,
    *,
    gap_threshold: float = DEFAULT_GAP_THRESHOLD,
) -> list[FailureObservation]:
    """Flag strategies that trail the oracle by a wide margin on a benchmark.

    Args:
        aggregation: The aggregated cells.
        gap_threshold: Primary-metric oracle gap above which a benchmark fails.

    Returns:
        Observations sorted by ``(strategy, benchmark)``.
    """
    observations: list[FailureObservation] = []
    for strategy_id in aggregation.strategies():
        if is_oracle_id(strategy_id):
            continue
        for benchmark_id in aggregation.benchmarks():
            metric = aggregation.benchmark_aggregate(benchmark_id).primary_metric()
            if metric is None:
                continue
            score = aggregation.mean_over_budgets(
                benchmark_id, strategy_id, metric
            )
            ceiling = oracle_primary_score(aggregation, benchmark_id)
            if score is None or ceiling is None:
                continue
            gap = ceiling - score
            if gap > gap_threshold:
                observations.append(
                    FailureObservation(
                        strategy_id=strategy_id,
                        benchmark_id=benchmark_id,
                        mode=FailureMode.BENCHMARK_FAILURE,
                        metric=metric,
                        severity=gap,
                        detail=(
                            f"{metric} {score:.3f} trails oracle {ceiling:.3f} "
                            f"by {gap:.3f}"
                        ),
                    )
                )
    observations.sort(key=lambda o: (o.strategy_id, o.benchmark_id))
    return observations


def metric_degradation(
    aggregation: Aggregation,
    *,
    min_degradation: float = DEFAULT_MIN_DEGRADATION,
) -> list[FailureObservation]:
    """Flag quality metrics that get worse as the budget grows.

    Comparing the smallest and largest budgets, a metric degrades when its
    oriented value (higher-is-better) falls. This catches both quality dropping
    and cost rising with more budget.

    Args:
        aggregation: The aggregated cells.
        min_degradation: Minimum oriented drop to report.

    Returns:
        Observations sorted by ``(strategy, benchmark, metric)``.
    """
    observations: list[FailureObservation] = []
    for strategy_id in aggregation.strategies():
        if is_oracle_id(strategy_id):
            continue
        for benchmark_id in aggregation.benchmarks():
            for metric in aggregation.benchmark_aggregate(benchmark_id).metrics():
                if not is_quality_metric(metric):
                    continue
                by_budget = _primary_by_budget(
                    aggregation, benchmark_id, strategy_id, metric
                )
                if len(by_budget) < 2:
                    continue
                low = min(by_budget)
                high = max(by_budget)
                sign = -1.0 if direction(metric) is Direction.LOWER_IS_BETTER else 1.0
                drop = sign * (by_budget[low] - by_budget[high])
                if drop > min_degradation:
                    observations.append(
                        FailureObservation(
                            strategy_id=strategy_id,
                            benchmark_id=benchmark_id,
                            mode=FailureMode.METRIC_DEGRADATION,
                            metric=metric,
                            severity=drop,
                            detail=(
                                f"{metric} worsens by {drop:.3f} from budget "
                                f"{low} to {high}"
                            ),
                        )
                    )
    observations.sort(key=lambda o: (o.strategy_id, o.benchmark_id, o.metric))
    return observations


def analyze_failures(
    aggregation: Aggregation,
    *,
    budget_threshold: float = DEFAULT_BUDGET_THRESHOLD,
    gap_threshold: float = DEFAULT_GAP_THRESHOLD,
    min_degradation: float = DEFAULT_MIN_DEGRADATION,
) -> list[FailureObservation]:
    """Run every failure detector and return the combined, sorted observations."""
    observations = [
        *budget_failures(aggregation, threshold=budget_threshold),
        *benchmark_failures(aggregation, gap_threshold=gap_threshold),
        *metric_degradation(aggregation, min_degradation=min_degradation),
    ]
    observations.sort(
        key=lambda o: (o.strategy_id, o.benchmark_id, o.mode.value, o.metric)
    )
    return observations
