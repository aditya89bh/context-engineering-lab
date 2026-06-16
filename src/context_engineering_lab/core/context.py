"""Contexts.

A :class:`Context` is the bounded set of items a strategy produces for a
consumer. It validates against its budget on construction: by default a context
whose total cost exceeds its budget is rejected, so over-budget contexts cannot
be created silently.
"""

from __future__ import annotations

from dataclasses import dataclass

from context_engineering_lab.core.budget import Budget, item_cost
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item


@dataclass(frozen=True, slots=True)
class Context:
    """An ordered, budget-bounded collection of items.

    Args:
        items: The items placed in context, in priority order.
        budget: The budget the context is constrained by.
        allow_overflow: If ``True``, a context whose total cost exceeds the
            budget is permitted (and flagged) rather than rejected. Defaults to
            ``False`` so overflow must always be explicit.
    """

    items: tuple[Item, ...]
    budget: Budget
    allow_overflow: bool = False

    def __post_init__(self) -> None:
        if not self.allow_overflow and self.total_cost > self.budget.limit:
            raise ValueError(
                "context total cost "
                f"{self.total_cost} exceeds budget {self.budget.limit} "
                f"({self.budget.unit.value}); set allow_overflow=True to permit"
            )

    @property
    def total_cost(self) -> int:
        """Total cost of all items under the budget's unit."""
        return sum(item_cost(item, self.budget.unit) for item in self.items)

    @property
    def item_ids(self) -> frozenset[ItemId]:
        """The set of item ids present in the context."""
        return frozenset(item.id for item in self.items)

    @property
    def is_over_budget(self) -> bool:
        """Whether the context's total cost exceeds its budget."""
        return self.total_cost > self.budget.limit

    def __len__(self) -> int:
        return len(self.items)
