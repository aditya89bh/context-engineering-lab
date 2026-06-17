"""Artifact loading utilities.

Reads experiment-result artifacts written by the Phase 2-8 suites
(:func:`context_engineering_lab.reporting.persistence.write_result`) back into
typed :class:`~context_engineering_lab.core.results.ExperimentResult` objects, but
with explicit schema validation and friendly errors. The persistence reader
assumes a well-formed file; synthesis may be pointed at an arbitrary directory, so
here a missing file, malformed JSON, or a structurally invalid artifact raises a
single :class:`ArtifactError` rather than a bare ``KeyError`` or ``OSError``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from context_engineering_lab.core.results import ExperimentResult

#: Top-level keys every artifact must contain.
_REQUIRED_TOP_LEVEL = ("metadata", "results")

#: Metadata keys synthesis relies on.
_REQUIRED_METADATA = (
    "run_id",
    "experiment_id",
    "benchmark_id",
    "benchmark_version",
    "strategy_ids",
    "seeds",
    "budgets",
)

#: Keys every metric record must contain.
_REQUIRED_METRIC = (
    "name",
    "value",
    "seed",
    "budget_limit",
    "budget_unit",
)


class ArtifactError(Exception):
    """Raised when an artifact is missing, unreadable, or structurally invalid."""


def _require_keys(where: str, data: Mapping[str, Any], keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ArtifactError(f"{where} is missing keys: {sorted(missing)}")


def validate_artifact_schema(data: Any) -> None:
    """Validate the structure of a decoded artifact.

    Checks only the shape synthesis depends on — top-level, metadata, and metric
    keys — not every field. Raises :class:`ArtifactError` on the first problem.

    Args:
        data: The object decoded from an artifact's JSON.

    Raises:
        ArtifactError: If the structure is not a valid artifact.
    """
    if not isinstance(data, Mapping):
        raise ArtifactError("artifact root must be a JSON object")
    _require_keys("artifact", data, _REQUIRED_TOP_LEVEL)

    metadata = data["metadata"]
    if not isinstance(metadata, Mapping):
        raise ArtifactError("artifact metadata must be a JSON object")
    _require_keys("artifact metadata", metadata, _REQUIRED_METADATA)

    results = data["results"]
    if not isinstance(results, list):
        raise ArtifactError("artifact results must be a JSON array")
    for index, run in enumerate(results):
        if not isinstance(run, Mapping):
            raise ArtifactError(f"results[{index}] must be a JSON object")
        _require_keys(f"results[{index}]", run, ("strategy_id", "metrics"))
        metrics = run["metrics"]
        if not isinstance(metrics, list):
            raise ArtifactError(f"results[{index}].metrics must be a JSON array")
        for m_index, metric in enumerate(metrics):
            if not isinstance(metric, Mapping):
                raise ArtifactError(
                    f"results[{index}].metrics[{m_index}] must be a JSON object"
                )
            _require_keys(
                f"results[{index}].metrics[{m_index}]", metric, _REQUIRED_METRIC
            )


def load_artifact(path: Path | str) -> ExperimentResult:
    """Load and validate a single result artifact.

    Args:
        path: Path to a JSON artifact written by ``write_result``.

    Returns:
        The deserialized :class:`ExperimentResult`.

    Raises:
        ArtifactError: If the file is missing, is not valid JSON, or does not
            match the artifact schema.
    """
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ArtifactError(f"artifact not found: {source}") from exc
    except OSError as exc:  # pragma: no cover - unusual filesystem failure
        raise ArtifactError(f"could not read artifact {source}: {exc}") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ArtifactError(f"artifact {source} is not valid JSON: {exc}") from exc

    validate_artifact_schema(data)
    try:
        return ExperimentResult.from_dict(data)
    except (KeyError, ValueError, TypeError) as exc:
        raise ArtifactError(f"artifact {source} could not be parsed: {exc}") from exc
