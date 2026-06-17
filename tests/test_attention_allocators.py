"""Tests for the deterministic attention allocators."""

from __future__ import annotations

import pytest

from context_engineering_lab.attention import (
    AdaptiveAllocation,
    OracleAllocation,
    ProportionalAllocation,
    SalienceAllocation,
    UniformAllocation,
    WinnerTakeMostAllocation,
    default_allocators,
)
from context_engineering_lab.core.attention import (
    SOURCE_QUALITY_KEY,
    Source,
    group_sources,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

TASK = Task(query="allocate")
BUDGET = Budget(6, BudgetUnit.ITEMS)


def _source(
    source_id: str, *, size: int, signal: int, salience: float, quality: float
) -> Source:
    items: list[Item] = []
    for k in range(size):
        meta: dict[str, JsonValue] = {
            ORACLE_RELEVANCE_KEY: k < signal,
            SALIENCE_KEY: salience,
            SOURCE_QUALITY_KEY: quality,
        }
        items.append(
            Item(
                id=ItemId(f"{source_id}-i{k}"),
                content=f"{source_id}-{k}",
                length=1,
                source=source_id,
                metadata=meta,
            )
        )
    return Source(source_id=source_id, items=tuple(items))


def _sources() -> tuple[Source, ...]:
    return (
        _source("s0", size=2, signal=2, salience=0.9, quality=0.9),
        _source("s1", size=6, signal=0, salience=0.8, quality=0.2),
        _source("s2", size=4, signal=3, salience=0.3, quality=0.5),
    )


def test_uniform_splits_evenly() -> None:
    result = UniformAllocation().allocate(_sources(), TASK, BUDGET)
    assert result.allocations == {"s0": 2, "s1": 2, "s2": 2}


def test_proportional_favors_the_largest_source() -> None:
    alloc = ProportionalAllocation().allocate(_sources(), TASK, BUDGET).allocations
    assert max(alloc, key=lambda k: alloc[k]) == "s1"


def test_salience_favors_the_most_salient_source() -> None:
    alloc = SalienceAllocation().allocate(_sources(), TASK, BUDGET).allocations
    assert max(alloc, key=lambda k: alloc[k]) == "s0"


def test_adaptive_is_capacity_aware_and_quality_led() -> None:
    alloc = AdaptiveAllocation().allocate(_sources(), TASK, BUDGET).allocations
    assert alloc["s0"] <= 2  # never exceeds the source's capacity
    assert alloc["s2"] > alloc["s1"]  # quality 0.5 beats 0.2


def test_winner_take_most_favors_top_quality_source() -> None:
    alloc = WinnerTakeMostAllocation().allocate(_sources(), TASK, BUDGET).allocations
    assert max(alloc, key=lambda k: alloc[k]) == "s0"


def test_oracle_starves_the_zero_signal_source() -> None:
    result = OracleAllocation().allocate(_sources(), TASK, BUDGET)
    assert result.allocations["s1"] == 0
    # It captures every signal item that fits the budget.
    selected = {str(i) for i in result.context.item_ids}
    assert "s0-i0" in selected and "s2-i0" in selected


def test_all_allocators_respect_budget_and_capacity() -> None:
    sources = _sources()
    for allocator in default_allocators():
        result = allocator.allocate(sources, TASK, BUDGET)
        assert result.context.total_cost <= BUDGET.limit
        for decision in result.decisions:
            source = next(s for s in sources if s.source_id == decision.source_id)
            assert decision.filled <= source.size


def test_allocators_are_deterministic() -> None:
    for allocator in default_allocators():
        first = allocator.allocate(_sources(), TASK, BUDGET).context.item_ids
        second = allocator.allocate(_sources(), TASK, BUDGET).context.item_ids
        assert first == second


def test_winner_take_most_rejects_bad_concentration() -> None:
    with pytest.raises(ValueError):
        WinnerTakeMostAllocation(concentration=0.0)
    with pytest.raises(ValueError):
        WinnerTakeMostAllocation(concentration=1.5)


def test_single_source_winner_take_most_allocates_all() -> None:
    one = (_source("s0", size=4, signal=2, salience=0.5, quality=0.5),)
    result = WinnerTakeMostAllocation().allocate(one, TASK, BUDGET)
    # The whole budget is steered to the only source (it is not capacity-aware),
    # but only the four available items can actually fill.
    assert result.allocations["s0"] == BUDGET.limit
    assert result.decisions[0].filled == 4


def test_allocator_via_grouped_candidates() -> None:
    flat = [item for source in _sources() for item in source.items]
    grouped = group_sources(flat)
    assert {s.source_id for s in grouped} == {"s0", "s1", "s2"}
