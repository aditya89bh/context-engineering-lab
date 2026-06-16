"""Result models.

Typed, JSON-serializable records of what an experiment produced. A
:class:`MetricValue` is a single measurement at one seed and budget; a
:class:`StrategyRunResult` collects all measurements for one strategy; an
:class:`ExperimentResult` bundles every strategy's results together with the
run's :class:`~context_engineering_lab.core.metadata.RunMetadata`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from context_engineering_lab.core.metadata import RunMetadata


@dataclass(frozen=True, slots=True)
class MetricValue:
    """A single metric measurement at one seed and budget.

    Args:
        name: Metric name (must be one the benchmark declared).
        value: Aggregated value across the cases for this seed/budget.
        seed: The seed under which the cases were generated.
        budget_limit: The budget limit used.
        budget_unit: The budget unit used.
        sample_size: Number of cases aggregated.
        stddev: Population standard deviation across cases (0.0 for one case).
    """

    name: str
    value: float
    seed: int
    budget_limit: int
    budget_unit: str
    sample_size: int
    stddev: float

    def to_dict(self) -> dict[str, Any]:
        """Render to a JSON-serializable dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "seed": self.seed,
            "budget_limit": self.budget_limit,
            "budget_unit": self.budget_unit,
            "sample_size": self.sample_size,
            "stddev": self.stddev,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetricValue:
        """Reconstruct from a dictionary produced by :meth:`to_dict`."""
        return cls(
            name=str(data["name"]),
            value=float(data["value"]),
            seed=int(data["seed"]),
            budget_limit=int(data["budget_limit"]),
            budget_unit=str(data["budget_unit"]),
            sample_size=int(data["sample_size"]),
            stddev=float(data["stddev"]),
        )


@dataclass(frozen=True, slots=True)
class StrategyRunResult:
    """All metric values produced by a single strategy in a run."""

    strategy_id: str
    metrics: tuple[MetricValue, ...]

    def to_dict(self) -> dict[str, Any]:
        """Render to a JSON-serializable dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "metrics": [m.to_dict() for m in self.metrics],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyRunResult:
        """Reconstruct from a dictionary produced by :meth:`to_dict`."""
        return cls(
            strategy_id=str(data["strategy_id"]),
            metrics=tuple(MetricValue.from_dict(m) for m in data["metrics"]),
        )


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """The complete, serializable result of one experiment run."""

    metadata: RunMetadata
    results: tuple[StrategyRunResult, ...]

    def to_dict(self) -> dict[str, Any]:
        """Render to a JSON-serializable dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "results": [r.to_dict() for r in self.results],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExperimentResult:
        """Reconstruct from a dictionary produced by :meth:`to_dict`."""
        return cls(
            metadata=RunMetadata.from_dict(data["metadata"]),
            results=tuple(
                StrategyRunResult.from_dict(r) for r in data["results"]
            ),
        )
