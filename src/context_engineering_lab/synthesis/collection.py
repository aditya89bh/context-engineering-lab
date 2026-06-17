"""Artifact collection utilities.

Discovers result artifacts on disk and groups loaded results by benchmark or by
strategy. Discovery is recursive and returns paths in a stable, sorted order so
that synthesis over a directory is deterministic regardless of filesystem order.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from context_engineering_lab.core.results import ExperimentResult, StrategyRunResult
from context_engineering_lab.synthesis.loading import ArtifactError, load_artifact


def discover_artifacts(directory: Path | str) -> list[Path]:
    """Recursively find candidate artifact files under a directory.

    Args:
        directory: Root directory to search.

    Returns:
        Sorted list of ``*.json`` paths (sorted by string path for determinism).

    Raises:
        ArtifactError: If ``directory`` does not exist or is not a directory.
    """
    root = Path(directory)
    if not root.exists():
        raise ArtifactError(f"artifact directory not found: {root}")
    if not root.is_dir():
        raise ArtifactError(f"not a directory: {root}")
    return sorted(root.rglob("*.json"), key=str)


def load_collection(
    directory: Path | str, *, skip_invalid: bool = False
) -> list[ExperimentResult]:
    """Discover and load every artifact under a directory.

    Args:
        directory: Root directory to search.
        skip_invalid: When ``True``, silently skip files that fail to load
            (e.g. unrelated JSON); when ``False``, the first failure raises.

    Returns:
        The loaded results, ordered by discovery order.

    Raises:
        ArtifactError: If discovery fails, or a file is invalid and
            ``skip_invalid`` is ``False``.
    """
    results: list[ExperimentResult] = []
    for path in discover_artifacts(directory):
        try:
            results.append(load_artifact(path))
        except ArtifactError:
            if skip_invalid:
                continue
            raise
    return results


def benchmarks_in(results: Sequence[ExperimentResult]) -> list[str]:
    """Return the sorted, unique benchmark ids appearing in ``results``."""
    return sorted({result.metadata.benchmark_id for result in results})


def strategies_in(results: Sequence[ExperimentResult]) -> list[str]:
    """Return the sorted, unique strategy ids appearing in ``results``."""
    return sorted(
        {run.strategy_id for result in results for run in result.results}
    )


def group_by_benchmark(
    results: Sequence[ExperimentResult],
) -> dict[str, list[ExperimentResult]]:
    """Group results by their benchmark id.

    Args:
        results: The results to group.

    Returns:
        A dict mapping benchmark id to its results, with keys in sorted order.
    """
    grouped: dict[str, list[ExperimentResult]] = {}
    for result in results:
        grouped.setdefault(result.metadata.benchmark_id, []).append(result)
    return {key: grouped[key] for key in sorted(grouped)}


def group_by_strategy(
    results: Sequence[ExperimentResult],
) -> dict[str, list[tuple[str, StrategyRunResult]]]:
    """Group strategy runs by strategy id, keeping the benchmark context.

    Args:
        results: The results to group.

    Returns:
        A dict mapping strategy id to a list of ``(benchmark_id, run)`` pairs,
        with keys in sorted order.
    """
    grouped: dict[str, list[tuple[str, StrategyRunResult]]] = {}
    for result in results:
        benchmark_id = result.metadata.benchmark_id
        for run in result.results:
            grouped.setdefault(run.strategy_id, []).append((benchmark_id, run))
    return {key: grouped[key] for key in sorted(grouped)}
