"""Tests for the built-in strategy compositions."""

from __future__ import annotations

from context_engineering_lab.benchmarks.interaction_presets import memory_pressure
from context_engineering_lab.compositions import (
    default_compositions,
    item_budget_compositions,
    oracle_pipeline,
    token_budget_compositions,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit


def test_composition_ids_are_stable() -> None:
    ids = {str(c.id) for c in default_compositions()}
    assert ids == {
        "temporal->selection",
        "attention->selection",
        "retention->attention",
        "temporal->retention",
        "retention->selection",
        "selection->compression",
        "retention->compression",
        "oracle-pipeline",
    }


def test_grouping_partitions_compositions() -> None:
    item_ids = {str(c.id) for c in item_budget_compositions()}
    token_ids = {str(c.id) for c in token_budget_compositions()}
    assert len(item_budget_compositions()) == 5
    assert len(token_budget_compositions()) == 2
    assert item_ids.isdisjoint(token_ids)
    assert "oracle-pipeline" not in item_ids | token_ids


def test_item_budget_pipeline_respects_item_budget() -> None:
    benchmark = memory_pressure()
    case = benchmark.generate(1)[0]
    budget = Budget(4, BudgetUnit.ITEMS)
    for composition in item_budget_compositions():
        context = composition.select(case.candidates, case.task, budget)
        assert len(context.items) <= 4
        candidate_ids = {item.id for item in case.candidates}
        assert set(context.item_ids) <= candidate_ids


def test_token_budget_pipeline_runs_under_token_budget() -> None:
    benchmark = memory_pressure()
    case = benchmark.generate(1)[0]
    budget = Budget(20, BudgetUnit.TOKENS)
    for composition in token_budget_compositions():
        context = composition.select(case.candidates, case.task, budget)
        assert context.total_cost <= 20


def test_oracle_pipeline_is_single_stage() -> None:
    assert len(oracle_pipeline().steps) == 1
    assert str(oracle_pipeline().id) == "oracle-pipeline"
