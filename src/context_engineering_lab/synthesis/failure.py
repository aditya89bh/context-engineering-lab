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
