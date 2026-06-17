"""Naturalistic benchmark family: ``document-revision-context``.

A question depends on the *current* version of a document, not on the older
revisions that precede it. The candidate set mixes current facts with an older
revision, deprecated facts, and old facts that directly conflict with the current
answer. Current facts read as important; superseded and conflicting facts are just
as on-topic textually but read as unimportant and old. So a keyword strategy keeps
the outdated facts, while an importance-aware policy tracks the current truth.

Deterministic from the seed; no real data, external call, or LLM.
"""

from __future__ import annotations

import random

from context_engineering_lab.benchmarks.naturalistic.records import (
    NaturalisticBenchmark,
    NaturalisticConfig,
    RevisionRecord,
    case_from_records,
    naturalistic_signal,
    query_fragment,
)
from context_engineering_lab.core.benchmark import Case

_QUERY = "api retry limit"

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "selection_precision",
    "current_truth_support",
    "superseded_fact_retention",
    "conflict_selection_rate",
    "budget_utilization",
)


class DocumentRevisionBenchmark(NaturalisticBenchmark):
    """A ``document-revision-context`` benchmark built from a config and knobs."""

    def __init__(
        self,
        config: NaturalisticConfig,
        *,
        num_current: int = 2,
        num_old: int = 3,
        num_conflicting: int = 2,
    ) -> None:
        super().__init__(config, DECLARED_METRICS)
        if num_current < 1:
            raise ValueError("num_current must be >= 1")
        if min(num_old, num_conflicting) < 0:
            raise ValueError("fact counts must be >= 0")
        self._num_current = num_current
        self._num_old = num_old
        self._num_conflicting = num_conflicting

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        records: list[RevisionRecord] = []
        for i in range(self._num_current):
            sal, freq = naturalistic_signal("current", rng)
            records.append(
                RevisionRecord(
                    record_id=f"case{case_index}-current{i}",
                    kind="current",
                    timestamp=float(rng.randint(9, 12)),
                    salience=sal,
                    frequency=freq,
                    relevant=True,
                    current=True,
                    required=i == 0,
                    revision=3,
                    body=f"current {query_fragment(_QUERY, 'full', rng)} is five",
                )
            )
        for i in range(self._num_old):
            sal, freq = naturalistic_signal("superseded", rng)
            records.append(
                RevisionRecord(
                    record_id=f"case{case_index}-old{i}",
                    kind="superseded",
                    timestamp=float(rng.randint(0, 4)),
                    salience=sal,
                    frequency=freq,
                    superseded=True,
                    revision=1,
                    body=f"deprecated {query_fragment(_QUERY, 'partial', rng)} note",
                )
            )
        for i in range(self._num_conflicting):
            sal, freq = naturalistic_signal("superseded", rng)
            records.append(
                RevisionRecord(
                    record_id=f"case{case_index}-conflict{i}",
                    kind="conflicting",
                    timestamp=float(rng.randint(0, 4)),
                    salience=sal,
                    frequency=freq,
                    superseded=True,
                    conflicting=True,
                    revision=2,
                    body=f"old {query_fragment(_QUERY, 'full', rng)} was three",
                )
            )
        return case_from_records(case_index, _QUERY, records)
