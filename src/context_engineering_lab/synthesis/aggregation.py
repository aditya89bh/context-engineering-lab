"""Aggregation models and metric orientation.

Collapses the per-seed metric values inside a set of
:class:`~context_engineering_lab.core.results.ExperimentResult` artifacts into one
cell per ``(benchmark, strategy, metric, budget)``, aggregated across seeds. It
also records each metric's *orientation* (higher-is-better, lower-is-better, or
neutral), which every downstream analysis needs to compare strategies sensibly.

No new metric is introduced; this only classifies the metrics the Phase 2-8
benchmarks already emit.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from statistics import fmean, pstdev

from context_engineering_lab.core.results import ExperimentResult


class Direction(Enum):
    """Whether a larger metric value is better, worse, or neither."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"


# Orientation of every metric the Phase 2-8 benchmarks emit. Quality metrics are
# higher-is-better; cost metrics are lower-is-better; utilisation/ratio/age
# metrics are neutral (a target band, not a direction) and excluded from ranking.
METRIC_DIRECTION: dict[str, Direction] = {
    "answer_support": Direction.HIGHER_IS_BETTER,
    "answer_support_after_compression": Direction.HIGHER_IS_BETTER,
    "selection_recall": Direction.HIGHER_IS_BETTER,
    "selection_precision": Direction.HIGHER_IS_BETTER,
    "information_retention": Direction.HIGHER_IS_BETTER,
    "temporal_relevance": Direction.HIGHER_IS_BETTER,
    "retention_precision": Direction.HIGHER_IS_BETTER,
    "retention_recall": Direction.HIGHER_IS_BETTER,
    "useful_retention_rate": Direction.HIGHER_IS_BETTER,
    "forgetting_efficiency": Direction.HIGHER_IS_BETTER,
    "allocation_efficiency": Direction.HIGHER_IS_BETTER,
    "signal_capture_rate": Direction.HIGHER_IS_BETTER,
    "source_coverage": Direction.HIGHER_IS_BETTER,
    "current_truth_support": Direction.HIGHER_IS_BETTER,
    "pipeline_efficiency": Direction.HIGHER_IS_BETTER,
    "distractor_retention": Direction.LOWER_IS_BETTER,
    "stale_selection_rate": Direction.LOWER_IS_BETTER,
    "relevant_age_gap": Direction.LOWER_IS_BETTER,
    "harmful_retention_rate": Direction.LOWER_IS_BETTER,
    "wasted_attention_rate": Direction.LOWER_IS_BETTER,
    "superseded_fact_retention": Direction.LOWER_IS_BETTER,
    "conflict_selection_rate": Direction.LOWER_IS_BETTER,
    "budget_utilization": Direction.NEUTRAL,
    "memory_budget_utilization": Direction.NEUTRAL,
    "compression_ratio": Direction.NEUTRAL,
    "age_of_selected_context": Direction.NEUTRAL,
}

# Priority order for choosing a benchmark's single primary quality metric: the
# first present metric wins. All are higher-is-better.
_PRIMARY_PRIORITY: tuple[str, ...] = (
    "answer_support",
    "answer_support_after_compression",
    "current_truth_support",
    "retention_recall",
    "useful_retention_rate",
    "signal_capture_rate",
    "temporal_relevance",
    "allocation_efficiency",
    "selection_recall",
    "information_retention",
)


def direction(metric: str) -> Direction:
    """Return a metric's orientation, defaulting to neutral when unknown."""
    return METRIC_DIRECTION.get(metric, Direction.NEUTRAL)


def is_quality_metric(metric: str) -> bool:
    """Whether a metric has a ranking direction (is not neutral)."""
    return direction(metric) is not Direction.NEUTRAL


def primary_metric(metrics: Sequence[str]) -> str | None:
    """Pick the primary quality metric from those available.

    Args:
        metrics: Metric names available for a benchmark.

    Returns:
        The first metric in the priority order that is present, or ``None`` if
        none of the priority metrics are available.
    """
    available = set(metrics)
    for candidate in _PRIMARY_PRIORITY:
        if candidate in available:
            return candidate
    return None


@dataclass(frozen=True, slots=True)
class AggregatedResult:
    """One ``(benchmark, strategy, metric, budget)`` cell, aggregated over seeds.

    Args:
        benchmark_id: The benchmark the cell belongs to.
        strategy_id: The strategy the cell belongs to.
        metric: The metric name.
        budget_limit: The budget limit for the cell.
        budget_unit: The budget unit for the cell.
        mean: Mean of the per-seed values.
        stddev: Population standard deviation across the per-seed values.
        seed_count: How many seeds contributed.
    """

    benchmark_id: str
    strategy_id: str
    metric: str
    budget_limit: int
    budget_unit: str
    mean: float
    stddev: float
    seed_count: int

    @property
    def direction(self) -> Direction:
        """Orientation of this cell's metric."""
        return direction(self.metric)


@dataclass(frozen=True, slots=True)
class StrategyAggregate:
    """A view of one strategy's cells across benchmarks."""

    strategy_id: str
    cells: tuple[AggregatedResult, ...]

    def benchmarks(self) -> list[str]:
        """Sorted benchmark ids this strategy was evaluated on."""
        return sorted({cell.benchmark_id for cell in self.cells})

    def metrics(self) -> list[str]:
        """Sorted metric names recorded for this strategy."""
        return sorted({cell.metric for cell in self.cells})

    def mean_over_budgets(self, benchmark_id: str, metric: str) -> float | None:
        """Mean of a metric's cell means over budgets on one benchmark."""
        values = [
            cell.mean
            for cell in self.cells
            if cell.benchmark_id == benchmark_id and cell.metric == metric
        ]
        return fmean(values) if values else None


@dataclass(frozen=True, slots=True)
class BenchmarkAggregate:
    """A view of one benchmark's cells across strategies."""

    benchmark_id: str
    version: str
    cells: tuple[AggregatedResult, ...]

    def strategies(self) -> list[str]:
        """Sorted strategy ids evaluated on this benchmark."""
        return sorted({cell.strategy_id for cell in self.cells})

    def metrics(self) -> list[str]:
        """Sorted metric names recorded for this benchmark."""
        return sorted({cell.metric for cell in self.cells})

    def budget_limits(self) -> list[int]:
        """Sorted, unique budget limits recorded for this benchmark."""
        return sorted({cell.budget_limit for cell in self.cells})

    def primary_metric(self) -> str | None:
        """The benchmark's primary quality metric, if any."""
        return primary_metric(self.metrics())


@dataclass(frozen=True, slots=True)
class Aggregation:
    """All aggregated cells from a set of artifacts, with lookup helpers."""

    cells: tuple[AggregatedResult, ...]
    benchmark_versions: Mapping[str, str]

    def benchmarks(self) -> list[str]:
        """Sorted benchmark ids present."""
        return sorted({cell.benchmark_id for cell in self.cells})

    def strategies(self) -> list[str]:
        """Sorted strategy ids present."""
        return sorted({cell.strategy_id for cell in self.cells})

    def metrics(self) -> list[str]:
        """Sorted metric names present."""
        return sorted({cell.metric for cell in self.cells})

    def filter(
        self,
        *,
        benchmark_id: str | None = None,
        strategy_id: str | None = None,
        metric: str | None = None,
    ) -> list[AggregatedResult]:
        """Return cells matching the given (optional) coordinates."""
        return [
            cell
            for cell in self.cells
            if (benchmark_id is None or cell.benchmark_id == benchmark_id)
            and (strategy_id is None or cell.strategy_id == strategy_id)
            and (metric is None or cell.metric == metric)
        ]

    def get(
        self, benchmark_id: str, strategy_id: str, metric: str, budget_limit: int
    ) -> AggregatedResult | None:
        """Return one specific cell, or ``None`` when absent."""
        for cell in self.cells:
            if (
                cell.benchmark_id == benchmark_id
                and cell.strategy_id == strategy_id
                and cell.metric == metric
                and cell.budget_limit == budget_limit
            ):
                return cell
        return None

    def mean_over_budgets(
        self, benchmark_id: str, strategy_id: str, metric: str
    ) -> float | None:
        """Mean of a metric's cell means over budgets for one strategy/benchmark."""
        values = [
            cell.mean
            for cell in self.filter(
                benchmark_id=benchmark_id, strategy_id=strategy_id, metric=metric
            )
        ]
        return fmean(values) if values else None

    def strategy_aggregate(self, strategy_id: str) -> StrategyAggregate:
        """A :class:`StrategyAggregate` view for one strategy."""
        return StrategyAggregate(
            strategy_id=strategy_id,
            cells=tuple(self.filter(strategy_id=strategy_id)),
        )

    def benchmark_aggregate(self, benchmark_id: str) -> BenchmarkAggregate:
        """A :class:`BenchmarkAggregate` view for one benchmark."""
        return BenchmarkAggregate(
            benchmark_id=benchmark_id,
            version=self.benchmark_versions.get(benchmark_id, ""),
            cells=tuple(self.filter(benchmark_id=benchmark_id)),
        )


def aggregate_results(results: Sequence[ExperimentResult]) -> Aggregation:
    """Aggregate per-seed metric values into one cell per coordinate.

    Cells are keyed by ``(benchmark, strategy, metric, budget)`` and aggregate the
    per-seed values across every artifact that shares the key, so duplicate or
    split runs merge cleanly.

    Args:
        results: The experiment results to aggregate.

    Returns:
        An :class:`Aggregation` with cells sorted by coordinate.
    """
    buckets: dict[tuple[str, str, str, int, str], list[float]] = {}
    versions: dict[str, str] = {}
    for result in results:
        benchmark_id = result.metadata.benchmark_id
        versions[benchmark_id] = result.metadata.benchmark_version
        for run in result.results:
            for metric in run.metrics:
                key = (
                    benchmark_id,
                    run.strategy_id,
                    metric.name,
                    metric.budget_limit,
                    metric.budget_unit,
                )
                buckets.setdefault(key, []).append(metric.value)

    cells: list[AggregatedResult] = []
    for (bench, strategy, metric_name, limit, unit), values in buckets.items():
        cells.append(
            AggregatedResult(
                benchmark_id=bench,
                strategy_id=strategy,
                metric=metric_name,
                budget_limit=limit,
                budget_unit=unit,
                mean=fmean(values),
                stddev=pstdev(values) if len(values) > 1 else 0.0,
                seed_count=len(values),
            )
        )
    cells.sort(
        key=lambda c: (c.benchmark_id, c.strategy_id, c.metric, c.budget_limit)
    )
    return Aggregation(cells=tuple(cells), benchmark_versions=dict(versions))
