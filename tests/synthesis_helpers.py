"""Shared builders for Phase 9 synthesis tests.

Not a test module (the name does not match ``test_*``), so pytest does not collect
it. It assembles small, fully synthetic :class:`ExperimentResult` objects so the
synthesis tests do not need to run the real Phase 2-8 suites.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.metadata import build_run_metadata
from context_engineering_lab.core.results import (
    ExperimentResult,
    MetricValue,
    StrategyRunResult,
)


def metric(
    name: str,
    value: float,
    seed: int,
    budget_limit: int,
    *,
    unit: str = "items",
    sample_size: int = 10,
    stddev: float = 0.0,
) -> MetricValue:
    """Build a single :class:`MetricValue`."""
    return MetricValue(
        name=name,
        value=value,
        seed=seed,
        budget_limit=budget_limit,
        budget_unit=unit,
        sample_size=sample_size,
        stddev=stddev,
    )


def run(strategy_id: str, metrics: Sequence[MetricValue]) -> StrategyRunResult:
    """Build a :class:`StrategyRunResult` from metric values."""
    return StrategyRunResult(strategy_id=strategy_id, metrics=tuple(metrics))


def result(
    benchmark_id: str,
    runs: Sequence[StrategyRunResult],
    *,
    version: str = "1.0",
    experiment_id: str | None = None,
    seeds: Sequence[int] = (1, 2, 3),
    budget_limits: Sequence[int] = (2, 4),
    unit: BudgetUnit = BudgetUnit.ITEMS,
) -> ExperimentResult:
    """Build an :class:`ExperimentResult` with deterministic metadata."""
    budgets = tuple(Budget(limit, unit) for limit in budget_limits)
    metadata = build_run_metadata(
        experiment_id=experiment_id or f"exp-{benchmark_id}",
        benchmark_id=benchmark_id,
        benchmark_version=version,
        strategy_ids=tuple(r.strategy_id for r in runs),
        seeds=tuple(seeds),
        budgets=budgets,
        code_version="test",
    )
    return ExperimentResult(metadata=metadata, results=tuple(runs))


def simple_result(
    benchmark_id: str,
    values: dict[str, dict[str, dict[tuple[int, int], float]]],
    *,
    version: str = "1.0",
    unit: str = "items",
) -> ExperimentResult:
    """Build a result from a nested strategy/metric/(seed, budget)/value map."""
    runs: list[StrategyRunResult] = []
    seeds: set[int] = set()
    budgets: set[int] = set()
    for strategy_id, metrics in values.items():
        metric_values: list[MetricValue] = []
        for metric_name, cells in metrics.items():
            for (seed, budget_limit), value in cells.items():
                seeds.add(seed)
                budgets.add(budget_limit)
                metric_values.append(
                    metric(
                        metric_name, value, seed, budget_limit, unit=unit
                    )
                )
        runs.append(run(strategy_id, metric_values))
    return result(
        benchmark_id,
        runs,
        version=version,
        seeds=tuple(sorted(seeds)),
        budget_limits=tuple(sorted(budgets)),
        unit=BudgetUnit(unit),
    )
