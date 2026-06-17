"""Tests for the attention abstractions and the allocator/strategy adapter."""

from __future__ import annotations

from context_engineering_lab.attention import UniformAllocation
from context_engineering_lab.core.attention import (
    SOURCE_QUALITY_KEY,
    AllocationDecision,
    AllocationStats,
    AllocatorStrategy,
    Source,
    group_sources,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY


def _item(name: str, source: str, *, salience: float, quality: float) -> Item:
    meta: dict[str, JsonValue] = {
        SALIENCE_KEY: salience,
        SOURCE_QUALITY_KEY: quality,
    }
    return Item(id=ItemId(name), content=name, length=1, source=source, metadata=meta)


def test_source_size_quality_and_salience() -> None:
    source = Source(
        source_id="s0",
        items=(
            _item("a", "s0", salience=0.4, quality=0.8),
            _item("b", "s0", salience=0.6, quality=0.8),
        ),
    )
    assert source.size == 2
    assert source.quality == 0.8
    assert source.mean_salience == 0.5


def test_source_quality_defaults_to_zero_without_metadata() -> None:
    source = Source(source_id="s0", items=(Item(id=ItemId("a"), content="a"),))
    assert source.quality == 0.0
    assert source.mean_salience == 0.0


def test_group_sources_preserves_first_appearance_order() -> None:
    items = [
        _item("a", "s1", salience=0.1, quality=0.1),
        _item("b", "s0", salience=0.1, quality=0.1),
        _item("c", "s1", salience=0.1, quality=0.1),
    ]
    sources = group_sources(items)
    assert [s.source_id for s in sources] == ["s1", "s0"]
    assert sources[0].size == 2


def test_group_sources_handles_missing_label() -> None:
    sources = group_sources([Item(id=ItemId("a"), content="a")])
    assert sources[0].source_id == "unsourced"


def test_allocation_result_allocations_mapping() -> None:
    items = [
        _item("a", "s0", salience=0.9, quality=0.9),
        _item("b", "s1", salience=0.1, quality=0.1),
    ]
    result = UniformAllocation().allocate(
        group_sources(items), Task(query="q"), Budget(2, BudgetUnit.ITEMS)
    )
    assert result.allocations == {"s0": 1, "s1": 1}
    assert isinstance(result.decisions[0], AllocationDecision)
    assert isinstance(result.stats, AllocationStats)


def test_stats_budget_utilization() -> None:
    stats = AllocationStats(
        allocator_id="a",
        num_sources=2,
        budget_limit=8,
        allocated_total=8,
        filled_total=4,
    )
    assert stats.budget_utilization == 0.5


def test_allocator_strategy_select_matches_allocate_context() -> None:
    allocator = UniformAllocation()
    adapter = AllocatorStrategy(allocator)
    items = [
        _item("a", "s0", salience=0.9, quality=0.9),
        _item("b", "s0", salience=0.2, quality=0.9),
        _item("c", "s1", salience=0.5, quality=0.4),
    ]
    task = Task(query="q")
    budget = Budget(2, BudgetUnit.ITEMS)
    selected = adapter.select(items, task, budget)
    allocated = allocator.allocate(group_sources(items), task, budget).context
    assert selected.item_ids == allocated.item_ids
    assert str(adapter.id) == "uniform-allocation"
    assert isinstance(adapter.allocator, UniformAllocation)
