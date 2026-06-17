"""Naturalistic benchmark family: ``meeting-notes-context``.

A question depends on a decision (and its action item) buried in meeting notes,
while an earlier decision on the same topic has since been *superseded* and several
status updates and asides add noise. The current decision reads as important; the
superseded one is just as on-topic textually but reads as unimportant. So a
keyword strategy drags in the superseded decision, while an importance-aware
policy keeps the current one.

Deterministic from the seed; no real data, external call, or LLM.
"""

from __future__ import annotations

import random

from context_engineering_lab.benchmarks.naturalistic.records import (
    MeetingNoteRecord,
    NaturalisticBenchmark,
    NaturalisticConfig,
    case_from_records,
    naturalistic_signal,
    query_fragment,
)
from context_engineering_lab.core.benchmark import Case

_QUERY = "launch date decision"

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "selection_recall",
    "selection_precision",
    "current_truth_support",
    "superseded_fact_retention",
    "conflict_selection_rate",
    "budget_utilization",
)


class MeetingNotesBenchmark(NaturalisticBenchmark):
    """A ``meeting-notes-context`` benchmark built from a config and knobs."""

    def __init__(
        self,
        config: NaturalisticConfig,
        *,
        num_updates: int = 5,
        num_superseded: int = 2,
        num_irrelevant: int = 4,
    ) -> None:
        super().__init__(config, DECLARED_METRICS)
        if min(num_updates, num_superseded, num_irrelevant) < 0:
            raise ValueError("note counts must be >= 0")
        self._num_updates = num_updates
        self._num_superseded = num_superseded
        self._num_irrelevant = num_irrelevant

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        records: list[MeetingNoteRecord] = []

        sal, freq = naturalistic_signal("current", rng)
        records.append(
            MeetingNoteRecord(
                record_id=f"case{case_index}-decision",
                kind="current",
                timestamp=float(rng.randint(8, 11)),
                salience=sal,
                frequency=freq,
                relevant=True,
                current=True,
                required=True,
                label="decision",
                body=f"{query_fragment(_QUERY, 'full', rng)} is final",
            )
        )
        sal, freq = naturalistic_signal("current", rng)
        records.append(
            MeetingNoteRecord(
                record_id=f"case{case_index}-action",
                kind="current",
                timestamp=float(rng.randint(8, 11)),
                salience=sal,
                frequency=freq,
                relevant=True,
                current=True,
                label="action",
                body=f"own {query_fragment(_QUERY, 'partial', rng)} rollout",
            )
        )
        for i in range(self._num_superseded):
            sal, freq = naturalistic_signal("superseded", rng)
            records.append(
                MeetingNoteRecord(
                    record_id=f"case{case_index}-superseded{i}",
                    kind="superseded",
                    timestamp=float(rng.randint(0, 4)),
                    salience=sal,
                    frequency=freq,
                    superseded=True,
                    conflicting=True,
                    label="decision",
                    body=f"earlier {query_fragment(_QUERY, 'full', rng)} reversed",
                )
            )
        for i in range(self._num_updates):
            sal, freq = naturalistic_signal("distractor", rng)
            records.append(
                MeetingNoteRecord(
                    record_id=f"case{case_index}-update{i}",
                    kind="distractor",
                    timestamp=float(rng.randint(5, 11)),
                    salience=sal,
                    frequency=freq,
                    label="update",
                    body=query_fragment("status update progress tooling", "full", rng),
                )
            )
        for i in range(self._num_irrelevant):
            sal, freq = naturalistic_signal("distractor", rng)
            records.append(
                MeetingNoteRecord(
                    record_id=f"case{case_index}-note{i}",
                    kind="distractor",
                    timestamp=float(rng.randint(5, 11)),
                    salience=sal,
                    frequency=freq,
                    label="note",
                    body=query_fragment("coffee machine parking badges", "full", rng),
                )
            )
        return case_from_records(case_index, _QUERY, records)
