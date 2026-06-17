"""Shared engine for the naturalistic benchmarks.

Holds the lightweight record helpers, the metadata keys the scenarios set, a
deterministic observable-signal table keyed by item *kind*, query-embedding
helpers, and the :class:`NaturalisticBenchmark` base that all five families share.

The records (``MessageLikeRecord``, ``MeetingNoteRecord``, ``TicketRecord``,
``RevisionRecord``, ``MemoryRecord``) are deliberately thin: each is a readable
container that converts cleanly into a core :class:`Item` via ``to_item``. The
base class centralises generation plumbing and a single scoring routine, so a
family only has to describe how to build its cases.

Everything is deterministic from a seed. Nothing here reads real data, calls an
external service, or uses an LLM.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY
from context_engineering_lab.core.attention_metrics import signal_capture_rate
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.compression_metrics import budget_utilization
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId, ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue, Metadata
from context_engineering_lab.core.metrics import (
    answer_support,
    selection_precision,
    selection_recall,
)
from context_engineering_lab.core.naturalistic_metrics import (
    conflict_selection_rate,
    current_truth_support,
    superseded_fact_retention,
)
from context_engineering_lab.core.retention import FREQUENCY_KEY
from context_engineering_lab.core.retention_metrics import harmful_retention_rate
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY, STALE_KEY
from context_engineering_lab.core.temporal_metrics import stale_selection_rate
from context_engineering_lab.seeding import derive_seed
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

#: Metadata flag a scenario sets on items that *conflict* with the current truth.
CONFLICTING_KEY = "conflicting"

#: Metadata flag a scenario sets on items that have been *superseded* by a newer
#: decision or revision.
SUPERSEDED_KEY = "superseded"

#: Metadata flag a scenario sets on items carrying the *current* truth.
CURRENT_KEY = "current"

#: Metadata flag marking the minimal must-select subset of relevant items.
REQUIRED_KEY = "required"

#: Metadata flag a scenario sets on actively misleading (harmful) items.
HARMFUL_KEY = "harmful"

# Observable (salience, frequency) ranges per item kind. Salience is an importance
# proxy a deployable policy may read (e.g. a pinned/flagged message); frequency is
# how often the item recurs or is referenced. They are noisy proxies, not labels.
_SIGNAL: dict[str, tuple[tuple[float, float], tuple[int, int]]] = {
    "relevant": ((0.75, 1.00), (4, 8)),
    "current": ((0.75, 1.00), (4, 8)),
    "superseded": ((0.30, 0.55), (1, 3)),
    "conflicting": ((0.30, 0.60), (2, 4)),
    "stale": ((0.00, 0.25), (0, 2)),
    "harmful": ((0.00, 0.30), (0, 2)),
    "distractor": ((0.00, 0.30), (0, 3)),
    "noisy": ((0.10, 0.40), (6, 9)),
}


def naturalistic_signal(kind: str, rng: random.Random) -> tuple[float, int]:
    """Return a deterministic observable ``(salience, frequency)`` for a kind."""
    (slo, shi), (flo, fhi) = _SIGNAL[kind]
    return round(rng.uniform(slo, shi), 3), rng.randint(flo, fhi)


def query_fragment(query: str, level: str, rng: random.Random) -> str:
    """Return a fragment of the query terms at an overlap ``level``.

    ``full`` keeps every term, ``partial`` a shuffled majority, ``none`` an empty
    string, so a keyword selector ranks full-overlap items above partial ones and
    ignores off-topic text.
    """
    terms = query.split()
    if level == "full":
        return query
    if level == "none":
        return ""
    keep = max(1, (len(terms) * 2) // 3)
    chosen = sorted(rng.sample(terms, min(keep, len(terms))))
    return " ".join(chosen)


@dataclass(frozen=True, slots=True)
class _RecordBase:
    """Common fields every naturalistic record shares."""

    record_id: str
    kind: str
    timestamp: float
    salience: float
    frequency: int
    relevant: bool = False
    current: bool = False
    superseded: bool = False
    conflicting: bool = False
    harmful: bool = False
    stale: bool = False
    required: bool = False
    source: str | None = None
    source_quality: float | None = None

    def _metadata(self) -> Metadata:
        meta: dict[str, JsonValue] = {
            ORACLE_RELEVANCE_KEY: self.relevant,
            CURRENT_KEY: self.current,
            SUPERSEDED_KEY: self.superseded,
            CONFLICTING_KEY: self.conflicting,
            HARMFUL_KEY: self.harmful,
            STALE_KEY: self.stale,
            REQUIRED_KEY: self.required,
            SALIENCE_KEY: self.salience,
            FREQUENCY_KEY: self.frequency,
        }
        if self.source_quality is not None:
            meta[SOURCE_QUALITY_KEY] = self.source_quality
        return meta

    def _to_item(self, content: str) -> Item:
        return Item(
            id=ItemId(self.record_id),
            content=content,
            length=1,
            timestamp=self.timestamp,
            source=self.source,
            metadata=self._metadata(),
        )

    def to_item(self) -> Item:
        """Convert the record to a core item. Overridden by each record kind."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class MessageLikeRecord(_RecordBase):
    """An email-like message in a thread."""

    sender: str = "person"
    subject: str = "re: thread"
    body: str = ""

    def to_item(self) -> Item:
        """Convert to a core item with thread-shaped content."""
        return self._to_item(f"from {self.sender} | {self.subject} | {self.body}")


@dataclass(frozen=True, slots=True)
class MeetingNoteRecord(_RecordBase):
    """A single meeting-note line (decision, action item, update, or aside)."""

    label: str = "note"
    body: str = ""

    def to_item(self) -> Item:
        """Convert to a core item with meeting-note-shaped content."""
        return self._to_item(f"{self.label}: {self.body}")


@dataclass(frozen=True, slots=True)
class TicketRecord(_RecordBase):
    """A support-ticket entry (symptom or resolution) from a past incident."""

    incident: str = "INC-0"
    field_name: str = "note"
    body: str = ""

    def to_item(self) -> Item:
        """Convert to a core item with ticket-shaped content."""
        return self._to_item(f"{self.incident} {self.field_name}: {self.body}")


@dataclass(frozen=True, slots=True)
class RevisionRecord(_RecordBase):
    """A document-revision fact tagged with its revision number."""

    revision: int = 1
    body: str = ""

    def to_item(self) -> Item:
        """Convert to a core item with revision-shaped content."""
        return self._to_item(f"rev{self.revision}: {self.body}")


@dataclass(frozen=True, slots=True)
class MemoryRecord(_RecordBase):
    """An agent-memory-log entry."""

    body: str = ""

    def to_item(self) -> Item:
        """Convert to a core item with memory-log-shaped content."""
        return self._to_item(f"memory: {self.body}")


@dataclass(frozen=True, slots=True)
class NaturalisticConfig:
    """Common preset configuration for a naturalistic benchmark.

    Args:
        benchmark_id: Stable identifier for the preset.
        version: Version string; bump when a change affects scores.
        construct: What the preset is designed to probe.
        num_cases: Number of cases generated per seed.
        budget_sweep: Item budgets to recommend sweeping over.
        expected_failure_modes: Human-readable notes on how strategies may fail.
    """

    benchmark_id: str
    version: str
    construct: str
    num_cases: int = 24
    budget_sweep: tuple[Budget, ...] = (
        Budget(2, BudgetUnit.ITEMS),
        Budget(4, BudgetUnit.ITEMS),
        Budget(8, BudgetUnit.ITEMS),
        Budget(12, BudgetUnit.ITEMS),
    )
    expected_failure_modes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.num_cases < 1:
            raise ValueError("num_cases must be >= 1")
        if not self.budget_sweep:
            raise ValueError("budget_sweep must be non-empty")


def _ids_where(case: Case, flag: str) -> frozenset[ItemId]:
    return frozenset(
        item.id
        for item in case.candidates
        if bool(item.metadata.get(flag, False))
    )


def case_from_records(
    case_index: int, query: str, records: Sequence[_RecordBase]
) -> Case:
    """Assemble a deterministic case from naturalistic records.

    Converts each record to an item, orders them by id (stable, content-blind),
    and reads the relevant and required sets from the ground-truth flags.

    Args:
        case_index: Index used to name the case.
        query: The task query for the case.
        records: The naturalistic records that make up the case.

    Returns:
        The assembled case.
    """
    items = sorted(
        (record.to_item() for record in records),
        key=lambda item: str(item.id),
    )
    relevant = frozenset(
        item.id for item in items if bool(item.metadata.get(ORACLE_RELEVANCE_KEY))
    )
    required = frozenset(
        item.id for item in items if bool(item.metadata.get(REQUIRED_KEY))
    )
    return Case(
        case_id=f"case{case_index}",
        task=Task(query=query),
        candidates=tuple(items),
        relevant_ids=relevant,
        required_ids=required,
    )


class NaturalisticBenchmark:
    """Base for the naturalistic benchmark families.

    Subclasses implement :meth:`_build_case`; this base supplies the benchmark
    interface, deterministic generation, and a single scoring routine that reports
    only the metrics a family declares.
    """

    #: Every metric the shared scorer knows how to compute.
    _ALL_METRICS: tuple[str, ...] = (
        "answer_support",
        "selection_precision",
        "selection_recall",
        "signal_capture_rate",
        "harmful_retention_rate",
        "stale_selection_rate",
        "conflict_selection_rate",
        "superseded_fact_retention",
        "current_truth_support",
        "budget_utilization",
    )

    def __init__(
        self, config: NaturalisticConfig, declared_metrics: tuple[str, ...]
    ) -> None:
        unknown = set(declared_metrics) - set(self._ALL_METRICS)
        if unknown:
            raise ValueError(f"unknown declared metrics: {sorted(unknown)}")
        self._config = config
        self._declared = declared_metrics

    @property
    def config(self) -> NaturalisticConfig:
        """The configuration this benchmark was built from."""
        return self._config

    @property
    def id(self) -> BenchmarkId:
        """Stable identifier for the benchmark."""
        return BenchmarkId(self._config.benchmark_id)

    @property
    def version(self) -> str:
        """Version string; bump when a change affects scores."""
        return self._config.version

    @property
    def declared_metrics(self) -> tuple[str, ...]:
        """Names of the metrics this benchmark reports."""
        return self._declared

    @property
    def budget_sweep(self) -> tuple[Budget, ...]:
        """Item budgets recommended for sweeping."""
        return self._config.budget_sweep

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        raise NotImplementedError

    def generate(self, seed: int) -> Sequence[Case]:
        """Generate deterministic cases from a seed.

        Args:
            seed: Root seed; all randomness derives from it.

        Returns:
            The generated cases.
        """
        cfg = self._config
        rng = random.Random(derive_seed(seed, cfg.benchmark_id, cfg.version))
        return [self._build_case(i, rng) for i in range(cfg.num_cases)]

    def evaluate(self, case: Case, context: Context) -> Mapping[str, float]:
        """Score a strategy's context for a single case.

        Computes every metric the family declared, reusing the selection,
        retention, and temporal metrics plus the naturalistic ones. Metrics
        undefined for an empty selection (precision, stale and conflict rates) are
        recorded as ``0.0``; rates over an empty ground-truth set are ``0.0``.

        Args:
            case: The case that produced the context.
            context: The strategy's output for the case.

        Returns:
            A mapping of the declared metric names to values.
        """
        selected = context.item_ids
        relevant = case.relevant_ids
        required = case.required_ids
        harmful = _ids_where(case, HARMFUL_KEY)
        stale = _ids_where(case, STALE_KEY)
        conflicting = _ids_where(case, CONFLICTING_KEY)
        superseded = _ids_where(case, SUPERSEDED_KEY)
        current = _ids_where(case, CURRENT_KEY)
        scores: dict[str, float] = {
            "answer_support": answer_support(required, selected),
            "selection_recall": selection_recall(relevant, selected),
            "selection_precision": (
                selection_precision(relevant, selected) if selected else 0.0
            ),
            "signal_capture_rate": signal_capture_rate(relevant, selected),
            "harmful_retention_rate": (
                harmful_retention_rate(harmful, selected) if harmful else 0.0
            ),
            "stale_selection_rate": (
                stale_selection_rate(selected, stale) if selected else 0.0
            ),
            "conflict_selection_rate": (
                conflict_selection_rate(selected, conflicting) if selected else 0.0
            ),
            "superseded_fact_retention": (
                superseded_fact_retention(superseded, selected)
                if superseded
                else 0.0
            ),
            "current_truth_support": (
                current_truth_support(current, selected) if current else 0.0
            ),
            "budget_utilization": budget_utilization(
                context.total_cost, context.budget.limit
            ),
        }
        return {name: scores[name] for name in self._declared}
