"""Pairwise comparison utilities for dominance analysis.

Compares two strategies cell by cell on the *quality* metrics they share. Each
metric is oriented so that larger is better (cost metrics are negated), and only
``(benchmark, metric, budget)`` cells present for *both* strategies are compared,
so strategies evaluated on disjoint benchmarks simply have nothing to compare.

This module provides the per-pair primitive; the dominance engine and the
non-dominated analysis build on it.
"""

from __future__ import annotations

from dataclasses import dataclass

from context_engineering_lab.synthesis.aggregation import (
    Aggregation,
    Direction,
    is_quality_metric,
)

#: Differences at or below this are treated as ties.
DEFAULT_EPS = 1e-9

#: A cell key: ``(benchmark_id, metric, budget_limit)``.
CellKey = tuple[str, str, int]


@dataclass(frozen=True, slots=True)
class PairComparison:
    """How strategy ``a`` compares to strategy ``b`` on their shared cells.

    Args:
        strategy_a: The first strategy.
        strategy_b: The second strategy.
        wins: Shared cells where ``a`` is better than ``b``.
        losses: Shared cells where ``a`` is worse than ``b``.
        ties: Shared cells where the two are within ``eps``.
    """

    strategy_a: str
    strategy_b: str
    wins: int
    losses: int
    ties: int

    @property
    def shared(self) -> int:
        """Number of shared cells compared."""
        return self.wins + self.losses + self.ties


def oriented_quality_cells(
    aggregation: Aggregation, strategy_id: str
) -> dict[CellKey, float]:
    """Return a strategy's quality cells, oriented so higher is better.

    Cost metrics (lower-is-better) are negated; neutral metrics are dropped.

    Args:
        aggregation: The aggregated cells.
        strategy_id: The strategy whose cells to orient.

    Returns:
        A dict from ``(benchmark, metric, budget)`` to an oriented value.
    """
    oriented: dict[CellKey, float] = {}
    for cell in aggregation.filter(strategy_id=strategy_id):
        if not is_quality_metric(cell.metric):
            continue
        value = cell.mean
        if cell.direction is Direction.LOWER_IS_BETTER:
            value = -value
        oriented[(cell.benchmark_id, cell.metric, cell.budget_limit)] = value
    return oriented


def compare_pair(
    aggregation: Aggregation,
    strategy_a: str,
    strategy_b: str,
    *,
    eps: float = DEFAULT_EPS,
) -> PairComparison:
    """Compare two strategies cell by cell on their shared quality cells.

    Args:
        aggregation: The aggregated cells.
        strategy_a: The first strategy.
        strategy_b: The second strategy.
        eps: Differences at or below this count as ties.

    Returns:
        A :class:`PairComparison` of ``a`` against ``b``.
    """
    cells_a = oriented_quality_cells(aggregation, strategy_a)
    cells_b = oriented_quality_cells(aggregation, strategy_b)
    wins = losses = ties = 0
    for key in cells_a.keys() & cells_b.keys():
        diff = cells_a[key] - cells_b[key]
        if diff > eps:
            wins += 1
        elif diff < -eps:
            losses += 1
        else:
            ties += 1
    return PairComparison(
        strategy_a=strategy_a,
        strategy_b=strategy_b,
        wins=wins,
        losses=losses,
        ties=ties,
    )
