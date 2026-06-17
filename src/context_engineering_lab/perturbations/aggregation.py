"""Robustness aggregation utilities.

Turns the raw Phase 10 experiment results (baseline and perturbed runs) into the
structured rows the report and CLI consume:

* :class:`GroupComparison` — a :class:`PerturbationComparison` tagged with its
  stress group.
* :class:`OracleGapShift` — how far a strategy sits from the oracle ceiling on a
  benchmark's primary metric, baseline vs perturbed, and whether that gap widened.

Everything is derived mechanically from a single
:class:`~context_engineering_lab.synthesis.aggregation.Aggregation` over all runs;
baseline and perturbed cells are told apart by benchmark id (the perturbed id is
``"<base>+<perturbation>"``).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.experiments.phase10 import RobustnessSpec
from context_engineering_lab.perturbations.comparison import (
    PerturbationComparison,
    compare_perturbation,
)
from context_engineering_lab.synthesis.aggregation import (
    Aggregation,
    Direction,
    aggregate_results,
    direction,
)
from context_engineering_lab.synthesis.profiles import is_oracle_id


@dataclass(frozen=True, slots=True)
class GroupComparison:
    """A perturbation comparison tagged with its stress group."""

    group: str
    comparison: PerturbationComparison


@dataclass(frozen=True, slots=True)
class OracleGapShift:
    """How a strategy's distance from the oracle changes under perturbation.

    Args:
        group: The stress group.
        benchmark_id: The baseline benchmark id.
        perturbation_id: The perturbation applied.
        strategy_id: The (non-oracle) strategy.
        metric: The benchmark's primary quality metric.
        baseline_gap: Oriented oracle score minus the strategy's, unperturbed.
        perturbed_gap: The same gap under perturbation.
        gap_increase: ``perturbed_gap - baseline_gap`` (positive: the gap widened).
    """

    group: str
    benchmark_id: str
    perturbation_id: str
    strategy_id: str
    metric: str
    baseline_gap: float
    perturbed_gap: float
    gap_increase: float


@dataclass(frozen=True, slots=True)
class RobustnessAggregation:
    """All robustness rows derived from the Phase 10 runs."""

    aggregation: Aggregation
    comparisons: tuple[GroupComparison, ...]
    oracle_shifts: tuple[OracleGapShift, ...]

    def groups(self) -> list[str]:
        """Sorted stress-group names present."""
        return sorted({row.group for row in self.comparisons})

    def perturbations(self) -> list[str]:
        """Sorted perturbation ids present."""
        return sorted({row.comparison.perturbation_id for row in self.comparisons})

    def for_group(self, group: str) -> list[GroupComparison]:
        """Comparisons belonging to one stress group."""
        return [row for row in self.comparisons if row.group == group]


def _oriented(metric: str, value: float) -> float:
    if direction(metric) is Direction.LOWER_IS_BETTER:
        return -value
    return value


def _oracle_gap(
    aggregation: Aggregation, benchmark_id: str, strategy_id: str, metric: str
) -> float | None:
    """Oriented oracle-minus-strategy gap on a benchmark's metric, or ``None``."""
    oracles = [
        s for s in aggregation.benchmark_aggregate(benchmark_id).strategies()
        if is_oracle_id(s)
    ]
    if not oracles:
        return None
    oracle_values = [
        aggregation.mean_over_budgets(benchmark_id, oracle, metric)
        for oracle in oracles
    ]
    present = [v for v in oracle_values if v is not None]
    strategy_value = aggregation.mean_over_budgets(benchmark_id, strategy_id, metric)
    if not present or strategy_value is None:
        return None
    best_oracle = max(_oriented(metric, v) for v in present)
    return best_oracle - _oriented(metric, strategy_value)


def _oracle_gap_shifts(
    aggregation: Aggregation, spec: RobustnessSpec
) -> list[OracleGapShift]:
    base_id = str(spec.benchmark.id)
    metric = aggregation.benchmark_aggregate(base_id).primary_metric()
    if metric is None:
        return []
    shifts: list[OracleGapShift] = []
    for perturbation_id in spec.perturbations:
        pert_id = f"{base_id}+{perturbation_id}"
        for strategy_id in aggregation.benchmark_aggregate(base_id).strategies():
            if is_oracle_id(strategy_id):
                continue
            baseline_gap = _oracle_gap(aggregation, base_id, strategy_id, metric)
            perturbed_gap = _oracle_gap(aggregation, pert_id, strategy_id, metric)
            if baseline_gap is None or perturbed_gap is None:
                continue
            shifts.append(
                OracleGapShift(
                    group=spec.group,
                    benchmark_id=base_id,
                    perturbation_id=perturbation_id,
                    strategy_id=strategy_id,
                    metric=metric,
                    baseline_gap=baseline_gap,
                    perturbed_gap=perturbed_gap,
                    gap_increase=perturbed_gap - baseline_gap,
                )
            )
    return shifts


def aggregate_robustness(
    results: Sequence[ExperimentResult],
    specs: Sequence[RobustnessSpec],
) -> RobustnessAggregation:
    """Aggregate baseline/perturbed results into robustness rows.

    Args:
        results: All Phase 10 experiment results (baseline and perturbed).
        specs: The stress groups describing how the runs pair up.

    Returns:
        A :class:`RobustnessAggregation` with per-(group, perturbation, strategy,
        metric) comparisons and oracle-gap shifts, all deterministically ordered.
    """
    aggregation = aggregate_results(results)
    comparisons: list[GroupComparison] = []
    oracle_shifts: list[OracleGapShift] = []
    for spec in specs:
        base_id = str(spec.benchmark.id)
        for perturbation_id in spec.perturbations:
            pert_id = f"{base_id}+{perturbation_id}"
            for comparison in compare_perturbation(
                aggregation,
                aggregation,
                baseline_benchmark=base_id,
                perturbed_benchmark=pert_id,
                perturbation_id=perturbation_id,
            ):
                comparisons.append(
                    GroupComparison(group=spec.group, comparison=comparison)
                )
        oracle_shifts.extend(_oracle_gap_shifts(aggregation, spec))
    return RobustnessAggregation(
        aggregation=aggregation,
        comparisons=tuple(comparisons),
        oracle_shifts=tuple(oracle_shifts),
    )
