"""The benchmark interface.

A benchmark is a task plus a way to generate cases plus a way to score a
strategy's output (see ``docs/benchmarks.md``). It declares its metrics and an
optional budget sweep so the runner knows what to measure and over which
budgets.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId, ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task


@dataclass(frozen=True, slots=True)
class Case:
    """A single benchmark instance.

    Args:
        case_id: Stable identifier for the case within a generation.
        task: What the consumer must accomplish.
        candidates: The items available to a strategy for this case.
        relevant_ids: Ground-truth ids of items relevant to the task.
        required_ids: The minimal set of ids needed to succeed. Defaults to
            ``relevant_ids`` when not narrower.
    """

    case_id: str
    task: Task
    candidates: tuple[Item, ...]
    relevant_ids: frozenset[ItemId]
    required_ids: frozenset[ItemId] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.required_ids:
            object.__setattr__(self, "required_ids", self.relevant_ids)


@runtime_checkable
class Benchmark(Protocol):
    """A task, a case generator, and a scoring procedure."""

    @property
    def id(self) -> BenchmarkId:
        """Stable identifier for the benchmark."""
        ...

    @property
    def version(self) -> str:
        """Version string; bump when a change affects scores."""
        ...

    @property
    def declared_metrics(self) -> tuple[str, ...]:
        """Names of the metrics this benchmark reports."""
        ...

    @property
    def budget_sweep(self) -> tuple[Budget, ...]:
        """Budgets the benchmark recommends sweeping over."""
        ...

    def generate(self, seed: int) -> Sequence[Case]:
        """Generate (or load) the benchmark's cases for a given seed.

        Args:
            seed: Root seed; all randomness must derive from it.

        Returns:
            The cases to evaluate.
        """
        ...

    def evaluate(self, case: Case, context: Context) -> Mapping[str, float]:
        """Score a strategy's context for a single case.

        Args:
            case: The case that produced the context.
            context: The strategy's output for the case.

        Returns:
            A mapping from metric name to value for this case.
        """
        ...
