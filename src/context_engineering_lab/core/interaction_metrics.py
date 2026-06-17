"""Interaction (composition) metric functions.

Phase 7 measures how composed pipelines compare to their primitive baselines.
Two kinds of metric live here:

* a per-case metric, :func:`pipeline_efficiency`, scored by a benchmark like any
  other metric, and
* report-level *comparative* functions (:func:`interaction_gain`,
  :func:`degradation_rate`, :func:`compensation_effect`) that take already
  aggregated mean values and contrast a pipeline with one or more baselines.

The comparative functions are pure scalar contrasts, not composite quality
scores: each compares one quality metric between runs, and the report always
shows the underlying means alongside. As elsewhere, undefined cases raise
``ValueError`` rather than returning a misleading number.
"""

from __future__ import annotations

from collections.abc import Sequence
from collections.abc import Set as AbstractSet

from context_engineering_lab.core.ids import ItemId


def pipeline_efficiency(
    relevant: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
    budget_limit: int,
) -> float:
    """Relevant items captured per unit of budget: ``|S ∩ R| / B``.

    A throughput-style view of a whole pipeline: how much of the budget turned
    into genuinely relevant context. With an item budget it lies in ``[0, 1]``
    (at most one relevant item per budget unit).

    Args:
        relevant: Ground-truth relevant item ids (``R``).
        selected: Item ids the pipeline placed in context (``S``).
        budget_limit: The final budget (``B``).

    Returns:
        Captured-relevant per budget unit.

    Raises:
        ValueError: If ``budget_limit <= 0``.
    """
    if budget_limit <= 0:
        raise ValueError("pipeline_efficiency is undefined for non-positive budget")
    return len(relevant & selected) / budget_limit


def interaction_gain(pipeline_value: float, baseline_value: float) -> float:
    """Signed change a pipeline produced on one metric: ``pipeline - baseline``.

    Positive means the composition scored higher than the named baseline on this
    metric; negative means lower. The two inputs are means already aggregated over
    seeds and budgets.

    Args:
        pipeline_value: The composition's mean for a metric.
        baseline_value: The baseline's mean for the same metric.

    Returns:
        The signed difference.
    """
    return pipeline_value - baseline_value


def degradation_rate(pipeline_value: float, baseline_value: float) -> float:
    """Relative quality lost when a pipeline scores below a baseline.

    ``max(0, baseline - pipeline) / baseline``: ``0`` when the pipeline matches or
    beats the baseline, approaching ``1`` as it collapses relative to it. Use only
    for metrics where higher is better.

    Args:
        pipeline_value: The composition's mean for a metric.
        baseline_value: The baseline's mean for the same metric.

    Returns:
        The relative degradation in ``[0, 1)``.

    Raises:
        ValueError: If ``baseline_value <= 0`` (the rate is undefined).
    """
    if baseline_value <= 0:
        raise ValueError("degradation_rate is undefined for a non-positive baseline")
    return max(0.0, baseline_value - pipeline_value) / baseline_value


def compensation_effect(
    pipeline_value: float, constituent_values: Sequence[float]
) -> float:
    """How much a pipeline beats the best of its own parts on one metric.

    ``pipeline - max(constituents)``: positive means the composition exceeds every
    one of its constituent primitives run alone (one primitive compensated for
    another's weakness); ``<= 0`` means it did not beat its best part.

    Args:
        pipeline_value: The composition's mean for a metric.
        constituent_values: Means for each constituent primitive, run alone.

    Returns:
        The signed margin over the best constituent.

    Raises:
        ValueError: If ``constituent_values`` is empty.
    """
    if not constituent_values:
        raise ValueError("compensation_effect needs at least one constituent")
    return pipeline_value - max(constituent_values)
