"""Strategy profile models.

A :class:`StrategyProfile` summarises how one strategy fared across the benchmarks
it was evaluated on, using each benchmark's primary quality metric (always
higher-is-better). The supporting records name the benchmarks where a strategy was
strongest or weakest and the budgets where it did best or worst. Generation lives
alongside these models; this section defines only the data shapes.
"""

from __future__ import annotations

from dataclasses import dataclass


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
