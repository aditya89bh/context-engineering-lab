"""Oracle-gap calculation utilities.

Measures how far each strategy sits below the oracle ceiling. Gaps are computed
per ``(benchmark, metric, budget)`` cell on the quality metrics, oriented so that
the gap is non-negative when the oracle is at least as good (which it should be).
The oracle value at a cell is the best among any oracle strategies present there.

Per-strategy normalized summaries build on these gaps in a companion section.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import fmean

from context_engineering_lab.synthesis.aggregation import (
    Aggregation,
    Direction,
    direction,
    is_quality_metric,
)
from context_engineering_lab.synthesis.dominance import (
    CellKey,
    oriented_quality_cells,
)
from context_engineering_lab.synthesis.profiles import (
    is_oracle_id,
    oracle_primary_score,
    primary_scores,
)


@dataclass(frozen=True, slots=True)
class OracleGap:
    """The gap from one strategy to the oracle at a single cell.

    Args:
        benchmark_id: The benchmark.
        strategy_id: The strategy.
        metric: The quality metric.
        budget_limit: The budget limit.
        strategy_value: The strategy's raw mean at the cell.
        oracle_value: The best oracle's raw mean at the cell.
        gap: Oriented oracle minus oriented strategy (non-negative when the
            oracle is at least as good).
    """

    benchmark_id: str
    strategy_id: str
    metric: str
    budget_limit: int
    strategy_value: float
    oracle_value: float
    gap: float


def oracle_oriented_cells(aggregation: Aggregation) -> dict[CellKey, float]:
    """Best oriented value among oracle strategies, per quality cell.

    Args:
        aggregation: The aggregated cells.

    Returns:
        A dict from ``(benchmark, metric, budget)`` to the best oracle oriented
        value at that cell.
    """
    best: dict[CellKey, float] = {}
    for strategy_id in aggregation.strategies():
        if not is_oracle_id(strategy_id):
            continue
        for key, value in oriented_quality_cells(aggregation, strategy_id).items():
            best[key] = max(best.get(key, -math.inf), value)
    return best


def _deorient(metric: str, oriented: float) -> float:
    return -oriented if direction(metric) is Direction.LOWER_IS_BETTER else oriented


def gaps_for_strategy(
    aggregation: Aggregation, strategy_id: str
) -> list[OracleGap]:
    """Compute every oracle gap for one strategy.

    Only quality cells that also have an oracle value are included.

    Args:
        aggregation: The aggregated cells.
        strategy_id: The strategy to measure.

    Returns:
        Gaps sorted by ``(benchmark, metric, budget)``.
    """
    oracle_cells = oracle_oriented_cells(aggregation)
    gaps: list[OracleGap] = []
    for cell in aggregation.filter(strategy_id=strategy_id):
        if not is_quality_metric(cell.metric):
            continue
        key = (cell.benchmark_id, cell.metric, cell.budget_limit)
        oracle_oriented = oracle_cells.get(key)
        if oracle_oriented is None:
            continue
        strategy_oriented = cell.mean
        if cell.direction is Direction.LOWER_IS_BETTER:
            strategy_oriented = -strategy_oriented
        gaps.append(
            OracleGap(
                benchmark_id=cell.benchmark_id,
                strategy_id=strategy_id,
                metric=cell.metric,
                budget_limit=cell.budget_limit,
                strategy_value=cell.mean,
                oracle_value=_deorient(cell.metric, oracle_oriented),
                gap=oracle_oriented - strategy_oriented,
            )
        )
    gaps.sort(key=lambda g: (g.benchmark_id, g.metric, g.budget_limit))
    return gaps


@dataclass(frozen=True, slots=True)
class OracleSummary:
    """An oracle-normalized summary of one strategy.

    Args:
        strategy_id: The strategy summarised.
        mean_gap: Mean gap across all quality cells with an oracle, or ``None``.
        mean_primary_gap: Mean primary-metric gap across benchmarks, or ``None``.
        normalized: Mean of ``strategy_primary / oracle_primary`` across
            benchmarks (1.0 means it matches the oracle), or ``None``.
        cell_count: Number of quality cells that had an oracle to compare to.
    """

    strategy_id: str
    mean_gap: float | None
    mean_primary_gap: float | None
    normalized: float | None
    cell_count: int


def oracle_summary(aggregation: Aggregation, strategy_id: str) -> OracleSummary:
    """Build an oracle-normalized summary for one strategy.

    Args:
        aggregation: The aggregated cells.
        strategy_id: The strategy to summarise.

    Returns:
        The :class:`OracleSummary`.
    """
    gaps = gaps_for_strategy(aggregation, strategy_id)
    mean_gap = fmean(gap.gap for gap in gaps) if gaps else None

    primary_gaps: list[float] = []
    ratios: list[float] = []
    for benchmark_id, (_metric, score) in primary_scores(
        aggregation, strategy_id
    ).items():
        ceiling = oracle_primary_score(aggregation, benchmark_id)
        if ceiling is None:
            continue
        primary_gaps.append(ceiling - score)
        if ceiling > 0:
            ratios.append(score / ceiling)

    return OracleSummary(
        strategy_id=strategy_id,
        mean_gap=mean_gap,
        mean_primary_gap=fmean(primary_gaps) if primary_gaps else None,
        normalized=fmean(ratios) if ratios else None,
        cell_count=len(gaps),
    )


def oracle_summaries(aggregation: Aggregation) -> list[OracleSummary]:
    """Summaries for every strategy, best normalized score first.

    Strategies without a normalized score (no oracle to compare to) sort last.

    Args:
        aggregation: The aggregated cells.

    Returns:
        The per-strategy summaries.
    """
    summaries = [
        oracle_summary(aggregation, strategy_id)
        for strategy_id in aggregation.strategies()
    ]
    summaries.sort(
        key=lambda s: (
            -(s.normalized if s.normalized is not None else -math.inf),
            s.strategy_id,
        )
    )
    return summaries
