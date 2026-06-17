"""Injection perturbations: add stressor items to a case.

These perturbations stress a benchmark by *adding* candidate items, never by
changing ground truth. Injected items always carry ``oracle_relevant=False`` and
are absent from ``relevant_ids``/``required_ids``, so the oracle ceiling is
unchanged and recall denominators stay fixed: any score drop comes purely from a
strategy spending budget on the injected stressors.

Three families live here:

* :class:`DistractorInjection` — on-topic-but-irrelevant competing items.
* :class:`ContradictionInjection` — on-topic items flagged ``conflicting``.
* :class:`StaleAmplification` — repeated stale / superseded items.
"""

from __future__ import annotations

import random

from context_engineering_lab.benchmarks.naturalistic.records import (
    CONFLICTING_KEY,
    CURRENT_KEY,
    HARMFUL_KEY,
    REQUIRED_KEY,
    SUPERSEDED_KEY,
)
from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.retention import FREQUENCY_KEY
from context_engineering_lab.core.temporal import SALIENCE_KEY, STALE_KEY
from context_engineering_lab.perturbations.base import (
    BasePerturbation,
    PerturbationConfig,
    PerturbationResult,
)
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

#: Filler tokens appended to injected content so distinct injected items differ.
_FILLER: tuple[str, ...] = (
    "update",
    "note",
    "thread",
    "reply",
    "summary",
    "context",
    "detail",
    "remark",
)


def _base_metadata() -> dict[str, JsonValue]:
    """Return injected-item metadata with every flag at a non-relevant default."""
    return {
        ORACLE_RELEVANCE_KEY: False,
        REQUIRED_KEY: False,
        CURRENT_KEY: False,
        CONFLICTING_KEY: False,
        SUPERSEDED_KEY: False,
        STALE_KEY: False,
        HARMFUL_KEY: False,
        SALIENCE_KEY: 0.5,
        FREQUENCY_KEY: 1,
        SOURCE_QUALITY_KEY: 0.5,
    }


def _max_timestamp(case: Case) -> float:
    stamps = [c.timestamp for c in case.candidates if c.timestamp is not None]
    return max(stamps) if stamps else 0.0


def _query_terms(case: Case, rng: random.Random) -> str:
    """Build on-topic content from the case query plus a filler token."""
    return f"{case.task.query} {rng.choice(_FILLER)}"


def _avg_length(case: Case) -> int:
    lengths = [c.length for c in case.candidates if c.length > 0]
    return round(sum(lengths) / len(lengths)) if lengths else 0


class DistractorInjection(BasePerturbation):
    """Inject on-topic-but-irrelevant items that compete for the budget.

    Injected items repeat the query terms (so content-aware selectors are
    tempted), carry a high salience and a recent timestamp (so salience- and
    recency-based selectors are tempted), but are flagged ``oracle_relevant=False``
    and excluded from ground truth.
    """

    def apply(self, case: Case, rng: random.Random) -> PerturbationResult:
        """Append ``config.count`` competing distractor items to the case."""
        base_ts = _max_timestamp(case)
        length = _avg_length(case)
        added: list[Item] = []
        for i in range(self._config.count):
            meta = _base_metadata()
            meta[SALIENCE_KEY] = round(rng.uniform(0.7, 1.0), 4)
            meta[FREQUENCY_KEY] = rng.randint(3, 8)
            added.append(
                Item(
                    id=ItemId(f"distractor-{case.case_id}-{i}"),
                    content=_query_terms(case, rng),
                    length=length,
                    timestamp=base_ts + i + 1,
                    source="injected-distractor",
                    metadata=meta,
                )
            )
        new_case = Case(
            case_id=case.case_id,
            task=case.task,
            candidates=(*case.candidates, *added),
            relevant_ids=case.relevant_ids,
            required_ids=case.required_ids,
        )
        return PerturbationResult(
            perturbation_id=self.id,
            case=new_case,
            items_added=len(added),
            items_modified=0,
        )


def distractor_injection(count: int = 6) -> DistractorInjection:
    """Return the default distractor-injection perturbation."""
    return DistractorInjection(
        PerturbationConfig(perturbation_id="distractor-injection", count=count)
    )


class ContradictionInjection(BasePerturbation):
    """Inject on-topic items that conflict with the case's current truth.

    Injected items repeat the query terms and read plausibly, but are flagged
    ``conflicting=True`` (and ``oracle_relevant=False``). They are designed to be
    kept by content-aware selectors that cannot tell a conflicting fact from the
    real one, raising ``conflict_selection_rate`` without changing ground truth.
    """

    def apply(self, case: Case, rng: random.Random) -> PerturbationResult:
        """Append ``config.count`` conflicting items to the case."""
        base_ts = _max_timestamp(case)
        length = _avg_length(case)
        added: list[Item] = []
        for i in range(self._config.count):
            meta = _base_metadata()
            meta[CONFLICTING_KEY] = True
            meta[SALIENCE_KEY] = round(rng.uniform(0.4, 0.7), 4)
            meta[FREQUENCY_KEY] = rng.randint(2, 5)
            added.append(
                Item(
                    id=ItemId(f"contradiction-{case.case_id}-{i}"),
                    content=f"{_query_terms(case, rng)} instead",
                    length=length,
                    timestamp=base_ts + i + 1,
                    source="injected-contradiction",
                    metadata=meta,
                )
            )
        new_case = Case(
            case_id=case.case_id,
            task=case.task,
            candidates=(*case.candidates, *added),
            relevant_ids=case.relevant_ids,
            required_ids=case.required_ids,
        )
        return PerturbationResult(
            perturbation_id=self.id,
            case=new_case,
            items_added=len(added),
            items_modified=0,
        )


def contradiction_injection(count: int = 4) -> ContradictionInjection:
    """Return the default contradiction-injection perturbation."""
    return ContradictionInjection(
        PerturbationConfig(perturbation_id="contradiction-injection", count=count)
    )
