"""Tests for the composition abstraction and pipeline execution."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.composition import (
    CompositionResult,
    PipelineStep,
    StepRecord,
    StrategyComposition,
)
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task


class _RecordingFirstN:
    """A fake strategy: keep the first ``budget.limit`` items, by id order."""

    def __init__(self, strategy_id: str) -> None:
        self._id = StrategyId(strategy_id)
        self.received_budgets: list[int] = []

    @property
    def id(self) -> StrategyId:
        return self._id

    def select(
        self, candidates: Sequence[Item], task: Task, budget: Budget
    ) -> Context:
        self.received_budgets.append(budget.limit)
        ordered = sorted(candidates, key=lambda item: str(item.id))
        return Context(items=tuple(ordered[: budget.limit]), budget=budget)


def _items(n: int) -> tuple[Item, ...]:
    return tuple(
        Item(id=ItemId(f"i{k:02d}"), content=f"item {k}", length=1) for k in range(n)
    )


def _task() -> Task:
    return Task(query="q")


def _budget(limit: int) -> Budget:
    return Budget(limit, BudgetUnit.ITEMS)


def test_empty_steps_rejected() -> None:
    with pytest.raises(ValueError, match="at least one step"):
        StrategyComposition(())


def test_widen_must_be_positive() -> None:
    with pytest.raises(ValueError, match="widen"):
        StrategyComposition((_RecordingFirstN("a"),), widen=0)


def test_default_id_joins_step_ids() -> None:
    comp = StrategyComposition((_RecordingFirstN("a"), _RecordingFirstN("b")))
    assert str(comp.id) == "a->b"


def test_explicit_id_is_used() -> None:
    comp = StrategyComposition(
        (_RecordingFirstN("a"),), composition_id="custom-pipeline"
    )
    assert str(comp.id) == "custom-pipeline"


def test_pipeline_step_id_mirrors_strategy() -> None:
    step = PipelineStep(_RecordingFirstN("a"))
    assert str(step.id) == "a"


def test_final_step_receives_real_budget_others_widened() -> None:
    first = _RecordingFirstN("a")
    second = _RecordingFirstN("b")
    comp = StrategyComposition((first, second), widen=3)
    comp.select(_items(10), _task(), _budget(2))
    assert first.received_budgets == [6]  # widened: 2 * 3
    assert second.received_budgets == [2]  # the real budget


def test_run_records_per_stage_counts() -> None:
    comp = StrategyComposition(
        (_RecordingFirstN("a"), _RecordingFirstN("b")), widen=2
    )
    result = comp.run(_items(10), _task(), _budget(3))
    assert isinstance(result, CompositionResult)
    assert result.steps == (
        StepRecord(step_id="a", input_count=10, output_count=6),
        StepRecord(step_id="b", input_count=6, output_count=3),
    )


def test_final_context_respects_budget() -> None:
    comp = StrategyComposition((_RecordingFirstN("a"), _RecordingFirstN("b")))
    context = comp.select(_items(20), _task(), _budget(4))
    assert len(context.items) == 4
    assert context.budget.limit == 4


def test_select_matches_run_context() -> None:
    comp = StrategyComposition((_RecordingFirstN("a"), _RecordingFirstN("b")))
    items, task, budget = _items(12), _task(), _budget(5)
    assert comp.select(items, task, budget).item_ids == comp.run(
        items, task, budget
    ).context.item_ids


def test_single_stage_pipeline_passes_budget_through() -> None:
    only = _RecordingFirstN("a")
    comp = StrategyComposition((only,))
    comp.select(_items(5), _task(), _budget(2))
    assert only.received_budgets == [2]
