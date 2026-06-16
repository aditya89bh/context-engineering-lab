"""Phase 3 experiment configurations: compression under budget pressure.

Four reproducible experiments, each pairing a compression preset with the same
compressor line-up so results are directly comparable. They are small and
deterministic. They produce controlled observations on these synthetic
benchmarks only; they do not support broad claims about compression or
summarization in general, and they include no LLM summarization.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.compression_presets import (
    dense_distractor_compression,
    easy_compression,
    late_signal_compression,
)
from context_engineering_lab.compression import default_compressors
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.compression import CompressorStrategy
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.strategy import Strategy

#: Seeds every Phase 3 experiment runs over.
PHASE3_SEEDS: tuple[int, ...] = (1, 2, 3)


def default_strategies() -> tuple[Strategy, ...]:
    """Return the standard Phase 3 compressor line-up, wrapped as strategies.

    Spans a no-compression reference, position-based truncation, query-aware
    keyword preservation, sentence-boundary extraction, and the oracle ceiling
    (which is **not deployable**).
    """
    return tuple(CompressorStrategy(c) for c in default_compressors())


def compression_baselines_easy() -> Experiment:
    """Compressors on the low-interference preset."""
    return Experiment(
        experiment_id=ExperimentId("compression-baselines-easy"),
        benchmark=easy_compression(),
        strategies=default_strategies(),
        seeds=PHASE3_SEEDS,
    )


def compression_late_signal() -> Experiment:
    """Probe truncation position bias with late target facts."""
    return Experiment(
        experiment_id=ExperimentId("compression-late-signal"),
        benchmark=late_signal_compression(),
        strategies=default_strategies(),
        seeds=PHASE3_SEEDS,
    )


def compression_distractor_density() -> Experiment:
    """Stress distractor discarding under heavy distractor density."""
    return Experiment(
        experiment_id=ExperimentId("compression-distractor-density"),
        benchmark=dense_distractor_compression(),
        strategies=default_strategies(),
        seeds=PHASE3_SEEDS,
    )


def compression_budget_sweep() -> Experiment:
    """Trace the compression-quality frontier with a finer budget ladder."""
    budgets = tuple(
        Budget(limit, BudgetUnit.TOKENS)
        for limit in (2, 4, 6, 8, 12, 16, 24, 32)
    )
    return Experiment(
        experiment_id=ExperimentId("compression-budget-sweep"),
        benchmark=dense_distractor_compression(),
        strategies=default_strategies(),
        seeds=PHASE3_SEEDS,
        budgets=budgets,
    )


def phase3_experiments() -> dict[str, Experiment]:
    """Return all Phase 3 experiments keyed by their experiment id."""
    experiments = (
        compression_baselines_easy(),
        compression_late_signal(),
        compression_distractor_density(),
        compression_budget_sweep(),
    )
    return {str(exp.experiment_id): exp for exp in experiments}
