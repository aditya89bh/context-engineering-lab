"""Budgets and budget units.

A :class:`Budget` is the hard constraint on a context. It pairs a positive limit
with a :class:`BudgetUnit` that determines how the cost of an item is measured.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from context_engineering_lab.core.item import Item


class BudgetUnit(Enum):
    """The unit in which a budget and item costs are measured."""

    ITEMS = "items"
    TOKENS = "tokens"
    CHARACTERS = "characters"


def item_cost(item: Item, unit: BudgetUnit) -> int:
    """Return the cost of an item under the given budget unit.

    Args:
        item: The item to measure.
        unit: The unit to measure in.

    Returns:
        The non-negative integer cost of the item.
    """
    if unit is BudgetUnit.ITEMS:
        return 1
    if unit is BudgetUnit.TOKENS:
        return item.length
    return len(item.content)


@dataclass(frozen=True, slots=True)
class Budget:
    """A positive limit expressed in a given unit.

    Args:
        limit: The maximum total cost permitted. Must be strictly positive.
        unit: The unit the limit is expressed in.
    """

    limit: int
    unit: BudgetUnit = BudgetUnit.ITEMS

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError(f"budget limit must be positive, got {self.limit}")

    def admits(self, used: int, additional: int) -> bool:
        """Return whether adding ``additional`` cost keeps within the limit.

        Args:
            used: Cost already consumed.
            additional: Cost of the item under consideration.

        Returns:
            ``True`` if ``used + additional`` does not exceed the limit.
        """
        return used + additional <= self.limit
