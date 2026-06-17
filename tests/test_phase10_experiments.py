"""Tests for Phase 10 robustness experiments and aggregation."""

from __future__ import annotations

from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase10 import (
    RobustnessSpec,
    robustness_experiments,
    robustness_specs,
)
from context_engineering_lab.perturbations.aggregation import aggregate_robustness


def test_specs_cover_the_four_stress_groups() -> None:
    groups = {spec.group for spec in robustness_specs()}
    assert groups == {
        "distractor-stress",
        "contradiction-stress",
        "stale-amplification",
        "corruption-stress",
    }


def test_experiments_include_baseline_and_each_perturbation() -> None:
    experiments = robustness_experiments()
    for spec in robustness_specs():
        assert spec.baseline_name() in experiments
        for perturbation_id in spec.perturbations:
            assert spec.perturbed_name(perturbation_id) in experiments


def test_perturbed_experiment_benchmark_ids_are_suffixed() -> None:
    experiments = robustness_experiments()
    corruption = next(s for s in robustness_specs() if s.group == "corruption-stress")
    base_id = str(corruption.benchmark.id)
    perturbed = experiments[corruption.perturbed_name("salience-corruption")]
    assert str(perturbed.benchmark.id) == f"{base_id}+salience-corruption"


def _run_spec(spec: RobustnessSpec) -> list[ExperimentResult]:
    runner = ExperimentRunner()
    experiments = robustness_experiments()
    names = [spec.baseline_name()]
    names += [spec.perturbed_name(p) for p in spec.perturbations]
    return [runner.run(experiments[name]) for name in names]


def test_aggregate_robustness_produces_comparisons_and_shifts() -> None:
    spec = next(s for s in robustness_specs() if s.group == "distractor-stress")
    results = _run_spec(spec)
    agg = aggregate_robustness(results, [spec])
    assert agg.comparisons
    assert agg.groups() == ["distractor-stress"]
    assert "distractor-injection" in agg.perturbations()
    assert all(0.0 <= row.comparison.robustness <= 1.0 for row in agg.comparisons)


def test_aggregate_robustness_is_deterministic() -> None:
    spec = next(s for s in robustness_specs() if s.group == "distractor-stress")
    first = aggregate_robustness(_run_spec(spec), [spec])
    second = aggregate_robustness(_run_spec(spec), [spec])
    assert [r.comparison for r in first.comparisons] == [
        r.comparison for r in second.comparisons
    ]


def test_oracle_shifts_exclude_oracle_strategy() -> None:
    spec = next(s for s in robustness_specs() if s.group == "contradiction-stress")
    agg = aggregate_robustness(_run_spec(spec), [spec])
    assert all("oracle" not in s.strategy_id for s in agg.oracle_shifts)
