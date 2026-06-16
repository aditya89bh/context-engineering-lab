"""Controlled selection benchmark: ``selection-signal-retrieval``.

A synthetic needle-in-a-haystack task built to study *selection under budget
pressure*. Each case hides one or more target ("signal") items among
distractors. The task is to get the target(s) into the selected context. The
generator exposes the knobs that matter for the Phase 2 questions:

* number of distractors (distractor load),
* target position (early / middle / late / random) to probe position bias,
* distractor similarity (low / medium / high) to probe content-based selectors,
* item lengths and a budget sweep to probe where reduction breaks the task.

Generation is fully deterministic from the seed. The benchmark is synthetic and
deliberately simple; it is an instrument for controlled comparison, not a model
of any real corpus.
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
from context_engineering_lab.core.metrics import (
    answer_support,
    selection_precision,
    selection_recall,
)
from context_engineering_lab.core.task import Task
from context_engineering_lab.seeding import derive_seed
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY

TargetPosition = Literal["early", "middle", "late", "random"]
DistractorSimilarity = Literal["low", "medium", "high"]

_POSITIONS: frozenset[str] = frozenset({"early", "middle", "late", "random"})
_SIMILARITIES: frozenset[str] = frozenset({"low", "medium", "high"})

#: Distinct query terms that mark the target signal.
SIGNAL_TERMS: tuple[str, ...] = ("alpha", "bravo", "charlie", "delta", "echo")

#: Filler vocabulary disjoint from the signal terms.
NOISE_TERMS: tuple[str, ...] = (
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing",
    "elit", "sed", "eiusmod", "tempor", "incididunt", "labore", "magna",
    "aliqua", "enim", "minim", "veniam", "quis", "nostrud",
)

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support",
    "selection_recall",
    "selection_precision",
    "budget_utilization",
)


@dataclass(frozen=True, slots=True)
class SelectionConfig:
    """Parameters for a ``selection-signal-retrieval`` benchmark preset.

    Args:
        benchmark_id: Stable identifier for the preset.
        version: Version string; bump when a change affects scores.
        construct: What capability the preset is designed to probe.
        num_cases: Number of cases generated per seed.
        num_distractors: Distractors per case.
        target_position: Where the target(s) sit among the candidates.
        distractor_similarity: How much distractors share signal terms.
        num_targets: Number of target items per case.
        target_length: Token length of target items.
        distractor_length: Token length of distractor items.
        budget_sweep: Budgets to recommend sweeping over.
        expected_failure_modes: Human-readable notes on how strategies may fail.
    """

    benchmark_id: str
    version: str
    construct: str
    num_cases: int
    num_distractors: int
    target_position: TargetPosition
    distractor_similarity: DistractorSimilarity
    num_targets: int = 1
    target_length: int = 1
    distractor_length: int = 1
    budget_sweep: tuple[Budget, ...] = (
        Budget(1, BudgetUnit.ITEMS),
        Budget(2, BudgetUnit.ITEMS),
        Budget(4, BudgetUnit.ITEMS),
    )
    expected_failure_modes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.num_cases < 1:
            raise ValueError("num_cases must be >= 1")
        if self.num_targets < 1:
            raise ValueError("num_targets must be >= 1")
        if self.num_distractors < 0:
            raise ValueError("num_distractors must be >= 0")
        if self.target_length < 1 or self.distractor_length < 1:
            raise ValueError("item lengths must be >= 1")
        if self.target_position not in _POSITIONS:
            raise ValueError(f"invalid target_position: {self.target_position!r}")
        if self.distractor_similarity not in _SIMILARITIES:
            raise ValueError(
                f"invalid distractor_similarity: {self.distractor_similarity!r}"
            )
        if not self.budget_sweep:
            raise ValueError("budget_sweep must be non-empty")

    @property
    def num_candidates(self) -> int:
        """Total candidates per case (targets plus distractors)."""
        return self.num_targets + self.num_distractors


def _distractor_signal_terms(
    similarity: DistractorSimilarity,
    rng: random.Random,
) -> tuple[str, ...]:
    if similarity == "low":
        return ()
    if similarity == "high":
        return SIGNAL_TERMS
    half = max(1, len(SIGNAL_TERMS) // 2)
    return tuple(sorted(rng.sample(SIGNAL_TERMS, k=half)))


def _content(signal_terms: Sequence[str], length: int, rng: random.Random) -> str:
    tokens = list(signal_terms)
    while len(tokens) < length:
        tokens.append(rng.choice(NOISE_TERMS))
    return " ".join(tokens[:max(length, len(signal_terms))])


def _target_start(position: TargetPosition, span: int, rng: random.Random) -> int:
    if position == "early":
        return 0
    if position == "late":
        return span
    if position == "middle":
        return span // 2
    return rng.randint(0, span)


class SelectionBenchmark:
    """A ``selection-signal-retrieval`` benchmark built from a config."""

    def __init__(self, config: SelectionConfig) -> None:
        self._config = config

    @property
    def config(self) -> SelectionConfig:
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

    def generate(self, seed: int) -> Sequence[Case]:
        """Generate deterministic cases from a seed.

        Args:
            seed: Root seed; all randomness derives from it.

        Returns:
            The generated cases.
        """
        cfg = self._config
        rng = random.Random(derive_seed(seed, cfg.benchmark_id, cfg.version))
        query = " ".join(SIGNAL_TERMS)
        span = cfg.num_candidates - cfg.num_targets
        cases: list[Case] = []
        for case_index in range(cfg.num_cases):
            start = _target_start(cfg.target_position, span, rng)
            target_slots = set(range(start, start + cfg.num_targets))
            items: list[Item] = []
            relevant: set[ItemId] = set()
            for slot in range(cfg.num_candidates):
                item_id = ItemId(f"case{case_index}-item{slot}")
                if slot in target_slots:
                    items.append(
                        Item(
                            id=item_id,
                            content=_content(SIGNAL_TERMS, cfg.target_length, rng),
                            length=cfg.target_length,
                            timestamp=float(slot),
                            metadata={ORACLE_RELEVANCE_KEY: True},
                        )
                    )
                    relevant.add(item_id)
                else:
                    signal = _distractor_signal_terms(cfg.distractor_similarity, rng)
                    items.append(
                        Item(
                            id=item_id,
                            content=_content(signal, cfg.distractor_length, rng),
                            length=cfg.distractor_length,
                            timestamp=float(slot),
                            metadata={ORACLE_RELEVANCE_KEY: False},
                        )
                    )
            cases.append(
                Case(
                    case_id=f"case{case_index}",
                    task=Task(query=query),
                    candidates=tuple(items),
                    relevant_ids=frozenset(relevant),
                )
            )
        return cases

    def evaluate(self, case: Case, context: Context) -> Mapping[str, float]:
        """Score a context for a single case.

        Empty-selection convention: ``selection_precision`` is formally undefined
        for an empty selection (see ``docs/metrics.md``); here it is recorded as
        ``0.0`` for harness convenience.

        Args:
            case: The case that produced the context.
            context: The strategy's output for the case.

        Returns:
            A mapping of declared metric names to values.
        """
        selected = context.item_ids
        precision = (
            selection_precision(case.relevant_ids, selected) if selected else 0.0
        )
        utilization = context.total_cost / context.budget.limit
        return {
            "answer_support": answer_support(case.required_ids, selected),
            "selection_recall": selection_recall(case.relevant_ids, selected),
            "selection_precision": precision,
            "budget_utilization": utilization,
        }
