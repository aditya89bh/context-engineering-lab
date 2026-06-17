"""Reproducibility validation against the checked-in example artifact.

This is the executable form of the determinism guarantee documented in
``docs/reproducibility.md``: regenerating the example experiment must reproduce
the committed reference file in ``docs/examples/`` byte-for-byte, once the two
machine-specific observation fields are normalized. It also re-asserts that a
fresh run is identical to itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from context_engineering_lab import Experiment, ExperimentRunner
from context_engineering_lab.catalog import (
    build_benchmark_registry,
    build_strategy_registry,
)
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.seeding import DEFAULT_SEED

_EXAMPLE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "examples"
    / "easy-selection-experiment.json"
)


def _build_example() -> dict[str, Any]:
    strategies = build_strategy_registry()
    benchmark = build_benchmark_registry().get("easy-selection")
    experiment = Experiment(
        experiment_id=ExperimentId("example-easy-selection"),
        benchmark=benchmark,
        strategies=(
            strategies.get("first-n"),
            strategies.get("keyword-overlap"),
            strategies.get("oracle"),
        ),
        seeds=(DEFAULT_SEED,),
        budgets=(benchmark.budget_sweep[0],),
    )
    data = ExperimentRunner().run(experiment).to_dict()
    data["metadata"]["python_version"] = "example"
    data["metadata"]["platform"] = "example"
    return data


def _serialize(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def test_example_artifact_regenerates_byte_for_byte() -> None:
    assert _serialize(_build_example()) == _EXAMPLE.read_text(encoding="utf-8")


def test_example_run_is_self_consistent() -> None:
    assert _serialize(_build_example()) == _serialize(_build_example())


def test_example_run_id_is_configuration_addressed() -> None:
    reference = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    assert _build_example()["metadata"]["run_id"] == reference["metadata"]["run_id"]
