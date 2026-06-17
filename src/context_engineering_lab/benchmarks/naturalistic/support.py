"""Naturalistic benchmark family: ``support-ticket-context``.

A current ticket resembles several past incidents. One past incident holds the
fix that actually works; another holds a fix that is now *stale*; another holds a
*harmful* fix that makes things worse; and every incident repeats the same noisy
symptom lines. Past incidents are *sources*, each with an observable quality
score, so this family also exercises source-based allocation. The successful fix
sits in a high-quality source and reads as important; the noisy symptoms recur
often (high frequency) but carry no resolution.

Deterministic from the seed; no real data, external call, or LLM.
"""

from __future__ import annotations

import random

from context_engineering_lab.benchmarks.naturalistic.records import (
    NaturalisticBenchmark,
    NaturalisticConfig,
    TicketRecord,
    case_from_records,
    naturalistic_signal,
    query_fragment,
)
from context_engineering_lab.core.benchmark import Case

_QUERY = "login error after password reset"

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "selection_recall",
    "signal_capture_rate",
    "harmful_retention_rate",
    "stale_selection_rate",
    "budget_utilization",
)

# Each special incident: (suffix, resolution kind, source quality).
_SPECIAL = (
    ("good", "relevant", 0.85),
    ("stale", "stale", 0.50),
    ("bad", "harmful", 0.20),
)


class SupportTicketBenchmark(NaturalisticBenchmark):
    """A ``support-ticket-context`` benchmark built from a config and knobs."""

    def __init__(
        self,
        config: NaturalisticConfig,
        *,
        num_similar: int = 3,
        symptoms_per_incident: int = 2,
    ) -> None:
        super().__init__(config, DECLARED_METRICS)
        if num_similar < 0:
            raise ValueError("num_similar must be >= 0")
        if symptoms_per_incident < 0:
            raise ValueError("symptoms_per_incident must be >= 0")
        self._num_similar = num_similar
        self._symptoms = symptoms_per_incident

    def _resolution(
        self,
        case_index: int,
        suffix: str,
        kind: str,
        quality: float,
        rng: random.Random,
    ) -> TicketRecord:
        sal, freq = naturalistic_signal(kind, rng)
        incident = f"case{case_index}-INC-{suffix}"
        return TicketRecord(
            record_id=f"{incident}-fix",
            kind=kind,
            timestamp=float(rng.randint(2, 11)),
            salience=sal,
            frequency=freq,
            relevant=kind == "relevant",
            current=kind == "relevant",
            required=kind == "relevant",
            stale=kind == "stale",
            harmful=kind == "harmful",
            conflicting=kind in ("stale", "harmful"),
            source=incident,
            source_quality=quality,
            incident=incident,
            field_name="resolution",
            body=f"{query_fragment(_QUERY, 'full', rng)} resolved by step {suffix}",
        )

    def _symptoms_for(
        self, case_index: int, incident: str, quality: float, rng: random.Random
    ) -> list[TicketRecord]:
        rows: list[TicketRecord] = []
        for s in range(self._symptoms):
            sal, freq = naturalistic_signal("noisy", rng)
            rows.append(
                TicketRecord(
                    record_id=f"{incident}-symptom{s}",
                    kind="noisy",
                    timestamp=float(rng.randint(2, 11)),
                    salience=sal,
                    frequency=freq,
                    source=incident,
                    source_quality=quality,
                    incident=incident,
                    field_name="symptom",
                    body=query_fragment(_QUERY, "full", rng),
                )
            )
        return rows

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        records: list[TicketRecord] = []
        for suffix, kind, quality in _SPECIAL:
            incident = f"case{case_index}-INC-{suffix}"
            records.append(
                self._resolution(case_index, suffix, kind, quality, rng)
            )
            records.extend(self._symptoms_for(case_index, incident, quality, rng))
        for i in range(self._num_similar):
            incident = f"case{case_index}-INC-sim{i}"
            quality = round(rng.uniform(0.3, 0.5), 3)
            sal, freq = naturalistic_signal("distractor", rng)
            records.append(
                TicketRecord(
                    record_id=f"{incident}-fix",
                    kind="distractor",
                    timestamp=float(rng.randint(2, 11)),
                    salience=sal,
                    frequency=freq,
                    source=incident,
                    source_quality=quality,
                    incident=incident,
                    field_name="resolution",
                    body=query_fragment("unrelated network timeout retry", "full", rng),
                )
            )
            records.extend(self._symptoms_for(case_index, incident, quality, rng))
        return case_from_records(case_index, _QUERY, records)
