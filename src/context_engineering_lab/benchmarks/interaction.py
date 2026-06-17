"""Controlled interaction benchmark: ``interaction-context-pipeline``.

A synthetic benchmark for studying how the Phase 2-6 primitives *interact* when
chained into a pipeline. Each case is rich enough to exercise every primitive at
once. It holds items of four kinds, spread over several sources and a timeline:

* **relevant** — ground-truth signal: carries the query's keywords, is salient,
  is *corroborated* (high access frequency), and is spread across time,
* **harmful** — a trap that *looks* relevant: it carries the query's keywords and
  is salient and recent, but is rarely corroborated (low frequency) and is
  flagged harmful,
* **stale** — old, off-topic items that a temporal filter should drop,
* **distractor** — recent, off-topic filler.

The signals are deliberately misaligned so that no single primitive is enough:

* keyword selection is fooled by harmful items (they carry the query terms),
* a salience- or recency-only policy keeps harmful items (they are salient and
  recent),
* only *frequency* separates corroborated-relevant from rarely-seen-harmful, so a
  retention or frequency-aware stage is what removes the trap,
* a temporal window drops stale items but, because relevant items are spread over
  time, an aggressive window can also drop old-but-relevant ones.

This is what makes compositions interesting: one stage can remove a trap the next
stage cannot, and a stage can also discard signal a later stage needed.

Generation is fully deterministic from the seed. Scoring is stateless and id
based. Nothing here calls an external service, uses an LLM, or persists a store.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from context_engineering_lab.benchmarks.retention import HARMFUL_KEY
from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.compression_metrics import budget_utilization
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId, ItemId
from context_engineering_lab.core.interaction_metrics import pipeline_efficiency
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.metrics import (
    answer_support,
    selection_precision,
    selection_recall,
)
from context_engineering_lab.core.retention import FREQUENCY_KEY
from context_engineering_lab.core.retention_metrics import harmful_retention_rate
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY, STALE_KEY
from context_engineering_lab.core.temporal_metrics import stale_selection_rate
from context_engineering_lab.seeding import derive_seed
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

Imbalance = Literal["low", "high"]
Concentration = Literal["spread", "concentrated"]

_IMBALANCE: frozenset[str] = frozenset({"low", "high"})
_CONCENTRATION: frozenset[str] = frozenset({"spread", "concentrated"})

#: Query terms shared by every case. Relevant and (trap) harmful items embed
#: these; stale and distractor items use a disjoint vocabulary.
_QUERY = "alpha beta gamma signal"
_OFFTOPIC_TOKENS = "delta epsilon zeta omega"

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "selection_precision",
    "selection_recall",
    "harmful_retention_rate",
    "stale_selection_rate",
    "budget_utilization",
    "pipeline_efficiency",
)


@dataclass(frozen=True, slots=True)
class InteractionConfig:
    """Parameters for an ``interaction-context-pipeline`` preset.

    Args:
        benchmark_id: Stable identifier for the preset.
        version: Version string; bump when a change affects scores.
        construct: What interaction the preset is designed to probe.
        num_cases: Number of cases generated per seed.
        num_sources: Number of competing sources per case.
        num_relevant: Relevant (signal) items per case.
        num_required: Must-select subset of the relevant items.
        num_stale: Stale items per case (stale density).
        num_harmful: Harmful trap items per case (harmful density).
        num_distractor: Off-topic filler items per case.
        source_imbalance: Source-quality spread (``low`` keeps sources similar;
            ``high`` spreads them across a gradient).
        signal_concentration: Whether relevant items sit in one source
            (``concentrated``) or are spread across sources (``spread``).
        budget_sweep: Item budgets to recommend sweeping over.
        expected_failure_modes: Human-readable notes on how pipelines may fail.
    """

    benchmark_id: str
    version: str
    construct: str
    num_cases: int
    num_sources: int
    num_relevant: int
    num_required: int
    num_stale: int
    num_harmful: int
    num_distractor: int
    source_imbalance: Imbalance
    signal_concentration: Concentration
    budget_sweep: tuple[Budget, ...] = (
        Budget(4, BudgetUnit.ITEMS),
        Budget(8, BudgetUnit.ITEMS),
        Budget(12, BudgetUnit.ITEMS),
        Budget(16, BudgetUnit.ITEMS),
    )
    expected_failure_modes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.num_cases < 1:
            raise ValueError("num_cases must be >= 1")
        if self.num_sources < 2:
            raise ValueError("num_sources must be >= 2")
        if self.num_relevant < 1:
            raise ValueError("num_relevant must be >= 1")
        if not 1 <= self.num_required <= self.num_relevant:
            raise ValueError("num_required must be in [1, num_relevant]")
        if min(self.num_stale, self.num_harmful, self.num_distractor) < 0:
            raise ValueError("item counts must be >= 0")
        if self.source_imbalance not in _IMBALANCE:
            raise ValueError(f"invalid source_imbalance: {self.source_imbalance!r}")
        if self.signal_concentration not in _CONCENTRATION:
            raise ValueError(
                f"invalid signal_concentration: {self.signal_concentration!r}"
            )
        if not self.budget_sweep:
            raise ValueError("budget_sweep must be non-empty")

    @property
    def memory_size(self) -> int:
        """Total items per case across all kinds."""
        return (
            self.num_relevant
            + self.num_stale
            + self.num_harmful
            + self.num_distractor
        )


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


# Fixed integer timeline shared by every case; positions run 0 (oldest) to
# ``_TIMELINE`` (newest). It is independent of memory size so the default
# recency window covers a meaningful, stable fraction of the timeline.
_TIMELINE = 12

# Per-kind generation profile:
#   (salience_lo, salience_hi), (frequency_lo, frequency_hi), (ts_lo, ts_hi)
# where the timestamp range is in timeline positions (larger = more recent).
# Relevant items are spread from mid-timeline to now; harmful items are recent;
# stale items are the oldest tail; distractors are mid-to-recent.
_Profile = tuple[tuple[float, float], tuple[int, int], tuple[int, int]]
_KIND_PROFILE: dict[str, _Profile] = {
    "relevant": ((0.60, 0.95), (5, 9), (3, _TIMELINE)),
    "harmful": ((0.70, 1.00), (0, 2), (8, _TIMELINE)),
    "stale": ((0.00, 0.30), (1, 4), (0, 2)),
    "distractor": ((0.00, 0.35), (0, 3), (3, _TIMELINE)),
}


class InteractionBenchmark:
    """An ``interaction-context-pipeline`` benchmark built from a config."""

    def __init__(self, config: InteractionConfig) -> None:
        self._config = config

    @property
    def config(self) -> InteractionConfig:
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
        """Item budgets recommended for sweeping."""
        return self._config.budget_sweep

    def _source_quality(self, rng: random.Random) -> list[float]:
        cfg = self._config
        n = cfg.num_sources
        if cfg.source_imbalance == "low":
            return [round(_clip(0.6 + rng.uniform(-0.05, 0.05)), 3) for _ in range(n)]
        return [round(_clip(0.9 - 0.7 * (s / (n - 1))), 3) for s in range(n)]

    def _source_for(self, kind: str, ordinal: int) -> int:
        cfg = self._config
        if kind == "relevant" and cfg.signal_concentration == "concentrated":
            return 0
        return ordinal % cfg.num_sources

    def _build_item(
        self,
        case_index: int,
        kind: str,
        ordinal: int,
        source_index: int,
        quality: float,
        rng: random.Random,
    ) -> Item:
        (slo, shi), (flo, fhi), (tlo, thi) = _KIND_PROFILE[kind]
        salience = round(rng.uniform(slo, shi), 3)
        frequency = rng.randint(flo, fhi)
        timestamp = float(rng.randint(tlo, thi))
        on_topic = kind in ("relevant", "harmful")
        tokens = _QUERY if on_topic else _OFFTOPIC_TOKENS
        source_id = f"case{case_index}-s{source_index}"
        item_id = ItemId(f"case{case_index}-{kind}{ordinal}")
        metadata: dict[str, JsonValue] = {
            ORACLE_RELEVANCE_KEY: kind == "relevant",
            HARMFUL_KEY: kind == "harmful",
            STALE_KEY: kind == "stale",
            SALIENCE_KEY: salience,
            FREQUENCY_KEY: frequency,
            SOURCE_QUALITY_KEY: quality,
        }
        return Item(
            id=item_id,
            content=f"{tokens} {kind} {ordinal}",
            length=1,
            timestamp=timestamp,
            source=source_id,
            metadata=metadata,
        )

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        cfg = self._config
        quality = self._source_quality(rng)
        items: list[Item] = []
        relevant: set[ItemId] = set()
        required: set[ItemId] = set()
        counts = {
            "relevant": cfg.num_relevant,
            "harmful": cfg.num_harmful,
            "stale": cfg.num_stale,
            "distractor": cfg.num_distractor,
        }
        for kind in ("relevant", "harmful", "stale", "distractor"):
            for ordinal in range(counts[kind]):
                source_index = self._source_for(kind, ordinal)
                item = self._build_item(
                    case_index,
                    kind,
                    ordinal,
                    source_index,
                    quality[source_index],
                    rng,
                )
                items.append(item)
                if kind == "relevant":
                    relevant.add(item.id)
                    if ordinal < cfg.num_required:
                        required.add(item.id)
        items.sort(key=lambda item: str(item.id))
        return Case(
            case_id=f"case{case_index}",
            task=Task(query=_QUERY),
            candidates=tuple(items),
            relevant_ids=frozenset(relevant),
            required_ids=frozenset(required),
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
        """Score a pipeline's context for a single case.

        Empty-context convention: metrics undefined for an empty selection
        (``selection_precision``, ``stale_selection_rate``) are recorded as
        ``0.0``; a budget of at least one item normally rules this out.
        ``harmful_retention_rate`` is ``0.0`` when a case has no harmful items.

        Args:
            case: The case that produced the context.
            context: The pipeline's output for the case.

        Returns:
            A mapping of declared metric names to values.
        """
        selected = context.item_ids
        relevant = case.relevant_ids
        required = case.required_ids
        harmful = frozenset(
            item.id
            for item in case.candidates
            if bool(item.metadata.get(HARMFUL_KEY, False))
        )
        stale = frozenset(
            item.id
            for item in case.candidates
            if bool(item.metadata.get(STALE_KEY, False))
        )
        return {
            "answer_support": answer_support(required, selected),
            "selection_precision": (
                selection_precision(relevant, selected) if selected else 0.0
            ),
            "selection_recall": selection_recall(relevant, selected),
            "harmful_retention_rate": (
                harmful_retention_rate(harmful, selected) if harmful else 0.0
            ),
            "stale_selection_rate": (
                stale_selection_rate(selected, stale) if selected else 0.0
            ),
            "budget_utilization": budget_utilization(
                context.total_cost, context.budget.limit
            ),
            "pipeline_efficiency": pipeline_efficiency(
                relevant, selected, context.budget.limit
            ),
        }
