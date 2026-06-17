"""Phase 8 experiment configurations: naturalistic context scenarios.

Five reproducible experiments, one per benchmark family, each running a small
*curated* lineup of existing strategies and Phase 7 compositions — not the whole
catalog. The lineup contrasts content-blind recency, content-aware keyword
selection, an importance-aware retention policy, two compositions, and an oracle
ceiling. The source-based support family additionally includes an attention
composition. They are deterministic and produce scenario-specific observations
only; they make no claim about real workplace context or real-world systems.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.naturalistic.presets import (
    email_old_signal,
    meeting_action_items,
    memory_log_noisy,
    revision_current_truth,
    support_stale_fix,
)
from context_engineering_lab.compositions import (
    attention_then_selection,
    retention_then_selection,
    temporal_then_selection,
)
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.retention import PolicyStrategy
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.retention.salience import SalienceRetentionPolicy
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection
from context_engineering_lab.strategies.oracle import OracleSelection
from context_engineering_lab.strategies.recency import RecencySelection

#: Seeds every Phase 8 experiment runs over.
PHASE8_SEEDS: tuple[int, ...] = (1, 2, 3)


def curated_strategies() -> tuple[Strategy, ...]:
    """Return the curated item-budget lineup shared by most families.

    Content-blind `recency`, content-aware `keyword-overlap`, an importance-aware
    `salience-retention`, the `temporal->selection` and `retention->selection`
    compositions, and the `oracle` ceiling (not deployable).
    """
    return (
        RecencySelection(),
        KeywordOverlapSelection(),
        PolicyStrategy(SalienceRetentionPolicy()),
        temporal_then_selection(),
        retention_then_selection(),
        OracleSelection(),
    )


def source_curated_strategies() -> tuple[Strategy, ...]:
    """The curated lineup plus `attention->selection` for source-based families."""
    return (*curated_strategies(), attention_then_selection())


def naturalistic_email() -> Experiment:
    """Curated lineup on an old relevant email under recent chatter."""
    return Experiment(
        experiment_id=ExperimentId("naturalistic-email"),
        benchmark=email_old_signal(),
        strategies=curated_strategies(),
        seeds=PHASE8_SEEDS,
    )


def naturalistic_meeting() -> Experiment:
    """Curated lineup on a current decision buried in meeting notes."""
    return Experiment(
        experiment_id=ExperimentId("naturalistic-meeting"),
        benchmark=meeting_action_items(),
        strategies=curated_strategies(),
        seeds=PHASE8_SEEDS,
    )


def naturalistic_support() -> Experiment:
    """Curated lineup (plus attention) on past support incidents."""
    return Experiment(
        experiment_id=ExperimentId("naturalistic-support"),
        benchmark=support_stale_fix(),
        strategies=source_curated_strategies(),
        seeds=PHASE8_SEEDS,
    )


def naturalistic_revision() -> Experiment:
    """Curated lineup on current vs superseded document facts."""
    return Experiment(
        experiment_id=ExperimentId("naturalistic-revision"),
        benchmark=revision_current_truth(),
        strategies=curated_strategies(),
        seeds=PHASE8_SEEDS,
    )


def naturalistic_memory_log() -> Experiment:
    """Curated lineup on a noisy agent memory log."""
    return Experiment(
        experiment_id=ExperimentId("naturalistic-memory-log"),
        benchmark=memory_log_noisy(),
        strategies=curated_strategies(),
        seeds=PHASE8_SEEDS,
    )


def phase8_experiments() -> dict[str, Experiment]:
    """Return all Phase 8 experiments keyed by their experiment id."""
    experiments = (
        naturalistic_email(),
        naturalistic_meeting(),
        naturalistic_support(),
        naturalistic_revision(),
        naturalistic_memory_log(),
    )
    return {str(exp.experiment_id): exp for exp in experiments}
