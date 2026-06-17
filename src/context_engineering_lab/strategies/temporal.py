"""Temporal selection strategies.

A family of strategies that decide what enters a budget-limited context using
*time*. They span the obvious baselines (oldest-first, fixed/sliding windows), an
age-aware weighting that reads an observable salience signal, and an oracle
ceiling that reads ground-truth relevance.

``RecencySelection`` is the canonical recency baseline and lives in
``strategies/recency.py``; it is reused unchanged by the temporal experiments and
is not redefined here.

All strategies are deterministic: given the same candidates and budget they
produce the same context, with ties broken by item id. They read only
``timestamp`` and observable metadata (salience); none reads ground-truth
relevance — except ``OracleTemporalSelection``, which is a **non-deployable
ceiling** (see its docstring).
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import (
    item_age,
    latest_timestamp,
    salience_of,
)
from context_engineering_lab.strategies._budget_fill import fill_within_budget
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

_OLDEST = float("-inf")
_NEWEST = float("inf")

#: Default number of timeline positions kept by the window strategies.
DEFAULT_WINDOW = 5

#: Default half-life (in age units) for age-weighted decay.
DEFAULT_HALF_LIFE = 4.0


def _timestamp(item: Item, *, missing: float) -> float:
    return item.timestamp if item.timestamp is not None else missing


class OldestFirstSelection:
    """Greedily select the oldest items that fit the budget.

    The temporal counterpart to recency, and a deliberate foil to it: when the
    useful signal is old, oldest-first wins where recency fails. Items without a
    timestamp are treated as oldest.
    """

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId("oldest-first")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Select oldest-first until the budget cannot admit the next item.

        Args:
            candidates: Items available for selection.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context of the oldest items that fit, oldest-to-newest.
        """
        ordered = sorted(
            candidates,
            key=lambda item: (_timestamp(item, missing=_OLDEST), str(item.id)),
        )
        return fill_within_budget(ordered, budget)


class SlidingWindowSelection:
    """Keep only items inside a recency window anchored at "now", then fill.

    The window tracks the most recent timestamp in the candidate set: it admits
    items whose age is at most ``window - 1`` and orders them newest-first. It
    adapts as "now" moves, but discards anything older than the window — so it
    fails when the signal is older than ``window``.
    """

    def __init__(self, window: int = DEFAULT_WINDOW) -> None:
        if window < 1:
            raise ValueError("window must be >= 1")
        self._window = window

    @property
    def window(self) -> int:
        """The number of recent timeline positions retained."""
        return self._window

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId(f"sliding-window-{self._window}")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Filter to the recency window, order newest-first, then fill.

        Args:
            candidates: Items available for selection.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context drawn only from the most recent window of items.
        """
        now = latest_timestamp(candidates)
        in_window = [
            item
            for item in candidates
            if item.timestamp is not None
            and item_age(item, now) <= self._window - 1
        ]
        ordered = sorted(
            in_window,
            key=lambda item: (-item_age(item, now), str(item.id)),
        )
        return fill_within_budget(ordered, budget)


class FixedWindowSelection:
    """Keep only items inside a fixed window at the *start* of the timeline.

    Unlike the sliding window, this window does **not** track "now": it is
    anchored at the oldest timestamp and admits the first ``window`` positions.
    It therefore captures old signal reliably but misses anything that arrives
    later — the canonical failure mode of a fixed window under temporal drift.
    """

    def __init__(self, window: int = DEFAULT_WINDOW) -> None:
        if window < 1:
            raise ValueError("window must be >= 1")
        self._window = window

    @property
    def window(self) -> int:
        """The number of leading timeline positions retained."""
        return self._window

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId(f"fixed-window-{self._window}")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Filter to the fixed leading window, order newest-first, then fill.

        Args:
            candidates: Items available for selection.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context drawn only from the fixed leading window of items.
        """
        stamps = [item.timestamp for item in candidates if item.timestamp is not None]
        if not stamps:
            return Context(items=(), budget=budget)
        start = min(stamps)
        in_window = [
            item
            for item in candidates
            if item.timestamp is not None
            and item.timestamp <= start + (self._window - 1)
        ]
        ordered = sorted(
            in_window,
            key=lambda item: (
                -(item.timestamp if item.timestamp is not None else _OLDEST),
                str(item.id),
            ),
        )
        return fill_within_budget(ordered, budget)


class AgeWeightedSelection:
    """Select by salience discounted for age, highest weight first.

    Scores each item as ``salience * 0.5 ** (age / half_life)``, where salience
    is an *observable* signal read from item metadata (default ``1.0``) and age
    is measured from the most recent timestamp. This is age-aware but deployable:
    it can prefer an older, clearly-salient item over a fresh but unremarkable
    one — something pure recency cannot do. Ties break by recency, then id.
    """

    def __init__(self, half_life: float = DEFAULT_HALF_LIFE) -> None:
        if half_life <= 0:
            raise ValueError("half_life must be positive")
        self._half_life = half_life

    @property
    def half_life(self) -> float:
        """The decay half-life in age units."""
        return self._half_life

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId(f"age-weighted-hl{self._half_life:g}")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Rank by age-discounted salience, then fill within budget.

        Args:
            candidates: Items available for selection.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context of the highest-weight items that fit the budget.
        """
        now = latest_timestamp(candidates)

        def weight(item: Item) -> float:
            decay = 0.5 ** (item_age(item, now) / self._half_life)
            return float(salience_of(item) * decay)

        ordered = sorted(
            candidates,
            key=lambda item: (-weight(item), -item_age(item, now), str(item.id)),
        )
        return fill_within_budget(ordered, budget)


class OracleTemporalSelection:
    """Select ground-truth relevant items first (upper bound only).

    A **non-deployable ceiling.** It reads the privileged relevance marker a
    benchmark writes into item metadata — information no real system has at
    selection time — and admits relevant items before any others, newest-first
    among ties. Use it to bound how much temporal headroom remains for the
    deployable strategies; never ship it.
    """

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the strategy."""
        return StrategyId("oracle-temporal")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Order relevant-flagged items first (newest-first), then fill.

        Args:
            candidates: Items available for selection. Relevant items are
                identified by the ``ORACLE_RELEVANCE_KEY`` metadata flag.
            task: Unused; present for interface conformance.
            budget: The constraint the returned context must satisfy.

        Returns:
            A context that includes as many relevant items as the budget allows,
            before any irrelevant items.
        """
        now = latest_timestamp(candidates)

        def is_relevant(item: Item) -> bool:
            return bool(item.metadata.get(ORACLE_RELEVANCE_KEY, False))

        ordered = sorted(
            candidates,
            key=lambda item: (
                0 if is_relevant(item) else 1,
                -item_age(item, now, missing=_NEWEST),
                str(item.id),
            ),
        )
        return fill_within_budget(ordered, budget)
