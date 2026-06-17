"""Tests for Phase 9 oracle-gap analysis."""

from __future__ import annotations

import pytest

from context_engineering_lab.synthesis.aggregation import aggregate_results
from context_engineering_lab.synthesis.oracle_gap import (
    gaps_for_strategy,
    oracle_oriented_cells,
    oracle_summaries,
    oracle_summary,
)
from synthesis_helpers import simple_result


def _aggregation():  # type: ignore[no-untyped-def]
    res = simple_result(
        "selection",
        {
            "oracle": {
                "answer_support": {(1, 2): 1.0},
                "harmful_retention_rate": {(1, 2): 0.0},
            },
            "recency": {
                "answer_support": {(1, 2): 0.5},
                "harmful_retention_rate": {(1, 2): 0.3},
            },
        },
    )
    return aggregate_results([res])


def test_oracle_oriented_cells() -> None:
    agg = _aggregation()
    cells = oracle_oriented_cells(agg)
    assert cells[("selection", "answer_support", 2)] == pytest.approx(1.0)
    assert cells[("selection", "harmful_retention_rate", 2)] == pytest.approx(0.0)


def test_gaps_for_strategy() -> None:
    agg = _aggregation()
    gaps = {g.metric: g for g in gaps_for_strategy(agg, "recency")}
    assert gaps["answer_support"].gap == pytest.approx(0.5)
    assert gaps["answer_support"].oracle_value == pytest.approx(1.0)
    assert gaps["harmful_retention_rate"].gap == pytest.approx(0.3)
    assert gaps["harmful_retention_rate"].oracle_value == pytest.approx(0.0)


def test_oracle_summary_normalized() -> None:
    agg = _aggregation()
    summary = oracle_summary(agg, "recency")
    assert summary.mean_gap == pytest.approx(0.4)
    assert summary.mean_primary_gap == pytest.approx(0.5)
    assert summary.normalized == pytest.approx(0.5)
    assert summary.cell_count == 2


def test_oracle_summaries_rank_oracle_first() -> None:
    agg = _aggregation()
    summaries = oracle_summaries(agg)
    assert summaries[0].strategy_id == "oracle"
    assert summaries[0].normalized == pytest.approx(1.0)
    assert summaries[-1].strategy_id == "recency"
