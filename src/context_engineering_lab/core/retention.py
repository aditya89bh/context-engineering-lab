"""The retention interface.

A *retention policy* decides, under a memory budget, which items to **keep** and
which to **forget**. This is the forgetting counterpart to selection: selection
chooses what enters a context for one task; retention chooses what survives in a
bounded memory. Phase 5 studies the *policy* — what should be kept — not a memory
store, persistence layer, or eviction schedule.

The interface is deliberately small:

* :class:`RetentionPolicy` — a protocol with an ``id`` and a ``retain`` method.
* :class:`RetentionDecision` — the keep/forget decision for a single item.
* :class:`RetentionStats` — the count accounting a retention produces.
* :class:`RetentionResult` — the retained context, the per-item decisions, and
  the stats.
* :class:`PolicyStrategy` — adapts any policy to the
  :class:`~context_engineering_lab.core.strategy.Strategy` interface so the
  existing experiment runner can drive it unchanged.

No memory database, no persistence, no network access — Phase 5 policies are
deterministic, local, and synthetic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task

#: Metadata key carrying an *observable* access-frequency count (a non-negative
#: integer). Like salience, frequency is a noisy proxy a deployable policy may
#: read; it is not a ground-truth relevance label. Defaults to ``0`` when absent.
FREQUENCY_KEY = "frequency"


@dataclass(frozen=True, slots=True)
class RetentionDecision:
    """The keep/forget decision for a single item.

    Args:
        item_id: The item the decision concerns.
        retained: ``True`` if the item is kept, ``False`` if it is forgotten.
        score: The policy's score for the item (higher means more worth keeping).
    """

    item_id: ItemId
    retained: bool
    score: float


@dataclass(frozen=True, slots=True)
class RetentionStats:
    """Count accounting for a single retention.

    Args:
        policy_id: Id of the policy that produced the result.
        considered: Number of items the policy saw.
        retained: Number of items kept.
        forgotten: Number of items dropped.
        budget_limit: The memory budget limit (in items).
    """

    policy_id: str
    considered: int
    retained: int
    forgotten: int
    budget_limit: int

    @property
    def memory_budget_utilization(self) -> float:
        """Retained count over the budget limit (``> 1`` if over budget)."""
        if self.budget_limit <= 0:
            return 0.0
        return self.retained / self.budget_limit


@dataclass(frozen=True, slots=True)
class RetentionResult:
    """The output of a retention policy: a kept context, decisions, and stats."""

    context: Context
    decisions: tuple[RetentionDecision, ...]
    stats: RetentionStats

    @property
    def retained_ids(self) -> frozenset[ItemId]:
        """Ids of the items the policy kept."""
        return frozenset(d.item_id for d in self.decisions if d.retained)

    @property
    def forgotten_ids(self) -> frozenset[ItemId]:
        """Ids of the items the policy forgot."""
        return frozenset(d.item_id for d in self.decisions if not d.retained)


@runtime_checkable
class RetentionPolicy(Protocol):
    """A policy that keeps some items and forgets the rest under a budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the policy."""
        ...

    def retain(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> RetentionResult:
        """Decide which items to keep within a memory budget.

        Args:
            items: The items currently in memory.
            task: The task; supplies the query for query-aware policies.
            budget: The memory budget the kept set should satisfy. A
                retain-all baseline may intentionally exceed it.

        Returns:
            The retained context, per-item decisions, and count statistics.
        """
        ...


class PolicyStrategy:
    """Adapt a :class:`RetentionPolicy` to the ``Strategy`` interface.

    The experiment runner calls ``select``; this adapter forwards to the wrapped
    policy's ``retain`` and returns its context, so retention policies run through
    the same harness as selection strategies.

    Args:
        policy: The retention policy to wrap.
    """

    def __init__(self, policy: RetentionPolicy) -> None:
        self._policy = policy

    @property
    def id(self) -> StrategyId:
        """Stable identifier, taken from the wrapped policy."""
        return self._policy.id

    @property
    def policy(self) -> RetentionPolicy:
        """The wrapped retention policy."""
        return self._policy

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Return the retained context for the candidates under the budget."""
        return self._policy.retain(candidates, task, budget).context
