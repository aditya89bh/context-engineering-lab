"""Shared greedy budget-fill helper.

Most selection strategies differ only in *how they order* candidates; once an
order is fixed, they all greedily admit items until the budget cannot fit the
next one. This helper captures that common step so each strategy implements only
its ordering.
"""

from __future__ import annotations

from collections.abc import Iterable

from context_engineering_lab.core.budget import Budget, item_cost
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.item import Item


def fill_within_budget(ordered: Iterable[Item], budget: Budget) -> Context:
    """Greedily admit items in the given order until the budget is exhausted.

    Items that do not fit are skipped (a later, smaller item may still fit), so
    the returned context never exceeds the budget.

    Args:
        ordered: Candidate items in the priority order the strategy chose.
        budget: The constraint the returned context must satisfy.

    Returns:
        A context of the admitted items, preserving the given order.
    """
    chosen: list[Item] = []
    used = 0
    for item in ordered:
        cost = item_cost(item, budget.unit)
        if budget.admits(used, cost):
            chosen.append(item)
            used += cost
    return Context(items=tuple(chosen), budget=budget)
