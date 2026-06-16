"""The experiment runner.

A small, synchronous runner that executes an
:class:`~context_engineering_lab.core.experiment.Experiment` over its strategies,
seeds, and budgets, aggregates per-case metric values, and returns a structured
:class:`~context_engineering_lab.core.results.ExperimentResult`.

It intentionally does *not* implement parallelism, plugins, dashboards, or
distributed execution; those are out of scope for the core harness.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from statistics import mean, pstdev

from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.metadata import build_run_metadata
from context_engineering_lab.core.results import (
    ExperimentResult,
    MetricValue,
    StrategyRunResult,
)

logger = logging.getLogger(__name__)


def _validate_evaluation(
    benchmark_id: str,
    case_id: str,
    declared: AbstractSet[str],
    returned: Mapping[str, float],
) -> None:
    """Ensure an evaluation returned exactly the declared metric names.

    Args:
        benchmark_id: The benchmark whose evaluation is being checked.
        case_id: The case the evaluation came from.
        declared: The benchmark's declared metric names.
        returned: The metric mapping returned by ``evaluate``.

    Raises:
        ValueError: If the returned names are missing any declared metric or
            include any undeclared (extra) metric.
    """
    returned_names = frozenset(returned)
    if returned_names == declared:
        return
    missing = sorted(declared - returned_names)
    extra = sorted(returned_names - declared)
    raise ValueError(
        "benchmark "
        f"{benchmark_id!r} returned metrics that do not match its declared "
        f"metrics for case {case_id!r}: missing={missing}, extra={extra}"
    )


class ExperimentRunner:
    """Runs experiments synchronously and collects their metrics."""

    def run(self, experiment: Experiment) -> ExperimentResult:
        """Execute an experiment and return its structured results.

        Args:
            experiment: The configuration to run.

        Returns:
            The aggregated results across every strategy, seed, and budget.
        """
        # Imported lazily to avoid a package-init import cycle (the package
        # ``__init__`` re-exports the runner).
        from context_engineering_lab import __version__

        benchmark = experiment.benchmark
        budgets = experiment.resolved_budgets()
        strategy_ids = tuple(str(s.id) for s in experiment.strategies)
        declared_metrics = frozenset(benchmark.declared_metrics)

        logger.info(
            "experiment_start experiment=%s benchmark=%s version=%s "
            "strategies=%d seeds=%d budgets=%d",
            str(experiment.experiment_id),
            str(benchmark.id),
            benchmark.version,
            len(experiment.strategies),
            len(experiment.seeds),
            len(budgets),
        )

        strategy_results: list[StrategyRunResult] = []
        for strategy in experiment.strategies:
            metric_values: list[MetricValue] = []
            for seed in experiment.seeds:
                cases = benchmark.generate(seed)
                for budget in budgets:
                    per_metric: dict[str, list[float]] = defaultdict(list)
                    for case in cases:
                        context = strategy.select(case.candidates, case.task, budget)
                        scores = benchmark.evaluate(case, context)
                        _validate_evaluation(
                            str(benchmark.id),
                            case.case_id,
                            declared_metrics,
                            scores,
                        )
                        for name, value in scores.items():
                            per_metric[name].append(value)
                    for name, values in per_metric.items():
                        metric_values.append(
                            MetricValue(
                                name=name,
                                value=mean(values),
                                seed=seed,
                                budget_limit=budget.limit,
                                budget_unit=budget.unit.value,
                                sample_size=len(values),
                                stddev=pstdev(values) if len(values) > 1 else 0.0,
                            )
                        )
            strategy_results.append(
                StrategyRunResult(
                    strategy_id=str(strategy.id),
                    metrics=tuple(metric_values),
                )
            )
            logger.info(
                "strategy_done experiment=%s strategy=%s measurements=%d",
                str(experiment.experiment_id),
                str(strategy.id),
                len(metric_values),
            )

        metadata = build_run_metadata(
            experiment_id=str(experiment.experiment_id),
            benchmark_id=str(benchmark.id),
            benchmark_version=benchmark.version,
            strategy_ids=strategy_ids,
            seeds=experiment.seeds,
            budgets=budgets,
            code_version=__version__,
        )
        logger.info(
            "experiment_done experiment=%s run_id=%s",
            str(experiment.experiment_id),
            metadata.run_id.value,
        )
        return ExperimentResult(metadata=metadata, results=tuple(strategy_results))
