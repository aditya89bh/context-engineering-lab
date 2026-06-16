"""Controlled compression benchmark: ``compression-fact-preservation``.

A synthetic benchmark for studying *compression under budget pressure*. Each case
is a single document whose content embeds task-relevant **facts** (required and
optional target facts) among **distractor** facts and filler words. A compressor
must shorten the document to a token budget while keeping the required facts. The
generator exposes the knobs that matter for the Phase 3 questions:

* target fact position (early / middle / late / distributed) to probe whether
  position-blind compressors succeed only by luck,
* distractor density to probe whether compression discards or launders noise,
* content length and a budget sweep to trace the compression-quality frontier.

Generation is fully deterministic from the seed. Facts are embedded as
recognizable tokens (see ``benchmarks/facts.py``) so scoring is stateless: it
scans the compressed text for surviving fact tokens. Nothing here calls an
external service or uses LLM summarization.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from context_engineering_lab.benchmarks import facts
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.compression_metrics import (
    answer_support_after_compression,
    budget_utilization,
    compression_ratio,
    distractor_retention,
    information_retention,
)
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId, ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task
from context_engineering_lab.seeding import derive_seed

TargetPosition = Literal["early", "middle", "late", "distributed"]

_POSITIONS: frozenset[str] = frozenset({"early", "middle", "late", "distributed"})

#: Filler vocabulary; chosen to never collide with fact-token markers.
NOISE_TERMS: tuple[str, ...] = (
    "lorem", "ipsum", "dolor", "amet", "consectetur", "adipiscing", "elit",
    "tempor", "incididunt", "labore", "magna", "aliqua", "veniam", "quis",
    "nostrud", "ullamco", "laboris", "aliquip", "commodo", "consequat",
)

DECLARED_METRICS: tuple[str, ...] = (
    "answer_support_after_compression",
    "budget_utilization",
    "compression_ratio",
    "distractor_retention",
    "information_retention",
)


@dataclass(frozen=True, slots=True)
class CompressionConfig:
    """Parameters for a ``compression-fact-preservation`` preset.

    Args:
        benchmark_id: Stable identifier for the preset.
        version: Version string; bump when a change affects scores.
        construct: What capability the preset is designed to probe.
        num_cases: Number of cases generated per seed.
        content_length: Number of non-period tokens per document.
        num_required_facts: Count of required target facts (``RF``).
        num_optional_facts: Count of optional target facts (``TF``).
        num_distractor_facts: Count of distractor facts (``DF``).
        target_position: Where target facts sit within the content.
        sentence_length: Tokens per sentence before a ``.`` separator.
        budget_sweep: Token budgets to recommend sweeping over.
        expected_failure_modes: Human-readable notes on how strategies may fail.
    """

    benchmark_id: str
    version: str
    construct: str
    num_cases: int
    content_length: int
    num_required_facts: int
    num_optional_facts: int
    num_distractor_facts: int
    target_position: TargetPosition
    sentence_length: int = 5
    budget_sweep: tuple[Budget, ...] = (
        Budget(4, BudgetUnit.TOKENS),
        Budget(8, BudgetUnit.TOKENS),
        Budget(16, BudgetUnit.TOKENS),
        Budget(32, BudgetUnit.TOKENS),
    )
    expected_failure_modes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.num_cases < 1:
            raise ValueError("num_cases must be >= 1")
        if self.num_required_facts < 1:
            raise ValueError("num_required_facts must be >= 1")
        if self.num_optional_facts < 0 or self.num_distractor_facts < 0:
            raise ValueError("fact counts must be >= 0")
        if self.sentence_length < 1:
            raise ValueError("sentence_length must be >= 1")
        if self.content_length < self.num_target_facts + self.num_distractor_facts:
            raise ValueError("content_length too small to hold all facts")
        if self.target_position not in _POSITIONS:
            raise ValueError(f"invalid target_position: {self.target_position!r}")
        if not self.budget_sweep:
            raise ValueError("budget_sweep must be non-empty")

    @property
    def num_target_facts(self) -> int:
        """Total target facts (required plus optional)."""
        return self.num_required_facts + self.num_optional_facts


def _target_indices(position: TargetPosition, length: int, count: int) -> list[int]:
    if count == 1:
        midpoint = {
            "early": 0,
            "late": length - 1,
            "middle": length // 2,
            "distributed": length // 2,
        }[position]
        return [midpoint]
    if position == "early":
        return list(range(count))
    if position == "late":
        return list(range(length - count, length))
    if position == "middle":
        start = (length - count) // 2
        return list(range(start, start + count))
    step = (length - 1) / (count - 1)
    return [round(i * step) for i in range(count)]


def _sentences(tokens: list[str], sentence_length: int) -> str:
    parts: list[str] = []
    for start in range(0, len(tokens), sentence_length):
        parts.extend(tokens[start : start + sentence_length])
        parts.append(".")
    return " ".join(parts)


class CompressionBenchmark:
    """A ``compression-fact-preservation`` benchmark built from a config."""

    def __init__(self, config: CompressionConfig) -> None:
        self._config = config

    @property
    def config(self) -> CompressionConfig:
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
        """Token budgets recommended for sweeping."""
        return self._config.budget_sweep

    def generate(self, seed: int) -> Sequence[Case]:
        """Generate deterministic cases from a seed.

        Args:
            seed: Root seed; all randomness derives from it.

        Returns:
            The generated cases, one document each.
        """
        cfg = self._config
        rng = random.Random(derive_seed(seed, cfg.benchmark_id, cfg.version))
        targets = [
            f"{facts.REQUIRED_PREFIX}{i}" for i in range(cfg.num_required_facts)
        ]
        targets += [
            f"{facts.OPTIONAL_PREFIX}{i}" for i in range(cfg.num_optional_facts)
        ]
        cases: list[Case] = []
        for case_index in range(cfg.num_cases):
            slots = [rng.choice(NOISE_TERMS) for _ in range(cfg.content_length)]
            target_at = _target_indices(
                cfg.target_position, cfg.content_length, len(targets)
            )
            for token, index in zip(targets, target_at, strict=True):
                slots[index] = token
            target_set = set(target_at)
            remaining = [i for i in range(cfg.content_length) if i not in target_set]
            distractor_at = sorted(
                rng.sample(remaining, min(cfg.num_distractor_facts, len(remaining)))
            )
            for distractor_index, index in enumerate(distractor_at):
                slots[index] = f"{facts.DISTRACTOR_PREFIX}{distractor_index}"
            content = _sentences(slots, cfg.sentence_length)
            item = Item(
                id=ItemId(f"case{case_index}-doc"),
                content=content,
                length=len(content.split()),
            )
            query = " ".join(facts.required_facts(content))
            cases.append(
                Case(
                    case_id=f"case{case_index}",
                    task=Task(query=query),
                    candidates=(item,),
                    relevant_ids=frozenset({item.id}),
                    required_ids=frozenset({item.id}),
                )
            )
        return cases

    def evaluate(self, case: Case, context: Context) -> Mapping[str, float]:
        """Score a compressed context for a single case.

        Args:
            case: The case that produced the context.
            context: The compressor's output for the case.

        Returns:
            A mapping of declared metric names to values. ``distractor_retention``
            is reported as ``0.0`` when a case has no distractors.
        """
        original = case.candidates[0]
        original_text = original.content
        compressed_text = " ".join(item.content for item in context.items)
        retained = set(facts.fact_tokens(compressed_text))
        original_distractors = facts.distractor_facts(original_text)
        compressed_length = sum(item.length for item in context.items)
        return {
            "answer_support_after_compression": answer_support_after_compression(
                facts.required_facts(original_text), retained
            ),
            "budget_utilization": budget_utilization(
                context.total_cost, context.budget.limit
            ),
            "compression_ratio": compression_ratio(original.length, compressed_length),
            "distractor_retention": (
                distractor_retention(original_distractors, retained)
                if original_distractors
                else 0.0
            ),
            "information_retention": information_retention(
                facts.target_facts(original_text), retained
            ),
        }
