"""Tests for the built-in catalog and result persistence."""

from __future__ import annotations

from pathlib import Path

from context_engineering_lab.catalog import (
    build_benchmark_registry,
    build_strategy_registry,
)
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.reporting.persistence import read_result, write_result


def test_catalog_contains_builtins() -> None:
    strategies = build_strategy_registry()
    benchmarks = build_benchmark_registry()
    assert "recency" in strategies
    assert "harness-smoke" in benchmarks


def test_result_persistence_round_trip(tmp_path: Path) -> None:
    strategies = build_strategy_registry()
    benchmarks = build_benchmark_registry()
    experiment = Experiment(
        experiment_id=ExperimentId("smoke"),
        benchmark=benchmarks.get("harness-smoke"),
        strategies=(strategies.get("recency"),),
        seeds=(1,),
    )
    result = ExperimentRunner().run(experiment)

    path = write_result(result, tmp_path / "nested" / "result.json")
    assert path.exists()
    restored = read_result(path)
    assert restored == result
