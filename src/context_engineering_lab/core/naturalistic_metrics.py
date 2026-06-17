"""Naturalistic-scenario metric functions.

Phase 8 scores deployable strategies on synthetic-but-realistic context shapes
(email threads, meeting notes, support tickets, document revisions, memory logs).
It reuses the selection, retention, and temporal metrics defined elsewhere and
adds three contrasts that the naturalistic scenarios make meaningful:

* :func:`current_truth_support` — did the selection recover the *current* facts,
* :func:`superseded_fact_retention` — did it drag along *superseded* ones,
* :func:`conflict_selection_rate` — how much of the output *conflicts* with the
  current truth.

Each operates on sets of item ids and raises ``ValueError`` for the cases its
definition leaves undefined, so callers decide how to record them rather than
silently receiving a misleading zero. Formulas are documented in
``docs/metrics.md``.
"""

from __future__ import annotations

from collections.abc import Set as AbstractSet

from context_engineering_lab.core.ids import ItemId


def current_truth_support(
    current: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
) -> float:
    """Fraction of current-truth items selected: ``|S ∩ C| / |C|``.

    A recall over the items that carry the *current* answer (as opposed to
    superseded or stale versions). Higher is better.

    Args:
        current: Ground-truth ids of current-truth items (``C``).
        selected: Item ids the strategy selected (``S``).

    Returns:
        Current-truth recall in ``[0, 1]``.

    Raises:
        ValueError: If ``current`` is empty (the metric is undefined).
    """
    if not current:
        raise ValueError("current_truth_support is undefined with no current items")
    return len(current & selected) / len(current)


def superseded_fact_retention(
    superseded: AbstractSet[ItemId],
    selected: AbstractSet[ItemId],
) -> float:
    """Fraction of superseded items kept: ``|S ∩ D| / |D|``.

    Superseded items are old versions a later revision or decision replaced.
    Lower is better: a good strategy drops what has been superseded.

    Args:
        superseded: Ground-truth ids of superseded items (``D``).
        selected: Item ids the strategy selected (``S``).

    Returns:
        The superseded survival rate in ``[0, 1]``.

    Raises:
        ValueError: If ``superseded`` is empty (the rate is undefined).
    """
    if not superseded:
        raise ValueError(
            "superseded_fact_retention is undefined with no superseded items"
        )
    return len(superseded & selected) / len(superseded)


def conflict_selection_rate(
    selected: AbstractSet[ItemId],
    conflicting: AbstractSet[ItemId],
) -> float:
    """Fraction of the selection that conflicts with the truth: ``|S ∩ K| / |S|``.

    Conflicting items contradict the current answer (e.g. an outdated figure that
    competes with the right one). Lower is better.

    Args:
        selected: Item ids the strategy selected (``S``).
        conflicting: Ground-truth ids of conflicting items (``K``).

    Returns:
        The conflict rate in ``[0, 1]``.

    Raises:
        ValueError: If ``selected`` is empty (the rate is undefined).
    """
    if not selected:
        raise ValueError("conflict_selection_rate is undefined for an empty selection")
    return len(selected & conflicting) / len(selected)
