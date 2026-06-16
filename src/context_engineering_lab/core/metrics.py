"""Selection metric functions.

Pure implementations of the selection metrics defined formally in
``docs/metrics.md``. They operate on sets of item ids (ground truth vs. what a
strategy selected) and make no research claims on their own; they are the
building blocks benchmarks use to score outputs.

Each function raises ``ValueError`` for the cases its formal definition leaves
undefined (e.g. precision with an empty selection), so callers must decide how
to handle those rather than silently receiving a misleading zero.
"""

from __future__ import annotations

from collections.abc import Set as AbstractSet

from context_engineering_lab.core.ids import ItemId


def selection_precision(
    relevant: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
) -> float:
    """Fraction of selected items that are relevant: ``|S ∩ R| / |S|``.

    Args:
        relevant: Ground-truth relevant item ids (``R``).
        selected: Item ids the strategy selected (``S``).

    Returns:
        Precision in ``[0, 1]``.

    Raises:
        ValueError: If ``selected`` is empty (precision is undefined).
    """
    if not selected:
        raise ValueError("selection_precision is undefined for an empty selection")
    return len(relevant & selected) / len(selected)


def selection_recall(
    relevant: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
) -> float:
    """Fraction of relevant items that were selected: ``|S ∩ R| / |R|``.

    Args:
        relevant: Ground-truth relevant item ids (``R``).
        selected: Item ids the strategy selected (``S``).

    Returns:
        Recall in ``[0, 1]``.

    Raises:
        ValueError: If ``relevant`` is empty (recall is undefined).
    """
    if not relevant:
        raise ValueError("selection_recall is undefined with no relevant items")
    return len(relevant & selected) / len(relevant)


def answer_support(
    required: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
) -> float:
    """Whether every required item is present: ``1`` if ``R_req ⊆ S`` else ``0``.

    Args:
        required: The minimal set of item ids needed to succeed (``R_req``).
        selected: Item ids the strategy selected (``S``).

    Returns:
        ``1.0`` if all required items were selected, else ``0.0``.

    Raises:
        ValueError: If ``required`` is empty (support is undefined).
    """
    if not required:
        raise ValueError("answer_support is undefined with no required items")
    return 1.0 if required <= selected else 0.0
