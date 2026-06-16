"""JSON persistence for experiment results.

Writes an :class:`~context_engineering_lab.core.results.ExperimentResult` to a
local file and reads it back. Output is deterministic (sorted keys, stable
indentation) so artifacts diff cleanly across reruns.
"""

from __future__ import annotations

import json
from pathlib import Path

from context_engineering_lab.core.results import ExperimentResult


def write_result(result: ExperimentResult, path: Path | str) -> Path:
    """Write a result to ``path`` as pretty-printed JSON.

    Parent directories are created as needed.

    Args:
        result: The result to serialize.
        path: Destination file path.

    Returns:
        The path written to.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result.to_dict(), indent=2, sort_keys=True)
    destination.write_text(text + "\n", encoding="utf-8")
    return destination


def read_result(path: Path | str) -> ExperimentResult:
    """Read a result previously written by :func:`write_result`.

    Args:
        path: Source file path.

    Returns:
        The deserialized result.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ExperimentResult.from_dict(data)
