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
from statistics import mean, pstdev

from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.metadata import build_run_metadata
from context_engineering_lab.core.results import (
    ExperimentResult,
    MetricValue,
    StrategyRunResult,
)

logger = logging.getLogger(__name__)


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
                        for name, value in benchmark.evaluate(case, context).items():
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
