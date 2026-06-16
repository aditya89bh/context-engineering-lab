"""Tests for the experiment runner using minimal in-test fakes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.budget import Budget, BudgetUnit, item_cost
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import (
    BenchmarkId,
    ExperimentId,
    ItemId,
    StrategyId,
)
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.metrics import answer_support
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.core.task import Task


class FirstNStrategy:
    """Selects items in input order until the budget is exhausted."""

    @property
    def id(self) -> StrategyId:
        return StrategyId("first-n")

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        chosen: list[Item] = []
        used = 0
        for item in candidates:
            cost = item_cost(item, budget.unit)
            if budget.admits(used, cost):
                chosen.append(item)
                used += cost
        return Context(items=tuple(chosen), budget=budget)


class TwoItemBenchmark:
    """A deterministic benchmark with the target as the first candidate."""

    @property
    def id(self) -> BenchmarkId:
        return BenchmarkId("two-item")

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def declared_metrics(self) -> tuple[str, ...]:
        return ("answer_support",)

    @property
    def budget_sweep(self) -> tuple[Budget, ...]:
        return (Budget(1, BudgetUnit.ITEMS), Budget(2, BudgetUnit.ITEMS))

    def generate(self, seed: int) -> Sequence[Case]:
        target = Item(id=ItemId("target"), content="t", length=1)
        distractor = Item(id=ItemId("distractor"), content="d", length=1)
        return [
            Case(
                case_id="c0",
                task=Task(query="find target"),
                candidates=(target, distractor),
                relevant_ids=frozenset({ItemId("target")}),
            )
        ]

    def evaluate(self, case: Case, context: Context) -> Mapping[str, float]:
        return {"answer_support": answer_support(case.required_ids, context.item_ids)}


def test_runner_produces_results_across_budgets() -> None:
    experiment = Experiment(
        experiment_id=ExperimentId("exp"),
        benchmark=TwoItemBenchmark(),
        strategies=(FirstNStrategy(),),
        seeds=(1, 2),
    )
    result = ExperimentRunner().run(experiment)

    assert len(result.results) == 1
    metrics = result.results[0].metrics
    # 2 seeds x 2 budgets = 4 measurements of the single declared metric.
    assert len(metrics) == 4
    assert {m.name for m in metrics} == {"answer_support"}
    # The target is first, so even a budget of 1 supports the answer.
    assert all(m.value == 1.0 for m in metrics)


def test_runner_metadata_is_deterministic() -> None:
    experiment = Experiment(
        experiment_id=ExperimentId("exp"),
        benchmark=TwoItemBenchmark(),
        strategies=(FirstNStrategy(),),
        seeds=(1,),
    )
    first = ExperimentRunner().run(experiment).metadata.run_id
    second = ExperimentRunner().run(experiment).metadata.run_id
    assert first == second
