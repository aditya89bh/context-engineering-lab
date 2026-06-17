"""Temporal metric functions.

Pure implementations of the temporal metrics defined formally in
``docs/metrics.md``. They describe *where in time* a selection sits relative to
the items that actually carry the signal — distinct from the set-overlap
selection metrics (precision/recall), which ignore time entirely.

Like the selection metrics, each function raises ``ValueError`` for the cases its
definition leaves undefined (e.g. the mean age of an empty selection), so callers
decide how to record those rather than silently receiving a misleading zero.
"""

from __future__ import annotations

from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from statistics import fmean

from context_engineering_lab.core.ids import ItemId


def stale_selection_rate(
    selected: AbstractSet[ItemId],
    stale: AbstractSet[ItemId],
) -> float:
    """Fraction of selected items that are stale: ``|S ∩ stale| / |S|``.

    Args:
        selected: Item ids the strategy selected (``S``).
        stale: Ground-truth ids of stale (old, no-longer-relevant) items.

    Returns:
        The stale rate in ``[0, 1]``; lower is better.

    Raises:
        ValueError: If ``selected`` is empty (the rate is undefined).
    """
    if not selected:
        raise ValueError("stale_selection_rate is undefined for an empty selection")
    return len(selected & stale) / len(selected)


def age_of_selected_context(selected_ages: Sequence[float], span: float) -> float:
    """Mean normalized age of the selected items: ``mean(age) / span``.

    Args:
        selected_ages: Ages of the selected items (``now - timestamp``).
        span: The positive timeline span used to normalize.

    Returns:
        Mean age normalized to roughly ``[0, 1]`` (older selections score higher).

    Raises:
        ValueError: If ``selected_ages`` is empty or ``span`` is not positive.
    """
    if not selected_ages:
        raise ValueError("age_of_selected_context is undefined for an empty selection")
    if span <= 0:
        raise ValueError("age_of_selected_context requires a positive span")
    return fmean(selected_ages) / span


def relevant_age_gap(
    selected_ages: Sequence[float],
    relevant_ages: Sequence[float],
    span: float,
) -> float:
    """Normalized distance in time between the selection and the relevant set.

    Computes ``|mean(selected_ages) - mean(relevant_ages)| / span``: how far, in
    normalized time, the average selected item sits from the average relevant
    item. ``0`` means the selection is temporally aligned with where the signal
    actually is; larger means the selector is looking in the wrong era.

    Args:
        selected_ages: Ages of the selected items.
        relevant_ages: Ages of the ground-truth relevant items.
        span: The positive timeline span used to normalize.

    Returns:
        The normalized absolute age gap (``>= 0``); lower is better.

    Raises:
        ValueError: If either sequence is empty or ``span`` is not positive.
    """
    if not selected_ages:
        raise ValueError("relevant_age_gap is undefined for an empty selection")
    if not relevant_ages:
        raise ValueError("relevant_age_gap is undefined with no relevant items")
    if span <= 0:
        raise ValueError("relevant_age_gap requires a positive span")
    return abs(fmean(selected_ages) - fmean(relevant_ages)) / span


def temporal_relevance(
    selected_ages: Sequence[float],
    relevant_lo: float,
    relevant_hi: float,
) -> float:
    """Fraction of selected items whose age falls in the relevant age band.

    The "relevant age band" is the closed interval spanned by the ages of the
    ground-truth relevant items, ``[relevant_lo, relevant_hi]``. This measures
    whether the selection lands in the right temporal region, independent of
    whether each selected item is itself the signal (which precision captures).

    Args:
        selected_ages: Ages of the selected items.
        relevant_lo: Minimum age among the relevant items.
        relevant_hi: Maximum age among the relevant items.

    Returns:
        The in-band fraction in ``[0, 1]``; higher is better.

    Raises:
        ValueError: If ``selected_ages`` is empty or the band is inverted.
    """
    if not selected_ages:
        raise ValueError("temporal_relevance is undefined for an empty selection")
    if relevant_lo > relevant_hi:
        raise ValueError("temporal_relevance requires relevant_lo <= relevant_hi")
    in_band = sum(1 for a in selected_ages if relevant_lo <= a <= relevant_hi)
    return in_band / len(selected_ages)
