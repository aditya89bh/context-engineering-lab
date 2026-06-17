"""Stability calculations.

Three complementary views of how *steady* the synthesis is:

* **Seed variance** — how much a strategy's quality cells move across seeds
  (the per-cell population standard deviation already recorded by aggregation).
* **Budget sensitivity** — how far a strategy's primary metric swings across the
  budget sweep.
* **Ranking volatility** — how much the strategy ordering on a benchmark's
  primary metric reshuffles between adjacent budgets (a normalized Kendall-tau
  distance over shared strategies).

Lower numbers mean steadier results in every case.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, pairwise
from statistics import fmean

from context_engineering_lab.synthesis.aggregation import (
    Aggregation,
    is_quality_metric,
)


@dataclass(frozen=True, slots=True)
class StabilityReport:
    """Per-strategy stability across seeds and budgets.

    Args:
        strategy_id: The strategy.
        seed_variance: Mean per-cell standard deviation across seeds over the
            strategy's quality cells, or ``None`` when it has none.
        budget_sensitivity: Mean primary-metric range across budgets over the
            strategy's benchmarks, or ``None`` when no benchmark has >1 budget.
    """

    strategy_id: str
    seed_variance: float | None
    budget_sensitivity: float | None


@dataclass(frozen=True, slots=True)
class RankingVolatility:
    """How much a benchmark's strategy ranking shifts across budgets.

    Args:
        benchmark_id: The benchmark.
        metric: The primary metric used to rank strategies.
        volatility: Mean fraction of discordant strategy pairs between adjacent
            budgets (0 stable, 1 fully reversed), or ``None`` when undefined.
    """

    benchmark_id: str
    metric: str
    volatility: float | None


def seed_variance(aggregation: Aggregation, strategy_id: str) -> float | None:
    """Mean across-seed standard deviation over a strategy's quality cells."""
    stddevs = [
        cell.stddev
        for cell in aggregation.filter(strategy_id=strategy_id)
        if is_quality_metric(cell.metric)
    ]
    return fmean(stddevs) if stddevs else None


def budget_sensitivity(
    aggregation: Aggregation, strategy_id: str
) -> float | None:
    """Mean primary-metric range across budgets, over a strategy's benchmarks."""
    ranges: list[float] = []
    for benchmark_id in aggregation.benchmarks():
        metric = aggregation.benchmark_aggregate(benchmark_id).primary_metric()
        if metric is None:
            continue
        values = [
            cell.mean
            for cell in aggregation.filter(
                benchmark_id=benchmark_id, strategy_id=strategy_id, metric=metric
            )
        ]
        if len(values) >= 2:
            ranges.append(max(values) - min(values))
    return fmean(ranges) if ranges else None


def strategy_stability(
    aggregation: Aggregation, strategy_id: str
) -> StabilityReport:
    """Build a :class:`StabilityReport` for one strategy."""
    return StabilityReport(
        strategy_id=strategy_id,
        seed_variance=seed_variance(aggregation, strategy_id),
        budget_sensitivity=budget_sensitivity(aggregation, strategy_id),
    )


def stability_reports(aggregation: Aggregation) -> list[StabilityReport]:
    """Stability reports for every strategy, in sorted order."""
    return [
        strategy_stability(aggregation, strategy_id)
        for strategy_id in aggregation.strategies()
    ]


def _discordant_fraction(
    order_a: dict[str, float], order_b: dict[str, float]
) -> float | None:
    common = sorted(order_a.keys() & order_b.keys())
    pairs = list(combinations(common, 2))
    if not pairs:
        return None
    discordant = 0
    for left, right in pairs:
        delta_a = order_a[left] - order_a[right]
        delta_b = order_b[left] - order_b[right]
        if delta_a * delta_b < 0:
            discordant += 1
    return discordant / len(pairs)


def ranking_volatility(
    aggregation: Aggregation, benchmark_id: str
) -> RankingVolatility | None:
    """Mean ranking discordance between adjacent budgets on a benchmark.

    Args:
        aggregation: The aggregated cells.
        benchmark_id: The benchmark to assess.

    Returns:
        A :class:`RankingVolatility`, or ``None`` when the benchmark has no
        primary metric.
    """
    metric = aggregation.benchmark_aggregate(benchmark_id).primary_metric()
    if metric is None:
        return None
    cells = aggregation.filter(benchmark_id=benchmark_id, metric=metric)
    by_budget: dict[int, dict[str, float]] = {}
    for cell in cells:
        by_budget.setdefault(cell.budget_limit, {})[cell.strategy_id] = cell.mean
    budgets = sorted(by_budget)
    fractions = [
        fraction
        for low, high in pairwise(budgets)
        if (fraction := _discordant_fraction(by_budget[low], by_budget[high]))
        is not None
    ]
    return RankingVolatility(
        benchmark_id=benchmark_id,
        metric=metric,
        volatility=fmean(fractions) if fractions else None,
    )


def ranking_volatilities(aggregation: Aggregation) -> list[RankingVolatility]:
    """Ranking volatility for every benchmark that has a primary metric."""
    results: list[RankingVolatility] = []
    for benchmark_id in aggregation.benchmarks():
        volatility = ranking_volatility(aggregation, benchmark_id)
        if volatility is not None:
            results.append(volatility)
    return results
