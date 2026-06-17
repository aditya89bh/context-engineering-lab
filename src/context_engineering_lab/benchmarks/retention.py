"""Controlled retention benchmark: ``retention-utility-preservation``.

A synthetic benchmark for studying *forgetting as a policy*. Each case is a small
"memory" of items of four kinds:

* **useful** — ground-truth relevant; should be kept,
* **stale** — once useful, now outdated; should be forgotten,
* **harmful** — actively misleading; must be forgotten,
* **neutral** — forgettable background filler.

Every item carries a timestamp, an observable access-frequency count, an
observable salience score, and ground-truth markers. Crucially the observable
signals are *not* aligned with usefulness in a trivial way: harmful items are
placed recently and recur often (high frequency), while useful items are spread
across time. A policy that forgets by age alone, or by frequency alone, therefore
retains harm — only signals that track utility (salience, or a blend) do well.

Generation is fully deterministic from the seed. Scoring is stateless: it
partitions the candidate ids by ground-truth kind and checks what survived.
Nothing here calls an external service, uses an LLM, or persists a store.
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
from context_engineering_lab.core.metrics import answer_support
from context_engineering_lab.core.retention import FREQUENCY_KEY
from context_engineering_lab.core.retention_metrics import (
    forgetting_efficiency,
    harmful_retention_rate,
    memory_budget_utilization,
    retention_precision,
    retention_recall,
    useful_retention_rate,
)
from context_engineering_lab.core.task import Task
from context_engineering_lab.core.temporal import SALIENCE_KEY, STALE_KEY
from context_engineering_lab.seeding import derive_seed
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

Noise = Literal["low", "high"]

_NOISE_LEVELS: frozenset[str] = frozenset({"low", "high"})

#: Metadata flag a benchmark sets to ``True`` on harmful items.
HARMFUL_KEY = "harmful"

#: Metadata flag marking the required (must-keep) subset of useful items.
REQUIRED_KEY = "required"

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "retention_precision",
    "retention_recall",
    "useful_retention_rate",
    "harmful_retention_rate",
    "memory_budget_utilization",
    "forgetting_efficiency",
)


@dataclass(frozen=True, slots=True)
class RetentionConfig:
    """Parameters for a ``retention-utility-preservation`` preset.

    Args:
        benchmark_id: Stable identifier for the preset.
        version: Version string; bump when a change affects scores.
        construct: What capability the preset is designed to probe.
        num_cases: Number of cases generated per seed.
        num_useful: Useful items per case (the signal).
        num_required: Must-keep subset of the useful items.
        num_stale: Stale items per case (stale-information density).
        num_harmful: Harmful items per case (harmful-information density).
        num_neutral: Neutral filler items per case (memory growth).
        noise: Utility-distribution clarity. ``low`` separates useful from
            harmful by salience; ``high`` overlaps them.
        budget_sweep: Retention budgets (in items) to recommend sweeping over.
        expected_failure_modes: Human-readable notes on how policies may fail.
    """

    benchmark_id: str
    version: str
    construct: str
    num_cases: int
    num_useful: int
    num_required: int
    num_stale: int
    num_harmful: int
    num_neutral: int
    noise: Noise
    budget_sweep: tuple[Budget, ...] = (
        Budget(2, BudgetUnit.ITEMS),
        Budget(4, BudgetUnit.ITEMS),
        Budget(8, BudgetUnit.ITEMS),
        Budget(16, BudgetUnit.ITEMS),
    )
    expected_failure_modes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.num_cases < 1:
            raise ValueError("num_cases must be >= 1")
        if self.num_useful < 1:
            raise ValueError("num_useful must be >= 1")
        if not 1 <= self.num_required <= self.num_useful:
            raise ValueError("num_required must be in [1, num_useful]")
        if min(self.num_stale, self.num_harmful, self.num_neutral) < 0:
            raise ValueError("item counts must be >= 0")
        if self.noise not in _NOISE_LEVELS:
            raise ValueError(f"invalid noise: {self.noise!r}")
        if not self.budget_sweep:
            raise ValueError("budget_sweep must be non-empty")

    @property
    def memory_size(self) -> int:
        """Total items per case across all kinds."""
        return self.num_useful + self.num_stale + self.num_harmful + self.num_neutral


def _spread_indices(span: int, count: int) -> list[int]:
    """Return ``count`` evenly spread distinct indices in ``range(span)``."""
    if count <= 0:
        return []
    if count >= span:
        return list(range(span))
    if count == 1:
        return [span // 2]
    step = (span - 1) / (count - 1)
    return sorted({round(i * step) for i in range(count)})


def _salience_frequency(
    kind: str, noise: Noise, rng: random.Random
) -> tuple[float, int]:
    """Return an observable (salience, frequency) for an item of a given kind."""
    if noise == "low":
        table = {
            "useful": ((0.70, 1.00), (5, 9)),
            "harmful": ((0.00, 0.30), (6, 10)),
            "stale": ((0.30, 0.60), (0, 3)),
            "neutral": ((0.00, 0.30), (0, 3)),
        }
    else:
        table = {
            "useful": ((0.45, 0.95), (3, 9)),
            "harmful": ((0.30, 0.80), (5, 10)),
            "stale": ((0.30, 0.70), (1, 5)),
            "neutral": ((0.10, 0.50), (0, 4)),
        }
    (lo, hi), (flo, fhi) = table[kind]
    return round(rng.uniform(lo, hi), 3), rng.randint(flo, fhi)


class RetentionBenchmark:
    """A ``retention-utility-preservation`` benchmark built from a config."""

    def __init__(self, config: RetentionConfig) -> None:
        self._config = config

    @property
    def config(self) -> RetentionConfig:
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
        """Retention budgets recommended for sweeping."""
        return self._config.budget_sweep

    def _kind_positions(self) -> dict[str, list[int]]:
        cfg = self._config
        n = cfg.memory_size
        stale_pos = list(range(cfg.num_stale))
        harmful_pos = list(range(n - cfg.num_harmful, n))
        middle = list(range(cfg.num_stale, n - cfg.num_harmful))
        useful_idx = set(_spread_indices(len(middle), cfg.num_useful))
        useful_pos = [middle[i] for i in sorted(useful_idx)]
        neutral_pos = [middle[i] for i in range(len(middle)) if i not in useful_idx]
        return {
            "useful": useful_pos,
            "stale": stale_pos,
            "harmful": harmful_pos,
            "neutral": neutral_pos,
        }

    def _build_case(self, case_index: int, rng: random.Random) -> Case:
        cfg = self._config
        positions = self._kind_positions()
        items: list[Item] = []
        useful: set[ItemId] = set()
        required: set[ItemId] = set()
        useful_seen = 0
        for kind in ("useful", "stale", "harmful", "neutral"):
            for slot, pos in enumerate(positions[kind]):
                item_id = ItemId(f"case{case_index}-{kind}{slot}")
                salience, frequency = _salience_frequency(kind, cfg.noise, rng)
                is_useful = kind == "useful"
                is_required = is_useful and useful_seen < cfg.num_required
                metadata: dict[str, JsonValue] = {
                    ORACLE_RELEVANCE_KEY: is_useful,
                    HARMFUL_KEY: kind == "harmful",
                    STALE_KEY: kind == "stale",
                    REQUIRED_KEY: is_required,
                    SALIENCE_KEY: salience,
                    FREQUENCY_KEY: frequency,
                }
                items.append(
                    Item(
                        id=item_id,
                        content=f"{kind} memory item",
                        length=1,
                        timestamp=float(pos),
                        metadata=metadata,
                    )
                )
                if is_useful:
                    useful.add(item_id)
                    useful_seen += 1
                if is_required:
                    required.add(item_id)
        items.sort(key=lambda item: item.timestamp or 0.0)
        return Case(
            case_id=f"case{case_index}",
            task=Task(query="retain useful information, discard harmful and stale"),
            candidates=tuple(items),
            relevant_ids=frozenset(useful),
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
        """Score a retained context for a single case.

        Empty-retention convention: metrics undefined for an empty retention
        (precision; see ``docs/metrics.md``) are recorded as harness-convenient
        sentinels. A budget of at least one item normally rules this out.
        ``harmful_retention_rate`` is recorded as ``0.0`` when a case has no
        harmful items.

        Args:
            case: The case that produced the context.
            context: The policy's retained output for the case.

        Returns:
            A mapping of declared metric names to values.
        """
        retained = context.item_ids
        useful = case.relevant_ids
        required = case.required_ids
        harmful = frozenset(
            item.id
            for item in case.candidates
            if bool(item.metadata.get(HARMFUL_KEY, False))
        )
        utilization = memory_budget_utilization(
            context.total_cost, context.budget.limit
        )
        if not retained:
            return {
                "answer_support": answer_support(required, retained),
                "retention_precision": 0.0,
                "retention_recall": retention_recall(required, retained),
                "useful_retention_rate": useful_retention_rate(useful, retained),
                "harmful_retention_rate": (
                    harmful_retention_rate(harmful, retained) if harmful else 0.0
                ),
                "memory_budget_utilization": utilization,
                "forgetting_efficiency": forgetting_efficiency(
                    useful, harmful, retained
                ),
            }
        return {
            "answer_support": answer_support(required, retained),
            "retention_precision": retention_precision(useful, retained),
            "retention_recall": retention_recall(required, retained),
            "useful_retention_rate": useful_retention_rate(useful, retained),
            "harmful_retention_rate": (
                harmful_retention_rate(harmful, retained) if harmful else 0.0
            ),
            "memory_budget_utilization": utilization,
            "forgetting_efficiency": forgetting_efficiency(useful, harmful, retained),
        }
