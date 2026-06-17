"""Naturalistic benchmark family: ``memory-log-context``.

An agent's memory log accumulates entries over time: a few *useful* memories that
answer the current need, *stale* memories that no longer apply, *harmful* memories
that would mislead, and *neutral* background entries. Useful memories read as
important and recur; harmful and stale memories read as unimportant. This is the
naturalistic skin over the Phase 5 forgetting question.

Deterministic from the seed; no real data, external call, or LLM.
"""

from __future__ import annotations

import random

from context_engineering_lab.benchmarks.naturalistic.records import (
    MemoryRecord,
    NaturalisticBenchmark,
    NaturalisticConfig,
    case_from_records,
    naturalistic_signal,
    query_fragment,
)
from context_engineering_lab.core.benchmark import Case

_QUERY = "user timezone preference"

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "selection_recall",
    "selection_precision",
    "harmful_retention_rate",
    "stale_selection_rate",
    "budget_utilization",
)


class MemoryLogBenchmark(NaturalisticBenchmark):
    """A ``memory-log-context`` benchmark built from a config and knobs."""

    def __init__(
        self,
        config: NaturalisticConfig,
        *,
        num_useful: int = 3,
        num_stale: int = 4,
        num_harmful: int = 3,
        num_neutral: int = 6,
    ) -> None:
        super().__init__(config, DECLARED_METRICS)
        if num_useful < 1:
            raise ValueError("num_useful must be >= 1")
        if min(num_stale, num_harmful, num_neutral) < 0:
            raise ValueError("memory counts must be >= 0")
        self._num_useful = num_useful
        self._num_stale = num_stale
        self._num_harmful = num_harmful
        self._num_neutral = num_neutral

    def _memory(
        self,
        record_id: str,
        kind: str,
        overlap: str,
        ts: tuple[int, int],
        rng: random.Random,
        *,
        relevant: bool = False,
        required: bool = False,
        stale: bool = False,
        harmful: bool = False,
    ) -> MemoryRecord:
        sal, freq = naturalistic_signal(kind, rng)
        return MemoryRecord(
            record_id=record_id,
            kind=kind,
            timestamp=float(rng.randint(*ts)),
            salience=sal,
            frequency=freq,
            relevant=relevant,
            current=relevant,
            required=required,
            stale=stale,
            harmful=harmful,
            body=query_fragment(_QUERY, overlap, rng),
        )

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        records: list[MemoryRecord] = []
        for i in range(self._num_useful):
            records.append(
                self._memory(
                    f"case{case_index}-useful{i}",
                    "relevant",
                    "full",
                    (3, 11),
                    rng,
                    relevant=True,
                    required=i == 0,
                )
            )
        for i in range(self._num_stale):
            records.append(
                self._memory(
                    f"case{case_index}-stale{i}", "stale", "partial", (0, 3), rng,
                    stale=True,
                )
            )
        for i in range(self._num_harmful):
            records.append(
                self._memory(
                    f"case{case_index}-harmful{i}", "harmful", "partial", (6, 11),
                    rng, harmful=True,
                )
            )
        for i in range(self._num_neutral):
            records.append(
                self._memory(
                    f"case{case_index}-neutral{i}", "distractor", "none", (3, 11), rng
                )
            )
        return case_from_records(case_index, _QUERY, records)
