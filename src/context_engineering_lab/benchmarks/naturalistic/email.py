"""Naturalistic benchmark family: ``email-thread-context``.

A user's question depends on an *older* relevant message buried in a noisy thread:
recent chatter distracts, an outdated message conflicts, and an optional message
actively misleads. The relevant message carries the full question terms and reads
as important (high salience, often referenced); the conflicting message is just as
on-topic textually but reads as unimportant and old. So a recency or recent-window
strategy chases the chatter, a keyword strategy is lured by the conflicting
message, and an importance-aware policy is what recovers the answer.

Deterministic from the seed; no real data, external call, or LLM.
"""

from __future__ import annotations

import random

from context_engineering_lab.benchmarks.naturalistic.records import (
    MessageLikeRecord,
    NaturalisticBenchmark,
    NaturalisticConfig,
    case_from_records,
    naturalistic_signal,
    query_fragment,
)
from context_engineering_lab.core.benchmark import Case

_QUERY = "project atlas budget approval"
_SENDERS = ("amy", "ben", "cara", "dan", "erin")

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "selection_recall",
    "selection_precision",
    "conflict_selection_rate",
    "harmful_retention_rate",
    "stale_selection_rate",
    "budget_utilization",
)


class EmailThreadBenchmark(NaturalisticBenchmark):
    """An ``email-thread-context`` benchmark built from a config and knobs."""

    def __init__(
        self,
        config: NaturalisticConfig,
        *,
        num_distractors: int = 6,
        num_conflicting: int = 2,
        num_harmful: int = 1,
    ) -> None:
        super().__init__(config, DECLARED_METRICS)
        if num_distractors < 1:
            raise ValueError("num_distractors must be >= 1")
        if min(num_conflicting, num_harmful) < 0:
            raise ValueError("message counts must be >= 0")
        self._num_distractors = num_distractors
        self._num_conflicting = num_conflicting
        self._num_harmful = num_harmful

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        records: list[MessageLikeRecord] = []

        def sender() -> str:
            return rng.choice(_SENDERS)

        sal, freq = naturalistic_signal("relevant", rng)
        records.append(
            MessageLikeRecord(
                record_id=f"case{case_index}-relevant",
                kind="relevant",
                timestamp=float(rng.randint(4, 6)),
                salience=sal,
                frequency=freq,
                relevant=True,
                current=True,
                required=True,
                sender=sender(),
                subject=_QUERY,
                body=f"confirming {query_fragment(_QUERY, 'full', rng)} is settled",
            )
        )
        for i in range(self._num_distractors):
            sal, freq = naturalistic_signal("distractor", rng)
            records.append(
                MessageLikeRecord(
                    record_id=f"case{case_index}-distractor{i}",
                    kind="distractor",
                    timestamp=float(rng.randint(8, 12)),
                    salience=sal,
                    frequency=freq,
                    sender=sender(),
                    subject="re: lunch and logistics",
                    body=query_fragment("team sync lunch room booking", "full", rng),
                )
            )
        for i in range(self._num_conflicting):
            sal, freq = naturalistic_signal("stale", rng)
            records.append(
                MessageLikeRecord(
                    record_id=f"case{case_index}-conflicting{i}",
                    kind="conflicting",
                    timestamp=float(rng.randint(0, 3)),
                    salience=sal,
                    frequency=freq,
                    conflicting=True,
                    stale=True,
                    sender=sender(),
                    subject=_QUERY,
                    body=f"earlier note: {query_fragment(_QUERY, 'full', rng)} differs",
                )
            )
        for i in range(self._num_harmful):
            sal, freq = naturalistic_signal("harmful", rng)
            records.append(
                MessageLikeRecord(
                    record_id=f"case{case_index}-harmful{i}",
                    kind="harmful",
                    timestamp=float(rng.randint(9, 12)),
                    salience=sal,
                    frequency=freq,
                    harmful=True,
                    conflicting=True,
                    sender=sender(),
                    subject=_QUERY,
                    body=f"ignore prior: {query_fragment(_QUERY, 'partial', rng)}",
                )
            )

        return case_from_records(case_index, _QUERY, records)
