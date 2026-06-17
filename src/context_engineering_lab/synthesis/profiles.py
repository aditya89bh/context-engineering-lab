"""Strategy profile models.

A :class:`StrategyProfile` summarises how one strategy fared across the benchmarks
it was evaluated on, using each benchmark's primary quality metric (always
higher-is-better). The supporting records name the benchmarks where a strategy was
strongest or weakest and the budgets where it did best or worst. Generation lives
alongside these models; this section defines only the data shapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean

from context_engineering_lab.synthesis.aggregation import Aggregation


@dataclass(frozen=True, slots=True)
class StrengthRecord:
    """A benchmark where a strategy scored relatively well.

    Args:
        benchmark_id: The benchmark.
        metric: The benchmark's primary quality metric.
        score: The strategy's mean of that metric over budgets (higher is better).
    """

    benchmark_id: str
    metric: str
    score: float


@dataclass(frozen=True, slots=True)
class WeaknessRecord:
    """A benchmark where a strategy scored relatively poorly.

    Args:
        benchmark_id: The benchmark.
        metric: The benchmark's primary quality metric.
        score: The strategy's mean of that metric over budgets (higher is better).
    """

    benchmark_id: str
    metric: str
    score: float


@dataclass(frozen=True, slots=True)
class BudgetScore:
    """A strategy's mean primary-metric score at one budget limit.

    Args:
        budget_limit: The budget limit (numeric; units may differ by benchmark).
        score: Mean primary-metric score across benchmarks at this budget.
        benchmark_count: How many benchmarks contributed at this budget.
    """

    budget_limit: int
    score: float
    benchmark_count: int


@dataclass(frozen=True, slots=True)
class StrategyProfile:
    """A cross-benchmark summary of one strategy.

    Args:
        strategy_id: The strategy summarised.
        benchmarks: Sorted benchmark ids the strategy was evaluated on.
        mean_primary: Mean primary-metric score across those benchmarks, or
            ``None`` when no benchmark exposes a primary metric.
        strengths: The strongest benchmarks (highest primary score first).
        weaknesses: The weakest benchmarks (lowest primary score first).
        best_budgets: Budgets with the highest mean primary score first.
        worst_budgets: Budgets with the lowest mean primary score first.
        oracle_distance: Mean gap to each benchmark's oracle on the primary
            metric, or ``None`` when not computed or no oracle is present.
    """

    strategy_id: str
    benchmarks: tuple[str, ...]
    mean_primary: float | None
    strengths: tuple[StrengthRecord, ...]
    weaknesses: tuple[WeaknessRecord, ...]
    best_budgets: tuple[BudgetScore, ...]
    worst_budgets: tuple[BudgetScore, ...]
    oracle_distance: float | None = None


def primary_scores(
    aggregation: Aggregation, strategy_id: str
) -> dict[str, tuple[str, float]]:
    """Map each benchmark to its ``(primary_metric, score)`` for one strategy.

    The score is the mean of the primary metric's cell means over budgets. Only
    benchmarks that expose a primary metric and have data for the strategy appear.

    Args:
        aggregation: The aggregated cells.
        strategy_id: The strategy to score.

    Returns:
        A dict keyed by benchmark id.
    """
    scores: dict[str, tuple[str, float]] = {}
    for benchmark_id in aggregation.benchmarks():
        metric = aggregation.benchmark_aggregate(benchmark_id).primary_metric()
        if metric is None:
            continue
        score = aggregation.mean_over_budgets(benchmark_id, strategy_id, metric)
        if score is None:
            continue
        scores[benchmark_id] = (metric, score)
    return scores


def strongest_benchmarks(
    aggregation: Aggregation, strategy_id: str, *, top_k: int = 3
) -> list[StrengthRecord]:
    """Return the benchmarks where a strategy scored highest on the primary metric."""
    scores = primary_scores(aggregation, strategy_id)
    ranked = sorted(scores.items(), key=lambda item: (-item[1][1], item[0]))
    return [
        StrengthRecord(benchmark_id=benchmark_id, metric=metric, score=score)
        for benchmark_id, (metric, score) in ranked[:top_k]
    ]


def weakest_benchmarks(
    aggregation: Aggregation, strategy_id: str, *, top_k: int = 3
) -> list[WeaknessRecord]:
    """Return the benchmarks where a strategy scored lowest on the primary metric."""
    scores = primary_scores(aggregation, strategy_id)
    ranked = sorted(scores.items(), key=lambda item: (item[1][1], item[0]))
    return [
        WeaknessRecord(benchmark_id=benchmark_id, metric=metric, score=score)
        for benchmark_id, (metric, score) in ranked[:top_k]
    ]


def budget_scores(aggregation: Aggregation, strategy_id: str) -> list[BudgetScore]:
    """Mean primary-metric score per budget limit, across benchmarks.

    Budgets are compared by numeric limit; units may differ between benchmarks
    (items vs tokens), so a budget limit may aggregate only a subset of
    benchmarks. ``benchmark_count`` records how many contributed.
    """
    by_budget: dict[int, list[float]] = {}
    for benchmark_id in aggregation.benchmarks():
        metric = aggregation.benchmark_aggregate(benchmark_id).primary_metric()
        if metric is None:
            continue
        for cell in aggregation.filter(
            benchmark_id=benchmark_id, strategy_id=strategy_id, metric=metric
        ):
            by_budget.setdefault(cell.budget_limit, []).append(cell.mean)
    return [
        BudgetScore(
            budget_limit=limit,
            score=fmean(values),
            benchmark_count=len(values),
        )
        for limit, values in sorted(by_budget.items())
    ]


def generate_profile(
    aggregation: Aggregation, strategy_id: str, *, top_k: int = 3
) -> StrategyProfile:
    """Build a :class:`StrategyProfile` for one strategy.

    Args:
        aggregation: The aggregated cells.
        strategy_id: The strategy to profile.
        top_k: How many strengths/weaknesses/budgets to retain at each end.

    Returns:
        The profile (without oracle distance, which is attached separately).
    """
    scores = primary_scores(aggregation, strategy_id)
    means = [score for _metric, score in scores.values()]
    budgets = budget_scores(aggregation, strategy_id)
    return StrategyProfile(
        strategy_id=strategy_id,
        benchmarks=tuple(sorted(scores)),
        mean_primary=fmean(means) if means else None,
        strengths=tuple(strongest_benchmarks(aggregation, strategy_id, top_k=top_k)),
        weaknesses=tuple(weakest_benchmarks(aggregation, strategy_id, top_k=top_k)),
        best_budgets=tuple(
            sorted(budgets, key=lambda b: (-b.score, b.budget_limit))[:top_k]
        ),
        worst_budgets=tuple(
            sorted(budgets, key=lambda b: (b.score, b.budget_limit))[:top_k]
        ),
    )


def generate_profiles(
    aggregation: Aggregation, *, top_k: int = 3
) -> list[StrategyProfile]:
    """Build profiles for every strategy in the aggregation, in sorted order."""
    return [
        generate_profile(aggregation, strategy_id, top_k=top_k)
        for strategy_id in aggregation.strategies()
    ]
