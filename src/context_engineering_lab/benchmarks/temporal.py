"""Controlled temporal benchmark: ``temporal-context-relevance``.

A synthetic task built to study *how time shapes what context is worth keeping*.
Each case lays items along a timeline (position ``0`` oldest, position ``L-1``
the "now"). Some items are ground-truth relevant, some are *stale* (old and no
longer relevant), and the rest are distractors or filler. The task is to get the
relevant items into a budget-limited context.

The generator exposes the knobs that matter for the Phase 4 questions:

* *relevant age* (recent / mixed / old): where in time the signal sits;
* *distractor age* (recent / mixed / old): where the noise sits;
* *temporal drift* (none / gradual / abrupt): how far an *observable* salience
  signal is pulled away from the true relevant items (modeling recent "decoys");
* *sequence length* and a budget sweep.

Items also carry an observable ``salience`` signal (a noisy proxy for relevance
that deployable strategies may read) so that age-aware weighting has something to
weight. Generation is fully deterministic from the seed. The benchmark is
synthetic and deliberately simple: an instrument for controlled comparison, not a
model of any real temporal corpus.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId, ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.metrics import (
    answer_support,
    selection_precision,
    selection_recall,
)
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY, STALE_KEY, age
from context_engineering_lab.core.temporal_metrics import (
    age_of_selected_context,
    relevant_age_gap,
    stale_selection_rate,
    temporal_relevance,
)
from context_engineering_lab.seeding import derive_seed
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

AgeBand = Literal["recent", "mixed", "old"]
Drift = Literal["none", "gradual", "abrupt"]

_BANDS: frozenset[str] = frozenset({"recent", "mixed", "old"})
_DRIFTS: frozenset[str] = frozenset({"none", "gradual", "abrupt"})

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "selection_recall",
    "selection_precision",
    "budget_utilization",
    "temporal_relevance",
    "stale_selection_rate",
    "age_of_selected_context",
    "relevant_age_gap",
)


@dataclass(frozen=True, slots=True)
class TemporalConfig:
    """Parameters for a ``temporal-context-relevance`` benchmark preset.

    Args:
        benchmark_id: Stable identifier for the preset.
        version: Version string; bump when a change affects scores.
        construct: What capability the preset is designed to probe.
        num_cases: Number of cases generated per seed.
        sequence_length: Number of timeline positions (and items) per case.
        num_relevant: Ground-truth relevant items per case.
        num_distractors: Recent/mixed distractor items per case.
        num_stale: Old, no-longer-relevant items per case.
        relevant_age: Where the relevant items sit in time.
        distractor_age: Where the distractors sit in time.
        drift: How far observable salience is pulled toward recent decoys.
        budget_sweep: Budgets (in items) to recommend sweeping over.
        expected_failure_modes: Human-readable notes on how strategies may fail.
    """

    benchmark_id: str
    version: str
    construct: str
    num_cases: int
    sequence_length: int
    num_relevant: int
    num_distractors: int
    num_stale: int
    relevant_age: AgeBand
    distractor_age: AgeBand
    drift: Drift
    budget_sweep: tuple[Budget, ...] = (
        Budget(1, BudgetUnit.ITEMS),
        Budget(2, BudgetUnit.ITEMS),
        Budget(4, BudgetUnit.ITEMS),
        Budget(8, BudgetUnit.ITEMS),
    )
    expected_failure_modes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.num_cases < 1:
            raise ValueError("num_cases must be >= 1")
        if self.sequence_length < 2:
            raise ValueError("sequence_length must be >= 2")
        if self.num_relevant < 1:
            raise ValueError("num_relevant must be >= 1")
        if self.num_distractors < 0 or self.num_stale < 0:
            raise ValueError("num_distractors and num_stale must be >= 0")
        occupied = self.num_relevant + self.num_distractors + self.num_stale
        if occupied > self.sequence_length:
            raise ValueError(
                "relevant + distractors + stale exceed sequence_length "
                f"({occupied} > {self.sequence_length})"
            )
        if self.relevant_age not in _BANDS:
            raise ValueError(f"invalid relevant_age: {self.relevant_age!r}")
        if self.distractor_age not in _BANDS:
            raise ValueError(f"invalid distractor_age: {self.distractor_age!r}")
        if self.drift not in _DRIFTS:
            raise ValueError(f"invalid drift: {self.drift!r}")
        if not self.budget_sweep:
            raise ValueError("budget_sweep must be non-empty")


def _band_positions(band: AgeBand, count: int, length: int) -> list[int]:
    """Return desired timeline positions for ``count`` items in a band."""
    if count <= 0:
        return []
    if band == "recent":
        return list(range(length - count, length))
    if band == "old":
        return list(range(count))
    if count == 1:
        return [(length - 1) // 2]
    step = (length - 1) / (count - 1)
    return [round(i * step) for i in range(count)]


def _assign_nearest(free: set[int], desired: Sequence[int]) -> list[int]:
    """Assign each desired position to the nearest still-free slot."""
    chosen: list[int] = []
    for target in desired:
        slot = min(free, key=lambda pos: (abs(pos - target), pos))
        free.remove(slot)
        chosen.append(slot)
    return chosen


def _decay_salience(rng: random.Random) -> float:
    return round(rng.uniform(0.05, 0.25), 3)


def _relevant_salience(rng: random.Random) -> float:
    return round(rng.choice((1.0, 1.0, 1.0, 0.6)), 3)


def _decoy_salience(drift: Drift, rng: random.Random) -> float:
    if drift == "gradual":
        return round(rng.uniform(0.5, 0.7), 3)
    return round(rng.uniform(0.9, 1.0), 3)  # abrupt


class TemporalBenchmark:
    """A ``temporal-context-relevance`` benchmark built from a config."""

    def __init__(self, config: TemporalConfig) -> None:
        self._config = config

    @property
    def config(self) -> TemporalConfig:
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
        return DECLARED_METRICS

    @property
    def budget_sweep(self) -> tuple[Budget, ...]:
        """Budgets recommended for sweeping."""
        return self._config.budget_sweep

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        cfg = self._config
        length = cfg.sequence_length
        free = set(range(length))
        relevant_want = _band_positions(cfg.relevant_age, cfg.num_relevant, length)
        stale_want = _band_positions("old", cfg.num_stale, length)
        distractor_want = _band_positions(
            cfg.distractor_age, cfg.num_distractors, length
        )
        relevant_pos = set(_assign_nearest(free, relevant_want))
        stale_pos = set(_assign_nearest(free, stale_want))
        distractor_pos = set(_assign_nearest(free, distractor_want))

        kinds: dict[int, str] = {}
        for pos in range(length):
            if pos in relevant_pos:
                kinds[pos] = "relevant"
            elif pos in stale_pos:
                kinds[pos] = "stale"
            elif pos in distractor_pos:
                kinds[pos] = "distractor"
            else:
                kinds[pos] = "filler"

        decoy_pos: set[int] = set()
        if cfg.drift != "none":
            non_relevant = sorted(
                (p for p in range(length) if kinds[p] != "relevant"), reverse=True
            )
            decoy_pos = set(non_relevant[: cfg.num_relevant])

        items: list[Item] = []
        relevant: set[ItemId] = set()
        for pos in range(length):
            item_id = ItemId(f"case{case_index}-item{pos}")
            kind = kinds[pos]
            is_relevant = kind == "relevant"
            if is_relevant:
                salience = _relevant_salience(rng)
            elif pos in decoy_pos:
                salience = _decoy_salience(cfg.drift, rng)
            else:
                salience = _decay_salience(rng)
            metadata: dict[str, JsonValue] = {
                ORACLE_RELEVANCE_KEY: is_relevant,
                SALIENCE_KEY: salience,
                STALE_KEY: kind == "stale",
            }
            items.append(
                Item(
                    id=item_id,
                    content=f"{kind} event at t={pos}",
                    length=1,
                    timestamp=float(pos),
                    metadata=metadata,
                )
            )
            if is_relevant:
                relevant.add(item_id)
        return Case(
            case_id=f"case{case_index}",
            task=Task(query="retrieve the temporally relevant context"),
            candidates=tuple(items),
            relevant_ids=frozenset(relevant),
        )

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
        """Score a context for a single case.

        Empty-selection convention: metrics that are formally undefined for an
        empty selection (precision and the temporal metrics; see
        ``docs/metrics.md``) are recorded with harness-convenient sentinels —
        ``0.0`` except ``relevant_age_gap``, which is recorded as ``1.0`` (maximal
        misalignment). A budget of at least one item normally rules this out.

        Args:
            case: The case that produced the context.
            context: The strategy's output for the case.

        Returns:
            A mapping of declared metric names to values.
        """
        now = float(self._config.sequence_length - 1)
        span = now
        selected = context.item_ids
        utilization = context.total_cost / context.budget.limit
        recall = selection_recall(case.relevant_ids, selected)
        support = answer_support(case.required_ids, selected)

        stale_ids = frozenset(
            item.id
            for item in case.candidates
            if bool(item.metadata.get(STALE_KEY, False))
        )
        relevant_ages = [
            age(item.timestamp, now)
            for item in case.candidates
            if item.id in case.relevant_ids and item.timestamp is not None
        ]
        selected_ages = [
            age(item.timestamp, now)
            for item in context.items
            if item.timestamp is not None
        ]

        if not selected or not selected_ages:
            return {
                "answer_support": support,
                "selection_recall": recall,
                "selection_precision": 0.0,
                "budget_utilization": utilization,
                "temporal_relevance": 0.0,
                "stale_selection_rate": 0.0,
                "age_of_selected_context": 0.0,
                "relevant_age_gap": 1.0,
            }

        return {
            "answer_support": support,
            "selection_recall": recall,
            "selection_precision": selection_precision(case.relevant_ids, selected),
            "budget_utilization": utilization,
            "temporal_relevance": temporal_relevance(
                selected_ages, min(relevant_ages), max(relevant_ages)
            ),
            "stale_selection_rate": stale_selection_rate(selected, stale_ids),
            "age_of_selected_context": age_of_selected_context(selected_ages, span),
            "relevant_age_gap": relevant_age_gap(selected_ages, relevant_ages, span),
        }
