"""Tests for the harness smoke benchmark."""

from __future__ import annotations

from context_engineering_lab.benchmarks.smoke import SmokeBenchmark
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.context import Context
from context_engineering_lab.strategies.recency import RecencySelection


def test_generation_is_deterministic() -> None:
    bench = SmokeBenchmark()
    first = bench.generate(7)
    second = bench.generate(7)
    assert [c.case_id for c in first] == [c.case_id for c in second]
    assert [c.candidates[0].id for c in first] == [c.candidates[0].id for c in second]


def test_each_case_has_one_target_among_distractors() -> None:
    bench = SmokeBenchmark()
    cases = bench.generate(1)
    assert len(cases) > 0
    for case in cases:
        assert len(case.relevant_ids) == 1
        assert len(case.candidates) == 6
        assert case.relevant_ids <= {item.id for item in case.candidates}


def test_full_budget_supports_the_answer() -> None:
    bench = SmokeBenchmark()
    strategy = RecencySelection()
    big_budget = Budget(6, BudgetUnit.ITEMS)
    for case in bench.generate(3):
        context = strategy.select(case.candidates, case.task, big_budget)
        scores = bench.evaluate(case, context)
        assert scores["answer_support"] == 1.0
        assert scores["selection_recall"] == 1.0


def test_metrics_are_in_unit_interval() -> None:
    bench = SmokeBenchmark()
    strategy = RecencySelection()
    for case in bench.generate(2):
        context: Context = strategy.select(
            case.candidates, case.task, Budget(2, BudgetUnit.ITEMS)
        )
        for name, value in bench.evaluate(case, context).items():
            assert 0.0 <= value <= 1.0, name
