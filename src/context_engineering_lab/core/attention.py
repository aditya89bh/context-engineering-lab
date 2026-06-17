"""The attention-allocation interface.

An *attention allocator* decides how to divide a fixed budget across several
competing **sources** of information *before* any items are selected. This is a
different operation from selection: selection ranks and picks items; allocation
splits a budget into per-source shares, and only then does a fixed inner
selection fill each share. Phase 6 studies the *allocation policy* — how capacity
should be distributed — not a scheduler, agent loop, or event system.

The interface is deliberately small:

* :class:`Source` — a named group of candidate items with an observable quality.
* :class:`AttentionAllocator` — a protocol with an ``id`` and an ``allocate``
  method.
* :class:`AllocationDecision` — the budget share a single source received.
* :class:`AllocationStats` — the budget accounting an allocation produces.
* :class:`AllocationResult` — the filled context, the per-source decisions, and
  the stats.
* :class:`AllocatorStrategy` — adapts any allocator to the
  :class:`~context_engineering_lab.core.strategy.Strategy` interface so the
  existing experiment runner can drive it unchanged.

No scheduler, no agent loop, no network access — Phase 6 allocators are
deterministic, local, and synthetic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import salience_of

#: Metadata key carrying an *observable* per-source quality score in ``[0, 1]``.
#: It is a (noisy) proxy for how much signal a source holds — a deployable
#: allocator may read it; it is not a ground-truth relevance label.
SOURCE_QUALITY_KEY = "source_quality"


@dataclass(frozen=True, slots=True)
class Source:
    """A named group of candidate items competing for budget.

    Args:
        source_id: Stable identifier for the source.
        items: The candidate items belonging to the source.
    """

    source_id: str
    items: tuple[Item, ...]

    @property
    def size(self) -> int:
        """Number of items the source holds."""
        return len(self.items)

    @property
    def quality(self) -> float:
        """Observable quality score, read from the items' metadata (``0`` if absent)."""
        for item in self.items:
            value = item.metadata.get(SOURCE_QUALITY_KEY)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            return float(value)
        return 0.0

    @property
    def mean_salience(self) -> float:
        """Mean observable salience of the source's items (``0`` if empty)."""
        if not self.items:
            return 0.0
        return sum(salience_of(item, 0.0) for item in self.items) / len(self.items)


def group_sources(items: Sequence[Item]) -> tuple[Source, ...]:
    """Group items into sources by their ``source`` label, preserving order.

    Items without a ``source`` label are grouped under the source id
    ``"unsourced"``. The order of sources is the order in which their first item
    appears, so grouping is deterministic.

    Args:
        items: The candidate items to group.

    Returns:
        The sources, in first-appearance order.
    """
    order: list[str] = []
    buckets: dict[str, list[Item]] = {}
    for item in items:
        key = item.source if item.source is not None else "unsourced"
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(item)
    return tuple(Source(source_id=key, items=tuple(buckets[key])) for key in order)


@dataclass(frozen=True, slots=True)
class AllocationDecision:
    """The budget share a single source received.

    Args:
        source_id: The source the decision concerns.
        allocated: Budget (in items) assigned to the source.
        filled: Items actually placed from the source (``<= allocated``).
        score: The allocator's weight for the source (higher attracts budget).
    """

    source_id: str
    allocated: int
    filled: int
    score: float


@dataclass(frozen=True, slots=True)
class AllocationStats:
    """Budget accounting for a single allocation.

    Args:
        allocator_id: Id of the allocator that produced the result.
        num_sources: Number of sources the allocator saw.
        budget_limit: The total budget (in items) to distribute.
        allocated_total: Sum of budget assigned across sources.
        filled_total: Sum of items actually placed across sources.
    """

    allocator_id: str
    num_sources: int
    budget_limit: int
    allocated_total: int
    filled_total: int

    @property
    def budget_utilization(self) -> float:
        """Items placed over the budget limit (``< 1`` when attention is wasted)."""
        if self.budget_limit <= 0:
            return 0.0
        return self.filled_total / self.budget_limit


@dataclass(frozen=True, slots=True)
class AllocationResult:
    """The output of an allocator: a filled context, decisions, and stats."""

    context: Context
    decisions: tuple[AllocationDecision, ...]
    stats: AllocationStats

    @property
    def allocations(self) -> dict[str, int]:
        """Mapping of source id to the budget it was allocated."""
        return {d.source_id: d.allocated for d in self.decisions}


@runtime_checkable
class AttentionAllocator(Protocol):
    """A policy that splits a budget across competing sources."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the allocator."""
        ...

    def allocate(
        self,
        sources: Sequence[Source],
        task: Task,
        budget: Budget,
    ) -> AllocationResult:
        """Distribute a budget across sources, then fill each share.

        Args:
            sources: The competing sources.
            task: The task; supplies the query for query-aware allocators.
            budget: The total budget (in items) to distribute.

        Returns:
            The filled context, per-source decisions, and budget statistics.
        """
        ...


class AllocatorStrategy:
    """Adapt an :class:`AttentionAllocator` to the ``Strategy`` interface.

    The experiment runner calls ``select``; this adapter groups the flat
    candidate list into sources (by their ``source`` label) and forwards to the
    wrapped allocator's ``allocate``, returning its context, so allocators run
    through the same harness as selection strategies.

    Args:
        allocator: The allocator to wrap.
    """

    def __init__(self, allocator: AttentionAllocator) -> None:
        self._allocator = allocator

    @property
    def id(self) -> StrategyId:
        """Stable identifier, taken from the wrapped allocator."""
        return self._allocator.id

    @property
    def allocator(self) -> AttentionAllocator:
        """The wrapped allocator."""
        return self._allocator

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Group candidates into sources and return the allocated context."""
        sources = group_sources(candidates)
        return self._allocator.allocate(sources, task, budget).context
