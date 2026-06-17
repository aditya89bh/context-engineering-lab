"""Tests for Phase 9 loading, collection, and aggregation."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_engineering_lab.reporting.persistence import write_result
from context_engineering_lab.synthesis.aggregation import (
    Direction,
    aggregate_results,
    direction,
    is_quality_metric,
    primary_metric,
)
from context_engineering_lab.synthesis.collection import (
    benchmarks_in,
    discover_artifacts,
    group_by_benchmark,
    group_by_strategy,
    load_collection,
    strategies_in,
)
from context_engineering_lab.synthesis.loading import (
    ArtifactError,
    load_artifact,
    validate_artifact_schema,
)
from tests.synthesis_helpers import metric, result, run, simple_result


def test_load_artifact_round_trips(tmp_path: Path) -> None:
    res = simple_result("selection", {"recency": {"answer_support": {(1, 2): 0.5}}})
    path = write_result(res, tmp_path / "r.json")
    assert load_artifact(path) == res


def test_load_artifact_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ArtifactError):
        load_artifact(tmp_path / "nope.json")


def test_load_artifact_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ArtifactError):
        load_artifact(bad)


def test_validate_rejects_missing_keys() -> None:
    with pytest.raises(ArtifactError):
        validate_artifact_schema({"metadata": {}})
    with pytest.raises(ArtifactError):
        validate_artifact_schema(["not", "a", "mapping"])


def test_discover_artifacts_is_sorted_and_recursive(tmp_path: Path) -> None:
    write_result(simple_result("b", {"s": {"answer_support": {(1, 2): 1.0}}}),
                 tmp_path / "z.json")
    nested = tmp_path / "sub"
    write_result(simple_result("b", {"s": {"answer_support": {(1, 2): 1.0}}}),
                 nested / "a.json")
    found = discover_artifacts(tmp_path)
    assert [p.name for p in found] == ["z.json", "a.json"] or [
        p.name for p in found
    ] == sorted(p.name for p in found)
    assert len(found) == 2


def test_discover_missing_dir() -> None:
    with pytest.raises(ArtifactError):
        discover_artifacts("/no/such/dir/here")


def test_load_collection_and_groupers(tmp_path: Path) -> None:
    write_result(
        simple_result("selection", {"recency": {"answer_support": {(1, 2): 0.4}}}),
        tmp_path / "selection.json",
    )
    write_result(
        simple_result("temporal", {"oracle": {"answer_support": {(1, 2): 1.0}}}),
        tmp_path / "temporal.json",
    )
    results = load_collection(tmp_path)
    assert benchmarks_in(results) == ["selection", "temporal"]
    assert strategies_in(results) == ["oracle", "recency"]
    by_bench = group_by_benchmark(results)
    assert set(by_bench) == {"selection", "temporal"}
    by_strategy = group_by_strategy(results)
    assert by_strategy["recency"][0][0] == "selection"


def test_load_collection_skips_invalid(tmp_path: Path) -> None:
    (tmp_path / "junk.json").write_text("{}", encoding="utf-8")
    write_result(
        simple_result("selection", {"recency": {"answer_support": {(1, 2): 0.4}}}),
        tmp_path / "ok.json",
    )
    assert load_collection(tmp_path, skip_invalid=True)
    with pytest.raises(ArtifactError):
        load_collection(tmp_path, skip_invalid=False)


def test_metric_direction_and_quality() -> None:
    assert direction("answer_support") is Direction.HIGHER_IS_BETTER
    assert direction("harmful_retention_rate") is Direction.LOWER_IS_BETTER
    assert direction("budget_utilization") is Direction.NEUTRAL
    assert direction("unknown_metric") is Direction.NEUTRAL
    assert is_quality_metric("answer_support")
    assert not is_quality_metric("budget_utilization")


def test_primary_metric_priority() -> None:
    assert primary_metric(["budget_utilization", "answer_support"]) == "answer_support"
    assert primary_metric(["signal_capture_rate", "budget_utilization"]) == (
        "signal_capture_rate"
    )
    assert primary_metric(["budget_utilization"]) is None


def test_aggregate_means_over_seeds() -> None:
    res = result(
        "selection",
        [
            run(
                "recency",
                [
                    metric("answer_support", 0.2, 1, 2),
                    metric("answer_support", 0.4, 2, 2),
                    metric("answer_support", 0.6, 3, 2),
                    metric("answer_support", 1.0, 1, 4),
                ],
            )
        ],
        seeds=(1, 2, 3),
        budget_limits=(2, 4),
    )
    agg = aggregate_results([res])
    cell = agg.get("selection", "recency", "answer_support", 2)
    assert cell is not None
    assert cell.mean == pytest.approx(0.4)
    assert cell.seed_count == 3
    assert cell.stddev > 0
    assert agg.mean_over_budgets("selection", "recency", "answer_support") == (
        pytest.approx((0.4 + 1.0) / 2)
    )


def test_aggregate_merges_duplicate_keys() -> None:
    a = simple_result("b", {"s": {"answer_support": {(1, 2): 0.0}}})
    b = simple_result("b", {"s": {"answer_support": {(2, 2): 1.0}}})
    agg = aggregate_results([a, b])
    cell = agg.get("b", "s", "answer_support", 2)
    assert cell is not None
    assert cell.seed_count == 2
    assert cell.mean == pytest.approx(0.5)


def test_aggregation_views() -> None:
    agg = aggregate_results(
        [simple_result("selection", {"recency": {"answer_support": {(1, 2): 0.5}}})]
    )
    assert agg.benchmarks() == ["selection"]
    assert agg.strategies() == ["recency"]
    sa = agg.strategy_aggregate("recency")
    assert sa.benchmarks() == ["selection"]
    ba = agg.benchmark_aggregate("selection")
    assert ba.primary_metric() == "answer_support"
    assert ba.version == "1.0"
