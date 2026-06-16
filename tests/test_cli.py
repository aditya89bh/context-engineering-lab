"""Tests for the CLI skeleton."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_engineering_lab.cli import main
from context_engineering_lab.reporting.persistence import read_result


def test_list_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["list"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "recency" in captured.out
    assert "harness-smoke" in captured.out


def test_run_smoke_writes_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "smoke-result.json"
    exit_code = main(["run-smoke", "--output", str(output), "--seeds", "1", "2"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert output.exists()
    assert "run_id=" in captured.out

    result = read_result(output)
    assert result.metadata.seeds == (1, 2)
    assert result.results[0].strategy_id == "recency"


def test_run_smoke_is_reproducible(tmp_path: Path) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    main(["run-smoke", "--output", str(first), "--seeds", "5"])
    main(["run-smoke", "--output", str(second), "--seeds", "5"])
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")
