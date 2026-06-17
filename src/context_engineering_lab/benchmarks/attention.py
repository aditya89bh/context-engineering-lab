"""Controlled attention benchmark: ``attention-source-allocation``.

A synthetic benchmark for studying *how a budget should be split across competing
sources*. Each case holds several **sources**; each source mixes signal items and
distractor items, and exposes an observable per-source quality score and a
salience profile. A strategy must decide how much of the budget each source gets
*before* the (fixed, salience-ordered) inner selection fills each share. The
generator exposes the knobs that matter for the Phase 6 questions:

* source count and source size (and an optional oversized source),
* quality imbalance — how different the sources are,
* signal concentration — whether the signal sits in one source or is spread,
* a noisy dominant source — a large, high-salience, low-quality trap.

Quality is a *noisy* proxy for a source's latent signal richness, so a
quality-aware allocator is good but not perfect; salience can be inflated on the
trap source, so a salience-aware allocator can be fooled. Generation is fully
deterministic from the seed. Scoring is stateless: it checks which signal items
survived and which sources contributed. Nothing here calls an external service or
uses an LLM.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY
from context_engineering_lab.core.attention_metrics import (
    allocation_efficiency,
    signal_capture_rate,
    source_coverage,
    wasted_attention_rate,
)
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.compression_metrics import budget_utilization
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId, ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY
from context_engineering_lab.seeding import derive_seed
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

Imbalance = Literal["low", "high"]
Concentration = Literal["spread", "concentrated"]

_IMBALANCE: frozenset[str] = frozenset({"low", "high"})
_CONCENTRATION: frozenset[str] = frozenset({"spread", "concentrated"})

DECLARED_METRICS: tuple[str, ...] = (
    "allocation_efficiency",
    "signal_capture_rate",
    "wasted_attention_rate",
    "source_coverage",
    "budget_utilization",
)


@dataclass(frozen=True, slots=True)
class AttentionConfig:
    """Parameters for an ``attention-source-allocation`` preset.

    Args:
        benchmark_id: Stable identifier for the preset.
        version: Version string; bump when a change affects scores.
        construct: What capability the preset is designed to probe.
        num_cases: Number of cases generated per seed.
        num_sources: Number of competing sources per case.
        source_size: Items in each regular source.
        quality_imbalance: How different source richness/quality is (``low`` keeps
            sources similar; ``high`` spreads them across a gradient).
        signal_concentration: Whether the signal sits in one source
            (``concentrated``) or is spread across sources (``spread``).
        noisy_dominant: If ``True``, add a large, high-salience, low-quality trap
            source whose volume and salience overstate its signal.
        dominant_size_factor: Size multiplier for the trap source.
        budget_sweep: Item budgets to recommend sweeping over.
        expected_failure_modes: Human-readable notes on how strategies may fail.
    """

    benchmark_id: str
    version: str
    construct: str
    num_cases: int
    num_sources: int
    source_size: int
    quality_imbalance: Imbalance
    signal_concentration: Concentration
    noisy_dominant: bool = False
    dominant_size_factor: int = 3
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
        if self.source_size < 1:
            raise ValueError("source_size must be >= 1")
        if self.dominant_size_factor < 1:
            raise ValueError("dominant_size_factor must be >= 1")
        if self.quality_imbalance not in _IMBALANCE:
            raise ValueError(f"invalid quality_imbalance: {self.quality_imbalance!r}")
        if self.signal_concentration not in _CONCENTRATION:
            raise ValueError(
                f"invalid signal_concentration: {self.signal_concentration!r}"
            )
        if not self.budget_sweep:
            raise ValueError("budget_sweep must be non-empty")

    @property
    def total_sources(self) -> int:
        """Number of sources per case, including any trap source."""
        return self.num_sources + (1 if self.noisy_dominant else 0)


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


class AttentionBenchmark:
    """An ``attention-source-allocation`` benchmark built from a config."""

    def __init__(self, config: AttentionConfig) -> None:
        self._config = config

    @property
    def config(self) -> AttentionConfig:
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

    def _richness(self, rng: random.Random) -> list[float]:
        cfg = self._config
        n = cfg.num_sources
        if cfg.signal_concentration == "concentrated":
            base = [0.1] * n
            base[0] = 0.9
            if cfg.quality_imbalance == "high":
                for s in range(1, n):
                    base[s] = 0.05 + 0.1 * (n - s) / n
            return base
        if cfg.quality_imbalance == "low":
            return [_clip(0.55 + rng.uniform(-0.05, 0.05)) for _ in range(n)]
        return [round(_clip(0.85 - 0.6 * (s / (n - 1))), 3) for s in range(n)]

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        cfg = self._config
        richness = self._richness(rng)
        sizes = [cfg.source_size] * cfg.num_sources
        traps = [False] * cfg.num_sources
        if cfg.noisy_dominant:
            richness.append(0.08)
            sizes.append(cfg.source_size * cfg.dominant_size_factor)
            traps.append(True)

        items: list[Item] = []
        signal_ids: set[ItemId] = set()
        for source_index, (rich, size, trap) in enumerate(
            zip(richness, sizes, traps, strict=True)
        ):
            source_id = f"case{case_index}-s{source_index}"
            signal_count = min(size, round(rich * size))
            quality = round(_clip(rich + rng.uniform(-0.12, 0.12)), 3)
            for k in range(size):
                is_signal = k < signal_count
                if is_signal or trap:
                    salience = round(rng.uniform(0.7, 1.0), 3)
                else:
                    salience = round(rng.uniform(0.0, 0.3), 3)
                item_id = ItemId(f"{source_id}-i{k}")
                metadata: dict[str, JsonValue] = {
                    ORACLE_RELEVANCE_KEY: is_signal,
                    SALIENCE_KEY: salience,
                    SOURCE_QUALITY_KEY: quality,
                }
                items.append(
                    Item(
                        id=item_id,
                        content=f"{source_id} item {k}",
                        length=1,
                        source=source_id,
                        metadata=metadata,
                    )
                )
                if is_signal:
                    signal_ids.add(item_id)
        if not signal_ids:
            # Guarantee at least one signal item so metrics are defined.
            first = items[0]
            promoted = Item(
                id=first.id,
                content=first.content,
                length=first.length,
                source=first.source,
                metadata={**dict(first.metadata), ORACLE_RELEVANCE_KEY: True},
            )
            items[0] = promoted
            signal_ids.add(promoted.id)
        return Case(
            case_id=f"case{case_index}",
            task=Task(query="allocate attention across sources to capture signal"),
            candidates=tuple(items),
            relevant_ids=frozenset(signal_ids),
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
        """Score an allocated context for a single case.

        ``allocation_efficiency`` is reported as ``0.0`` for an empty context
        (its formal value is undefined; a budget of at least one item normally
        rules this out).

        Args:
            case: The case that produced the context.
            context: The allocator's output for the case.

        Returns:
            A mapping of declared metric names to values.
        """
        selected = context.item_ids
        signal = case.relevant_ids
        all_sources = {
            item.source for item in case.candidates if item.source is not None
        }
        covered = {item.source for item in context.items if item.source is not None}
        return {
            "allocation_efficiency": (
                allocation_efficiency(signal, selected) if selected else 0.0
            ),
            "signal_capture_rate": signal_capture_rate(signal, selected),
            "wasted_attention_rate": wasted_attention_rate(
                signal, selected, context.budget.limit
            ),
            "source_coverage": source_coverage(covered, all_sources),
            "budget_utilization": budget_utilization(
                context.total_cost, context.budget.limit
            ),
        }
