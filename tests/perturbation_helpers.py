"""Shared fixtures for Phase 10 perturbation tests.

Builds a small synthetic :class:`~context_engineering_lab.core.benchmark.Case`
whose items carry the full set of observable signals and ground-truth flags the
perturbations read or preserve.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.naturalistic.records import (
    CURRENT_KEY,
    HARMFUL_KEY,
    SUPERSEDED_KEY,
)
from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.retention import FREQUENCY_KEY
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY, STALE_KEY
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY


def _meta(**overrides: JsonValue) -> dict[str, JsonValue]:
    base: dict[str, JsonValue] = {
        ORACLE_RELEVANCE_KEY: False,
        CURRENT_KEY: False,
        SUPERSEDED_KEY: False,
        STALE_KEY: False,
        HARMFUL_KEY: False,
        SALIENCE_KEY: 0.5,
        FREQUENCY_KEY: 2,
        SOURCE_QUALITY_KEY: 0.5,
    }
    base.update(overrides)
    return base


def sample_case(case_id: str = "case-0") -> Case:
    """Return a case with one relevant, one stale, and one harmful item."""
    relevant = Item(
        id=ItemId("rel"),
        content="deploy rollback procedure alpha",
        length=10,
        timestamp=100.0,
        source="wiki",
        metadata=_meta(
            **{
                ORACLE_RELEVANCE_KEY: True,
                CURRENT_KEY: True,
                SALIENCE_KEY: 0.9,
                FREQUENCY_KEY: 6,
                SOURCE_QUALITY_KEY: 0.9,
            }
        ),
    )
    stale = Item(
        id=ItemId("old"),
        content="deploy rollback procedure legacy",
        length=10,
        timestamp=10.0,
        source="chat",
        metadata=_meta(
            **{
                STALE_KEY: True,
                SUPERSEDED_KEY: True,
                SALIENCE_KEY: 0.2,
                SOURCE_QUALITY_KEY: 0.3,
            }
        ),
    )
    harmful = Item(
        id=ItemId("bad"),
        content="deploy rollback procedure dangerous",
        length=10,
        timestamp=50.0,
        source="chat",
        metadata=_meta(**{HARMFUL_KEY: True, SOURCE_QUALITY_KEY: 0.4}),
    )
    return Case(
        case_id=case_id,
        task=Task(query="deploy rollback procedure"),
        candidates=(relevant, stale, harmful),
        relevant_ids=frozenset({ItemId("rel")}),
        required_ids=frozenset({ItemId("rel")}),
    )
