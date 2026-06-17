"""Shared helpers for deterministic attention allocators.

Allocators differ only in *how they weight* sources. Once a weight vector is
fixed, they all turn it into an integer per-source budget and fill each share
with the same inner selection (highest observable salience first). This module
captures that common machinery so each allocator implements only its weighting.

Two apportionment modes are offered:

* :func:`largest_remainder` — a plain Hamilton apportionment that ignores source
  capacity, so a source can be handed more budget than it can fill (the budget is
  then wasted). Fixed allocators use this; wasting is a real failure mode.
* :func:`capacity_aware_apportion` — never assigns a source more than it holds,
  redistributing the slack to other weighted sources. Adaptive and oracle
  allocators use this.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.attention import (
    AllocationDecision,
    AllocationResult,
    AllocationStats,
    Source,
)
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.temporal import salience_of


def largest_remainder(weights: Sequence[float], total: int) -> list[int]:
    """Apportion ``total`` integer units across weights (Hamilton method).

    Ties in the fractional remainder are broken by lowest index, so the result is
    deterministic. Non-positive total weights fall back to an even split.

    Args:
        weights: Non-negative source weights.
        total: The integer total to distribute.

    Returns:
        Integer allocations summing to ``max(total, 0)``.
    """
    n = len(weights)
    if n == 0 or total <= 0:
        return [0] * n
    weight_sum = sum(weights)
    if weight_sum <= 0:
        base, remainder = divmod(total, n)
        return [base + (1 if i < remainder else 0) for i in range(n)]
    quotas = [w / weight_sum * total for w in weights]
    floors = [int(q) for q in quotas]
    remainder = total - sum(floors)
    by_frac = sorted(range(n), key=lambda i: (-(quotas[i] - floors[i]), i))
    for i in by_frac[:remainder]:
        floors[i] += 1
    return floors


def capacity_aware_apportion(
    weights: Sequence[float], sizes: Sequence[int], total: int
) -> list[int]:
    """Apportion ``total`` by weights without exceeding any source's capacity.

    Slack from a source that cannot absorb its weighted share is redistributed to
    the remaining weighted sources, so no budget is wasted while capacity exists.

    Args:
        weights: Non-negative source weights.
        sizes: Per-source capacities (item counts).
        total: The integer total to distribute.

    Returns:
        Integer allocations, each ``<= sizes[i]``, summing to
        ``min(total, sum(sizes))``.
    """
    n = len(weights)
    alloc = [0] * n
    remaining = min(max(total, 0), sum(sizes))
    while remaining > 0:
        active = [i for i in range(n) if alloc[i] < sizes[i] and weights[i] > 0]
        if not active:
            active = [i for i in range(n) if alloc[i] < sizes[i]]
            if not active:
                break
            for i in active:
                if remaining <= 0:
                    break
                alloc[i] += 1
                remaining -= 1
            continue
        give = largest_remainder([weights[i] for i in active], remaining)
        progressed = False
        for slot, i in enumerate(active):
            add = min(give[slot], sizes[i] - alloc[i])
            if add > 0:
                alloc[i] += add
                remaining -= add
                progressed = True
        if not progressed:  # pragma: no cover - guard against a stuck loop
            i = max(active, key=lambda j: (weights[j], -j))
            alloc[i] += 1
            remaining -= 1
    return alloc


def fill_source(source: Source, sub_budget: int) -> list[Item]:
    """Fill a source's budget share with its highest-salience items.

    The inner selection is identical for every allocator, so differences between
    allocators come only from the budget split, not from item ranking.

    Args:
        source: The source to draw from.
        sub_budget: The number of items the source may contribute.

    Returns:
        The chosen items (at most ``sub_budget``), highest salience first.
    """
    if sub_budget <= 0:
        return []
    ordered = sorted(
        source.items, key=lambda item: (-salience_of(item, 0.0), str(item.id))
    )
    return ordered[:sub_budget]


def allocate_by_weights(
    allocator_id: str,
    sources: Sequence[Source],
    weights: Sequence[float],
    budget: Budget,
    *,
    capacity_aware: bool,
) -> AllocationResult:
    """Turn source weights into an allocation, then fill each share.

    Args:
        allocator_id: Id of the allocator producing the result.
        sources: The competing sources.
        weights: One non-negative weight per source.
        budget: The total budget (in items) to distribute.
        capacity_aware: If ``True``, never over-allocate a source; otherwise a
            source may be handed more budget than it can fill (wasting it).

    Returns:
        The filled context, per-source decisions, and budget statistics.
    """
    sizes = [source.size for source in sources]
    if capacity_aware:
        allocations = capacity_aware_apportion(weights, sizes, budget.limit)
    else:
        allocations = largest_remainder(weights, budget.limit)

    items: list[Item] = []
    decisions: list[AllocationDecision] = []
    for source, allocated, weight in zip(sources, allocations, weights, strict=True):
        filled = fill_source(source, allocated)
        items.extend(filled)
        decisions.append(
            AllocationDecision(
                source_id=source.source_id,
                allocated=allocated,
                filled=len(filled),
                score=float(weight),
            )
        )
    context = Context(items=tuple(items), budget=budget)
    stats = AllocationStats(
        allocator_id=allocator_id,
        num_sources=len(sources),
        budget_limit=budget.limit,
        allocated_total=sum(allocations),
        filled_total=len(items),
    )
    return AllocationResult(context=context, decisions=tuple(decisions), stats=stats)
