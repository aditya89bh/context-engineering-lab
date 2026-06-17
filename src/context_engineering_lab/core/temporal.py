"""Minimal temporal utilities.

Small, dependency-free helpers for reasoning about *time* over items: how old an
item is relative to a reference point, and a normalized version of that age. They
are deliberately tiny — Phase 4 studies temporal *effects*, it does not introduce
event stores, clocks, or retention machinery (see ``docs/non-goals.md``).

Conventions used throughout the temporal lab:

* A larger ``timestamp`` means *more recent*; the "now" of a sequence is its
  largest timestamp.
* *Age* is ``now - timestamp``: ``0`` for the newest item, larger for older
  items. Items without a timestamp are treated as maximally old.
"""

from __future__ import annotations

from collections.abc import Iterable

from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue

#: Metadata key carrying an *observable* salience signal in ``[0, 1]``. Unlike a
#: ground-truth relevance label, salience is a noisy proxy a deployable strategy
#: is allowed to read (see ``AgeWeightedSelection``). Defaults to ``1.0`` when
#: absent, so items without the key are treated as equally salient.
SALIENCE_KEY = "salience"

#: Metadata flag a benchmark sets to ``True`` on items that are *stale*: old and
#: no longer task-relevant. Used by the ``stale_selection_rate`` metric.
STALE_KEY = "stale"


def age(timestamp: float, now: float) -> float:
    """Return the age of ``timestamp`` relative to ``now``: ``now - timestamp``.

    Args:
        timestamp: The item's timestamp (larger means more recent).
        now: The reference time to measure age against.

    Returns:
        The (possibly negative) age. ``0`` when the item is the reference time.
    """
    return now - timestamp


def item_age(item: Item, now: float, *, missing: float = float("inf")) -> float:
    """Return an item's age relative to ``now``.

    Args:
        item: The item to measure.
        now: The reference time to measure age against.
        missing: Age assigned to items without a timestamp. Defaults to positive
            infinity so timeless items rank as the oldest possible.

    Returns:
        The item's age, or ``missing`` when it has no timestamp.
    """
    if item.timestamp is None:
        return missing
    return age(item.timestamp, now)


def relative_age(timestamp: float, now: float, span: float) -> float:
    """Return age normalized to ``[0, 1]`` over a span, clamped to the range.

    Args:
        timestamp: The item's timestamp.
        now: The reference time to measure age against.
        span: The positive timeline span used to normalize.

    Returns:
        ``(now - timestamp) / span`` clamped to ``[0, 1]``.

    Raises:
        ValueError: If ``span`` is not positive.
    """
    if span <= 0:
        raise ValueError("relative_age requires a positive span")
    return min(1.0, max(0.0, age(timestamp, now) / span))


def salience_of(item: Item, default: float = 1.0) -> float:
    """Return an item's observable salience, or ``default`` when unset.

    Args:
        item: The item to read salience from.
        default: Value returned when the item carries no salience.

    Returns:
        The salience as a float.
    """
    value: JsonValue = item.metadata.get(SALIENCE_KEY, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return float(value)


def latest_timestamp(items: Iterable[Item], *, default: float = 0.0) -> float:
    """Return the largest timestamp among ``items`` (their shared "now").

    Args:
        items: The items to scan.
        default: Value returned when no item has a timestamp.

    Returns:
        The maximum timestamp, or ``default`` when none is present.
    """
    stamps = [item.timestamp for item in items if item.timestamp is not None]
    return max(stamps) if stamps else default
