"""Tests for Phase 10 perturbation abstractions and registry."""

from __future__ import annotations

import random

import pytest

from context_engineering_lab.core.benchmark import Benchmark, Case
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId, ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.perturbations.base import (
    BasePerturbation,
    Perturbation,
    PerturbationConfig,
    PerturbationResult,
    PerturbedBenchmark,
)
from context_engineering_lab.perturbations.registry import (
    build_perturbation_registry,
    load_perturbation,
    perturb,
    perturb_by_id,
)
from context_engineering_lab.seeding import DEFAULT_SEED


def _case(case_id: str = "c0") -> Case:
    items = (
        Item(id=ItemId("a"), content="alpha", metadata={"oracle_relevant": True}),
        Item(id=ItemId("b"), content="beta"),
    )
    return Case(
        case_id=case_id,
        task=Task(query="alpha"),
        candidates=items,
        relevant_ids=frozenset({ItemId("a")}),
    )


class _AddOne(BasePerturbation):
    """Inject a single fixed distractor; rewrite the first item's content."""

    def apply(self, case: Case, rng: random.Random) -> PerturbationResult:
        extra = Item(id=ItemId(f"x-{rng.randint(0, 9)}"), content="noise")
        rewritten = (
            Item(id=case.candidates[0].id, content="alpha-prime"),
            *case.candidates[1:],
            extra,
        )
        new_case = Case(
            case_id=case.case_id,
            task=case.task,
            candidates=rewritten,
            relevant_ids=case.relevant_ids,
            required_ids=case.required_ids,
        )
        return PerturbationResult(
            perturbation_id=self.id,
            case=new_case,
            items_added=1,
            items_modified=1,
        )


def _perturbation() -> _AddOne:
    return _AddOne(PerturbationConfig(perturbation_id="add-one", count=1))


def test_config_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        PerturbationConfig(perturbation_id="")


@pytest.mark.parametrize("intensity", [-0.1, 1.1])
def test_config_rejects_out_of_range_intensity(intensity: float) -> None:
    with pytest.raises(ValueError, match="intensity"):
        PerturbationConfig(perturbation_id="p", intensity=intensity)


def test_config_rejects_negative_count() -> None:
    with pytest.raises(ValueError, match="count"):
        PerturbationConfig(perturbation_id="p", count=-1)


def test_base_perturbation_exposes_id_and_config() -> None:
    pert = _perturbation()
    assert pert.id == "add-one"
    assert pert.config.count == 1
    assert isinstance(pert, Perturbation)


def test_apply_reports_added_and_modified_counts() -> None:
    result = _perturbation().apply(_case(), random.Random(0))
    assert isinstance(result, PerturbationResult)
    assert result.items_added == 1
    assert result.items_modified == 1
    assert len(result.case.candidates) == 3
    assert result.case.candidates[0].content == "alpha-prime"


def test_base_perturbation_apply_not_implemented() -> None:
    base = BasePerturbation(PerturbationConfig(perturbation_id="bare"))
    with pytest.raises(NotImplementedError):
        base.apply(_case(), random.Random(0))


class _OneCaseBenchmark:
    """A minimal benchmark exposing one case for wrapper tests."""

    @property
    def id(self) -> BenchmarkId:
        return BenchmarkId("base-bench")

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def declared_metrics(self) -> tuple[str, ...]:
        return ("selection_recall",)

    @property
    def budget_sweep(self) -> tuple[Budget, ...]:
        return (Budget(limit=2, unit=BudgetUnit.ITEMS),)

    def generate(self, seed: int) -> list[Case]:
        return [_case("only")]

    def evaluate(self, case: Case, context: Context) -> dict[str, float]:
        return {"selection_recall": float(len(context.item_ids))}


def test_perturbed_benchmark_conforms_to_protocol() -> None:
    wrapped = PerturbedBenchmark(_OneCaseBenchmark(), _perturbation())
    assert isinstance(wrapped, Benchmark)
    assert str(wrapped.id) == "base-bench+add-one"
    assert wrapped.version == "1.0"
    assert wrapped.declared_metrics == ("selection_recall",)


def test_perturbed_benchmark_applies_perturbation_to_cases() -> None:
    wrapped = PerturbedBenchmark(_OneCaseBenchmark(), _perturbation())
    cases = wrapped.generate(DEFAULT_SEED)
    assert len(cases) == 1
    assert len(cases[0].candidates) == 3
    assert cases[0].relevant_ids == frozenset({ItemId("a")})


def test_perturbed_benchmark_generate_is_deterministic() -> None:
    wrapped = PerturbedBenchmark(_OneCaseBenchmark(), _perturbation())
    first = wrapped.generate(7)
    second = wrapped.generate(7)
    assert [i.id for i in first[0].candidates] == [i.id for i in second[0].candidates]


def test_perturbed_benchmark_delegates_evaluate() -> None:
    inner = _OneCaseBenchmark()
    wrapped = PerturbedBenchmark(inner, _perturbation())
    case = _case()
    budget = Budget(limit=5, unit=BudgetUnit.ITEMS)
    context = Context(items=case.candidates, budget=budget)
    assert wrapped.evaluate(case, context) == inner.evaluate(case, context)


def test_registry_registers_and_lists() -> None:
    registry = build_perturbation_registry([_perturbation()])
    assert registry.names() == ["add-one"]
    assert load_perturbation("add-one", registry).id == "add-one"


def test_registry_rejects_duplicates() -> None:
    with pytest.raises(ValueError, match="already registered"):
        build_perturbation_registry([_perturbation(), _perturbation()])


def test_default_registry_is_empty_or_unique() -> None:
    registry = build_perturbation_registry()
    assert len(registry.names()) == len(set(registry.names()))


def test_perturb_helpers_build_wrappers() -> None:
    pert = _perturbation()
    direct = perturb(_OneCaseBenchmark(), pert)
    assert str(direct.id) == "base-bench+add-one"
    registry = build_perturbation_registry([pert])
    by_id = perturb_by_id(_OneCaseBenchmark(), "add-one", registry)
    assert str(by_id.id) == "base-bench+add-one"
