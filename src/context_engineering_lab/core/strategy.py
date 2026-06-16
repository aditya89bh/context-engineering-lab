"""The strategy interface.

A strategy is a named policy that, given candidate items, a task, and a budget,
produces a :class:`~context_engineering_lab.core.context.Context`. This single
interface is deliberately broad enough to express selection, compression,
temporal weighting, and attention-budget allocation in later phases: a
compressor, for instance, returns a context whose items are shortened, while a
selector returns a subset.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task


@runtime_checkable
class Strategy(Protocol):
    """A policy that turns candidate items into a budget-bounded context."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        ...

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Produce a context from candidates under a budget.

        Implementations must return a context that respects ``budget`` (i.e. one
        that does not set ``allow_overflow``), so the harness can trust that a
        strategy honored its constraint.

        Args:
            candidates: The items available for selection.
            task: What the consumer is trying to do.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context containing the chosen (and possibly transformed) items.
        """
        ...
