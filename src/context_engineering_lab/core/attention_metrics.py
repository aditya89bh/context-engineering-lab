"""Attention-allocation metric functions.

Pure implementations of the allocation metrics defined formally in
``docs/metrics.md``. They describe how well a budget split across sources
converted into captured signal, and make no research claims on their own.

Like the other metric modules, each function raises ``ValueError`` for the cases
its definition leaves undefined (e.g. efficiency with nothing selected), so
callers decide how to record those rather than receiving a misleading value.
"""

from __future__ import annotations

from collections.abc import Set as AbstractSet

from context_engineering_lab.core.ids import ItemId


def allocation_efficiency(
    signal: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
) -> float:
    """Fraction of selected items that are signal: ``|S ∩ G| / |S|``.

    The precision of where attention landed: of everything the allocation placed,
    how much was genuine signal rather than distractor.

    Args:
        signal: Ground-truth signal item ids (``G``).
        selected: Item ids actually placed in context (``S``).

    Returns:
        Efficiency in ``[0, 1]``.

    Raises:
        ValueError: If ``selected`` is empty (efficiency is undefined).
    """
    if not selected:
        raise ValueError("allocation_efficiency is undefined for an empty selection")
    return len(signal & selected) / len(selected)


def signal_capture_rate(
    signal: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
) -> float:
    """Fraction of all available signal captured: ``|S ∩ G| / |G|``.

    The recall of the allocation across every source: how much of the total
    signal made it into context.

    Args:
        signal: Ground-truth signal item ids across all sources (``G``).
        selected: Item ids actually placed in context (``S``).

    Returns:
        Capture rate in ``[0, 1]``.

    Raises:
        ValueError: If ``signal`` is empty (the rate is undefined).
    """
    if not signal:
        raise ValueError("signal_capture_rate is undefined with no signal")
    return len(signal & selected) / len(signal)


def wasted_attention_rate(
    signal: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
    budget_limit: int,
) -> float:
    """Fraction of the budget that did not become signal: ``(B - |S ∩ G|) / B``.

    Lower is better. Budget is wasted two ways: on selected distractors, and on
    capacity an allocator gave to a source that could not fill it. Both are
    captured here because ``|S ∩ G| <= |S| <= B``.

    Args:
        signal: Ground-truth signal item ids (``G``).
        selected: Item ids actually placed in context (``S``).
        budget_limit: The total budget (``B``).

    Returns:
        The wasted-attention rate in ``[0, 1]``.

    Raises:
        ValueError: If ``budget_limit <= 0``.
    """
    if budget_limit <= 0:
        raise ValueError("wasted_attention_rate is undefined for non-positive budget")
    captured = len(signal & selected)
    return (budget_limit - captured) / budget_limit


def source_coverage(
    covered_sources: AbstractSet[str],
    all_sources: AbstractSet[str],
) -> float:
    """Fraction of sources that contributed at least one selected item.

    Describes how widely the allocation spread its budget. High coverage is not
    inherently good — concentrating on the right source can beat spreading — so
    this is reported as a descriptor, not a quality score.

    Args:
        covered_sources: Ids of sources that contributed a selected item.
        all_sources: Ids of all sources available in the case.

    Returns:
        Coverage in ``[0, 1]``.

    Raises:
        ValueError: If ``all_sources`` is empty (coverage is undefined).
    """
    if not all_sources:
        raise ValueError("source_coverage is undefined with no sources")
    return len(covered_sources & all_sources) / len(all_sources)
