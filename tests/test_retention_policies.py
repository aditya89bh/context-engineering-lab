"""Tests for the deterministic retention policies."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.retention import FREQUENCY_KEY
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY
from context_engineering_lab.retention import (
    FrequencyRetentionPolicy,
    HybridRetentionPolicy,
    OracleRetentionPolicy,
    RecencyRetentionPolicy,
    RetainAllPolicy,
    SalienceRetentionPolicy,
    default_policies,
)
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

TASK = Task(query="retain useful")
BUDGET = Budget(2, BudgetUnit.ITEMS)


def _item(
    name: str, *, salience: float, freq: int, ts: float, useful: bool
) -> Item:
    meta: dict[str, JsonValue] = {
        SALIENCE_KEY: salience,
        FREQUENCY_KEY: freq,
        ORACLE_RELEVANCE_KEY: useful,
    }
    return Item(id=ItemId(name), content=name, length=1, timestamp=ts, metadata=meta)


def _memory() -> tuple[Item, ...]:
    return (
        _item("A", salience=0.9, freq=1, ts=0.0, useful=True),
        _item("B", salience=0.1, freq=9, ts=5.0, useful=False),
        _item("C", salience=0.5, freq=5, ts=2.0, useful=False),
        _item("D", salience=0.8, freq=2, ts=9.0, useful=True),
    )


def _retained(policy: object) -> set[str]:
    result = policy.retain(_memory(), TASK, BUDGET)  # type: ignore[attr-defined]
    return {str(i) for i in result.context.item_ids}


def test_retain_all_keeps_everything_over_budget() -> None:
    result = RetainAllPolicy().retain(_memory(), TASK, BUDGET)
    assert len(result.context.items) == 4
    assert result.context.total_cost > BUDGET.limit
    assert result.context.allow_overflow is True


def test_recency_keeps_newest() -> None:
    assert _retained(RecencyRetentionPolicy()) == {"D", "B"}


def test_frequency_keeps_most_frequent() -> None:
    assert _retained(FrequencyRetentionPolicy()) == {"B", "C"}


def test_salience_keeps_most_salient() -> None:
    assert _retained(SalienceRetentionPolicy()) == {"A", "D"}


def test_oracle_keeps_useful_first() -> None:
    assert _retained(OracleRetentionPolicy()) == {"A", "D"}


def test_policies_respect_budget() -> None:
    for policy in default_policies():
        if isinstance(policy, RetainAllPolicy):
            continue
        result = policy.retain(_memory(), TASK, BUDGET)
        assert len(result.context.items) <= BUDGET.limit
        assert result.context.total_cost <= BUDGET.limit


def test_policies_are_deterministic() -> None:
    for policy in default_policies():
        first = policy.retain(_memory(), TASK, BUDGET).context.item_ids
        second = policy.retain(_memory(), TASK, BUDGET).context.item_ids
        assert first == second


def test_decisions_cover_all_items() -> None:
    for policy in default_policies():
        result = policy.retain(_memory(), TASK, BUDGET)
        assert {str(d.item_id) for d in result.decisions} == {"A", "B", "C", "D"}


def test_hybrid_rejects_bad_weights() -> None:
    with pytest.raises(ValueError):
        HybridRetentionPolicy(weights=(-1.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        HybridRetentionPolicy(weights=(0.0, 0.0, 0.0))


def test_hybrid_id_encodes_weights() -> None:
    assert str(HybridRetentionPolicy().id) == "hybrid-retention-0.5-0.3-0.2"


def test_hybrid_blends_signals() -> None:
    # With pure salience weighting, hybrid reduces to the salience policy.
    pure_salience = HybridRetentionPolicy(weights=(1.0, 0.0, 0.0))
    assert _retained(pure_salience) == {"A", "D"}
    # With pure frequency weighting, it reduces to the frequency policy.
    pure_freq = HybridRetentionPolicy(weights=(0.0, 1.0, 0.0))
    assert _retained(pure_freq) == {"B", "C"}
