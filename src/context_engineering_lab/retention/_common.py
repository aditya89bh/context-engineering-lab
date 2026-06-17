"""Shared helpers for deterministic retention policies.

Most policies differ only in *how they score* an item's worth; once a score is
fixed, they all keep the highest-scoring items the budget allows and forget the
rest. This module captures that common step so each policy implements only its
scoring function. Ties are broken by item id so every policy is reproducible.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from context_engineering_lab.core.budget import Budget, item_cost
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import (
    RetentionDecision,
    RetentionResult,
    RetentionStats,
)

ScoreFn = Callable[[Item], float]


def retain_by_score(
    policy_id: str,
    items: Sequence[Item],
    budget: Budget,
    score_fn: ScoreFn,
    *,
    keep_all: bool = False,
) -> RetentionResult:
    """Keep the highest-scoring items within the budget, forget the rest.

    Args:
        policy_id: Id of the policy producing the result.
        items: The items currently in memory.
        budget: The memory budget the kept set should satisfy.
        score_fn: Maps an item to its worth; higher is kept first.
        keep_all: If ``True``, keep every item regardless of the budget (the
            retain-all reference); the returned context permits overflow.

    Returns:
        A :class:`RetentionResult` with the kept context, per-item decisions
        (in the original order), and count statistics.
    """
    scores = {item.id: score_fn(item) for item in items}
    ordered = sorted(items, key=lambda item: (-scores[item.id], str(item.id)))

    kept: list[Item] = []
    retained_ids: set[str] = set()
    used = 0
    for item in ordered:
        cost = item_cost(item, budget.unit)
        if keep_all or budget.admits(used, cost):
            kept.append(item)
            used += cost
            retained_ids.add(str(item.id))

    decisions = tuple(
        RetentionDecision(
            item_id=item.id,
            retained=str(item.id) in retained_ids,
            score=scores[item.id],
        )
        for item in items
    )
    context = Context(items=tuple(kept), budget=budget, allow_overflow=keep_all)
    stats = RetentionStats(
        policy_id=policy_id,
        considered=len(items),
        retained=len(kept),
        forgotten=len(items) - len(kept),
        budget_limit=budget.limit,
    )
    return RetentionResult(context=context, decisions=decisions, stats=stats)


def normalize(values: Sequence[float]) -> list[float]:
    """Min-max normalize values to ``[0, 1]`` (all zeros if the range is empty).

    Args:
        values: The raw values to normalize.

    Returns:
        The normalized values; an all-equal input maps to all zeros.
    """
    if not values:
        return []
    low = min(values)
    high = max(values)
    span = high - low
    if span <= 0:
        return [0.0 for _ in values]
    return [(v - low) / span for v in values]
