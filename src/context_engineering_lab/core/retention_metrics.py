"""Retention (forgetting) metric functions.

Pure implementations of the forgetting metrics defined formally in
``docs/metrics.md``. They operate on sets of item ids partitioned by ground-truth
*kind* — useful, harmful, required — and on what a policy chose to keep. They make
no research claims on their own.

Like the other metric modules, each function raises ``ValueError`` for the cases
its definition leaves undefined (e.g. precision with nothing retained), so callers
decide how to record those rather than receiving a misleading value.
"""

from __future__ import annotations

from collections.abc import Set as AbstractSet

from context_engineering_lab.core.ids import ItemId


def retention_precision(
    useful: AbstractSet[ItemId],
    retained: AbstractSet[ItemId],
) -> float:
    """Fraction of retained items that are useful: ``|R ∩ U| / |R|``.

    Args:
        useful: Ground-truth useful item ids (``U``).
        retained: Item ids the policy kept (``R``).

    Returns:
        Precision in ``[0, 1]``; higher means a cleaner memory.

    Raises:
        ValueError: If ``retained`` is empty (precision is undefined).
    """
    if not retained:
        raise ValueError("retention_precision is undefined for an empty retention")
    return len(useful & retained) / len(retained)


def retention_recall(
    required: AbstractSet[ItemId],
    retained: AbstractSet[ItemId],
) -> float:
    """Fraction of required useful items kept: ``|R ∩ U_req| / |U_req|``.

    Args:
        required: The minimal useful item ids that must be kept (``U_req``).
        retained: Item ids the policy kept (``R``).

    Returns:
        Recall in ``[0, 1]``.

    Raises:
        ValueError: If ``required`` is empty (recall is undefined).
    """
    if not required:
        raise ValueError("retention_recall is undefined with no required items")
    return len(required & retained) / len(required)


def useful_retention_rate(
    useful: AbstractSet[ItemId],
    retained: AbstractSet[ItemId],
) -> float:
    """Fraction of *all* useful items kept: ``|R ∩ U| / |U|``.

    The graded companion to :func:`retention_recall` (which is over the required
    subset): how much of the broad useful population survived.

    Args:
        useful: Ground-truth useful item ids (``U``).
        retained: Item ids the policy kept (``R``).

    Returns:
        The useful survival rate in ``[0, 1]``.

    Raises:
        ValueError: If ``useful`` is empty (the rate is undefined).
    """
    if not useful:
        raise ValueError("useful_retention_rate is undefined with no useful items")
    return len(useful & retained) / len(useful)


def harmful_retention_rate(
    harmful: AbstractSet[ItemId],
    retained: AbstractSet[ItemId],
) -> float:
    """Fraction of harmful items kept: ``|R ∩ H| / |H|``.

    Lower is better: a good policy forgets harmful information.

    Args:
        harmful: Ground-truth harmful item ids (``H``).
        retained: Item ids the policy kept (``R``).

    Returns:
        The harmful survival rate in ``[0, 1]``.

    Raises:
        ValueError: If ``harmful`` is empty (the rate is undefined).
    """
    if not harmful:
        raise ValueError("harmful_retention_rate is undefined with no harmful items")
    return len(harmful & retained) / len(harmful)


def memory_budget_utilization(retained_count: int, budget_limit: int) -> float:
    """Fraction of the memory budget consumed: ``|R| / limit``.

    May exceed ``1.0`` for a policy that does not honor the budget (e.g. a
    retain-all baseline).

    Args:
        retained_count: Number of items the policy kept.
        budget_limit: The memory budget limit.

    Returns:
        The utilization ratio.

    Raises:
        ValueError: If ``budget_limit <= 0`` or ``retained_count < 0``.
    """
    if budget_limit <= 0:
        raise ValueError("memory_budget_utilization needs a positive budget")
    if retained_count < 0:
        raise ValueError("retained_count cannot be negative")
    return retained_count / budget_limit


def forgetting_efficiency(
    useful: AbstractSet[ItemId],
    harmful: AbstractSet[ItemId],
    retained: AbstractSet[ItemId],
) -> float:
    """Useful survival minus harmful survival.

    A transparent contrast — *not* a composite quality score — equal to
    ``useful_retention_rate - harmful_retention_rate``. It is positive when a
    policy keeps more of the useful than of the harmful, ``0`` when it cannot
    tell them apart, and negative when it preferentially keeps harm. The two
    component rates are always reported alongside it (see ``docs/metrics.md``); it
    only summarizes the gap between them.

    Args:
        useful: Ground-truth useful item ids (``U``).
        harmful: Ground-truth harmful item ids (``H``). May be empty, in which
            case the harmful term is ``0``.
        retained: Item ids the policy kept (``R``).

    Returns:
        A value in ``[-1, 1]``; higher is better.

    Raises:
        ValueError: If ``useful`` is empty (the metric is undefined).
    """
    if not useful:
        raise ValueError("forgetting_efficiency is undefined with no useful items")
    useful_rate = len(useful & retained) / len(useful)
    harmful_rate = (len(harmful & retained) / len(harmful)) if harmful else 0.0
    return useful_rate - harmful_rate
