"""Built-in strategy compositions.

Phase 7 chains the existing Phase 2-6 primitives into linear pipelines using
:class:`~context_engineering_lab.core.composition.StrategyComposition`. Nothing
here is a new algorithm: every stage is an existing strategy (a selector, a
temporal selector, a retention policy, or an attention allocator) wrapped through
the adapters built in earlier phases. The factories below give each pipeline a
stable id so it can be compared against its primitive constituents in a report.

The retention stage uses :class:`FrequencyRetentionPolicy` on purpose: in the
``interaction-context-pipeline`` benchmark, access frequency is the one observable
signal that separates corroborated-relevant items from the harmful traps that
otherwise mimic them, so a frequency-aware forgetting stage is what a downstream
selector or allocator cannot do for itself.
"""

from __future__ import annotations

from context_engineering_lab.attention.adaptive import AdaptiveAllocation
from context_engineering_lab.compression.keyword_preserving import (
    KeywordPreservingCompression,
)
from context_engineering_lab.core.attention import AllocatorStrategy
from context_engineering_lab.core.composition import StrategyComposition
from context_engineering_lab.core.compression import CompressorStrategy
from context_engineering_lab.core.retention import PolicyStrategy
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.retention.frequency import FrequencyRetentionPolicy
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection
from context_engineering_lab.strategies.oracle import OracleSelection
from context_engineering_lab.strategies.temporal import SlidingWindowSelection


def _selection() -> Strategy:
    return KeywordOverlapSelection()


def _temporal() -> Strategy:
    return SlidingWindowSelection()


def _retention() -> Strategy:
    return PolicyStrategy(FrequencyRetentionPolicy())


def _attention() -> Strategy:
    return AllocatorStrategy(AdaptiveAllocation())


def _compression() -> Strategy:
    return CompressorStrategy(KeywordPreservingCompression())


def temporal_then_selection() -> StrategyComposition:
    """Temporal recency window, then keyword selection."""
    return StrategyComposition(
        (_temporal(), _selection()), composition_id="temporal->selection"
    )


def attention_then_selection() -> StrategyComposition:
    """Attention allocation across sources, then keyword selection."""
    return StrategyComposition(
        (_attention(), _selection()), composition_id="attention->selection"
    )


def retention_then_attention() -> StrategyComposition:
    """Frequency-based forgetting, then attention allocation."""
    return StrategyComposition(
        (_retention(), _attention()), composition_id="retention->attention"
    )


def temporal_then_retention() -> StrategyComposition:
    """Temporal recency window, then frequency-based forgetting."""
    return StrategyComposition(
        (_temporal(), _retention()), composition_id="temporal->retention"
    )


def retention_then_selection() -> StrategyComposition:
    """Frequency-based forgetting, then keyword selection."""
    return StrategyComposition(
        (_retention(), _selection()), composition_id="retention->selection"
    )


def selection_then_compression() -> StrategyComposition:
    """Keyword selection, then keyword-preserving compression.

    A token-budget pipeline: the compression stage shortens content, so this is
    meaningful under a token budget rather than the item budgets the shipped
    interaction experiments sweep. Provided (and tested) to show the abstraction
    composes a compressor like any other stage.
    """
    return StrategyComposition(
        (_selection(), _compression()), composition_id="selection->compression"
    )


def retention_then_compression() -> StrategyComposition:
    """Frequency-based forgetting, then keyword-preserving compression.

    A token-budget pipeline; see :func:`selection_then_compression` for the
    budget-unit caveat.
    """
    return StrategyComposition(
        (_retention(), _compression()), composition_id="retention->compression"
    )


def oracle_pipeline() -> StrategyComposition:
    """A single-stage oracle ceiling.

    Wraps :class:`OracleSelection`, which reads ground-truth relevance, as a
    one-step composition. It is **not deployable**; it marks the best a pipeline
    could do on this benchmark.
    """
    return StrategyComposition((OracleSelection(),), composition_id="oracle-pipeline")


def item_budget_compositions() -> tuple[StrategyComposition, ...]:
    """Return the compositions that run under an item budget, in a stable order."""
    return (
        temporal_then_selection(),
        attention_then_selection(),
        retention_then_attention(),
        temporal_then_retention(),
        retention_then_selection(),
    )


def token_budget_compositions() -> tuple[StrategyComposition, ...]:
    """Return the compositions whose final stage is compression (token budget)."""
    return (
        selection_then_compression(),
        retention_then_compression(),
    )


def default_compositions() -> tuple[StrategyComposition, ...]:
    """Return every built-in composition, including the oracle ceiling."""
    return (
        *item_budget_compositions(),
        *token_budget_compositions(),
        oracle_pipeline(),
    )
