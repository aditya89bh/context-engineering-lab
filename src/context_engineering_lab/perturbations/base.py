"""Perturbation abstractions.

A *perturbation* is a deterministic transform from a benchmark
:class:`~context_engineering_lab.core.benchmark.Case` to a stressed case. It may
add candidate items (distractors, contradictions, amplified stale facts) or
rewrite the observable metadata of existing items (source-quality or salience
corruption). A perturbation never touches ground truth: it leaves ``relevant_ids``
and ``required_ids`` and the privileged oracle markers alone, so the oracle ceiling
is unchanged and only signal-using strategies can degrade.

:class:`PerturbedBenchmark` wraps an existing benchmark with a perturbation so a
stressed run flows through the ordinary
:class:`~context_engineering_lab.core.runner.ExperimentRunner` unchanged: it
re-generates the inner cases, perturbs each one with a seed derived from the run
seed, and delegates scoring back to the inner benchmark.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from context_engineering_lab.core.benchmark import Benchmark, Case
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import BenchmarkId
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.seeding import derive_seed


@dataclass(frozen=True, slots=True)
class PerturbationConfig:
    """Knobs shared by perturbations.

    Args:
        perturbation_id: Stable identifier for the perturbation instance.
        intensity: Strength in ``[0.0, 1.0]``. For corruptions this is how far a
            signal may be distorted; for injections it scales nothing directly
            but is recorded for provenance.
        count: Number of items an injection perturbation adds per case. Ignored
            by corruption perturbations. Must be ``>= 0``.
        params: Optional extra JSON-safe knobs for a specific perturbation.
    """

    perturbation_id: str
    intensity: float = 1.0
    count: int = 0
    params: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.perturbation_id:
            raise ValueError("perturbation_id must be non-empty")
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(
                f"intensity must be in [0.0, 1.0], got {self.intensity}"
            )
        if self.count < 0:
            raise ValueError(f"count cannot be negative, got {self.count}")


@dataclass(frozen=True, slots=True)
class PerturbationResult:
    """The outcome of applying a perturbation to a single case.

    Args:
        perturbation_id: The perturbation that produced this result.
        case: The transformed case to evaluate in place of the original.
        items_added: How many candidate items the perturbation injected.
        items_modified: How many existing candidate items it rewrote.
    """

    perturbation_id: str
    case: Case
    items_added: int
    items_modified: int


@runtime_checkable
class Perturbation(Protocol):
    """A deterministic transform from a case to a stressed case."""

    @property
    def id(self) -> str:
        """Stable identifier for the perturbation."""
        ...

    @property
    def config(self) -> PerturbationConfig:
        """The perturbation's configuration."""
        ...

    def apply(self, case: Case, rng: random.Random) -> PerturbationResult:
        """Transform ``case`` using ``rng`` for any randomness.

        Args:
            case: The case to perturb.
            rng: A seeded RNG; all randomness must derive from it so the
                transform is reproducible.

        Returns:
            The perturbation result wrapping the transformed case.
        """
        ...


class BasePerturbation:
    """Common ``id``/``config`` plumbing for perturbations.

    Subclasses implement :meth:`apply`.
    """

    def __init__(self, config: PerturbationConfig) -> None:
        self._config = config

    @property
    def id(self) -> str:
        """Stable identifier for the perturbation."""
        return self._config.perturbation_id

    @property
    def config(self) -> PerturbationConfig:
        """The perturbation's configuration."""
        return self._config

    def apply(self, case: Case, rng: random.Random) -> PerturbationResult:
        """Transform ``case`` (implemented by subclasses)."""
        raise NotImplementedError


class PerturbedBenchmark:
    """An existing benchmark whose cases are stressed by a perturbation.

    The wrapper conforms to the
    :class:`~context_engineering_lab.core.benchmark.Benchmark` protocol. It keeps
    the inner benchmark's metrics, budget sweep, and scoring, and only rewrites
    the cases ``generate`` returns. Scoring is delegated unchanged, so a metric
    measured on a perturbed run is directly comparable to the baseline.

    Args:
        inner: The benchmark to stress. Not modified.
        perturbation: The transform applied to each generated case.
    """

    def __init__(self, inner: Benchmark, perturbation: Perturbation) -> None:
        self._inner = inner
        self._perturbation = perturbation

    @property
    def inner(self) -> Benchmark:
        """The wrapped (unperturbed) benchmark."""
        return self._inner

    @property
    def perturbation(self) -> Perturbation:
        """The perturbation applied to each case."""
        return self._perturbation

    @property
    def id(self) -> BenchmarkId:
        """The inner id suffixed with the perturbation id (``base+perturb``)."""
        return BenchmarkId(f"{self._inner.id}+{self._perturbation.id}")

    @property
    def version(self) -> str:
        """The inner benchmark's version (scoring is unchanged)."""
        return self._inner.version

    @property
    def declared_metrics(self) -> tuple[str, ...]:
        """The inner benchmark's declared metrics."""
        return tuple(self._inner.declared_metrics)

    @property
    def budget_sweep(self) -> tuple[Budget, ...]:
        """The inner benchmark's recommended budget sweep."""
        return tuple(self._inner.budget_sweep)

    def generate(self, seed: int) -> Sequence[Case]:
        """Generate the inner cases, then perturb each one deterministically.

        Args:
            seed: Root seed; the inner generation and every per-case perturbation
                RNG derive from it.

        Returns:
            The perturbed cases.
        """
        cases = self._inner.generate(seed)
        perturbed: list[Case] = []
        for index, case in enumerate(cases):
            sub = derive_seed(
                seed, str(self.id), self._perturbation.id, str(index)
            )
            rng = random.Random(sub)
            perturbed.append(self._perturbation.apply(case, rng).case)
        return perturbed

    def evaluate(self, case: Case, context: Context) -> Mapping[str, float]:
        """Delegate scoring to the inner benchmark unchanged."""
        return self._inner.evaluate(case, context)
