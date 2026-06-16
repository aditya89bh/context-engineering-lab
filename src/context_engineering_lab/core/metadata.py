"""Deterministic run metadata.

Every experiment run records the metadata needed to reproduce it. The
:class:`RunId` is derived deterministically from the experiment configuration
(not from wall-clock time), so the same configuration always yields the same id
and reruns are detectable. Environment details (Python version, platform) are
recorded as observations but deliberately excluded from the run id, which
identifies the *configuration*, not the machine.
"""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass
from typing import Any

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import RunId


def _canonical_config(
    experiment_id: str,
    benchmark_id: str,
    benchmark_version: str,
    strategy_ids: tuple[str, ...],
    seeds: tuple[int, ...],
    budgets: tuple[Budget, ...],
) -> str:
    """Render a configuration to a stable, canonical JSON string."""
    payload = {
        "experiment_id": experiment_id,
        "benchmark_id": benchmark_id,
        "benchmark_version": benchmark_version,
        "strategy_ids": list(strategy_ids),
        "seeds": list(seeds),
        "budgets": [[b.limit, b.unit.value] for b in budgets],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_run_id(
    experiment_id: str,
    benchmark_id: str,
    benchmark_version: str,
    strategy_ids: tuple[str, ...],
    seeds: tuple[int, ...],
    budgets: tuple[Budget, ...],
) -> RunId:
    """Derive a deterministic run id from an experiment configuration.

    Returns:
        A :class:`RunId` whose value is a 16-byte BLAKE2b hex digest of the
        canonical configuration.
    """
    canonical = _canonical_config(
        experiment_id,
        benchmark_id,
        benchmark_version,
        strategy_ids,
        seeds,
        budgets,
    )
    digest = hashlib.blake2b(canonical.encode("utf-8"), digest_size=16).hexdigest()
    return RunId(digest)


@dataclass(frozen=True, slots=True)
class RunMetadata:
    """Provenance recorded for a single experiment run."""

    run_id: RunId
    experiment_id: str
    benchmark_id: str
    benchmark_version: str
    strategy_ids: tuple[str, ...]
    seeds: tuple[int, ...]
    budgets: tuple[tuple[int, str], ...]
    code_version: str
    python_version: str
    platform: str

    def to_dict(self) -> dict[str, Any]:
        """Render the metadata to a JSON-serializable dictionary."""
        return {
            "run_id": self.run_id.value,
            "experiment_id": self.experiment_id,
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "strategy_ids": list(self.strategy_ids),
            "seeds": list(self.seeds),
            "budgets": [list(b) for b in self.budgets],
            "code_version": self.code_version,
            "python_version": self.python_version,
            "platform": self.platform,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunMetadata:
        """Reconstruct metadata from a dictionary produced by :meth:`to_dict`."""
        return cls(
            run_id=RunId(str(data["run_id"])),
            experiment_id=str(data["experiment_id"]),
            benchmark_id=str(data["benchmark_id"]),
            benchmark_version=str(data["benchmark_version"]),
            strategy_ids=tuple(str(s) for s in data["strategy_ids"]),
            seeds=tuple(int(s) for s in data["seeds"]),
            budgets=tuple((int(limit), str(unit)) for limit, unit in data["budgets"]),
            code_version=str(data["code_version"]),
            python_version=str(data["python_version"]),
            platform=str(data["platform"]),
        )


def build_run_metadata(
    experiment_id: str,
    benchmark_id: str,
    benchmark_version: str,
    strategy_ids: tuple[str, ...],
    seeds: tuple[int, ...],
    budgets: tuple[Budget, ...],
    code_version: str,
) -> RunMetadata:
    """Assemble :class:`RunMetadata`, computing the run id and environment."""
    run_id = compute_run_id(
        experiment_id,
        benchmark_id,
        benchmark_version,
        strategy_ids,
        seeds,
        budgets,
    )
    return RunMetadata(
        run_id=run_id,
        experiment_id=experiment_id,
        benchmark_id=benchmark_id,
        benchmark_version=benchmark_version,
        strategy_ids=strategy_ids,
        seeds=seeds,
        budgets=tuple((b.limit, b.unit.value) for b in budgets),
        code_version=code_version,
        python_version=platform.python_version(),
        platform=f"{platform.system()} {platform.release()}",
    )


__all__ = [
    "RunMetadata",
    "build_run_metadata",
    "compute_run_id",
]
