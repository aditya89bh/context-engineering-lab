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


def test_run_phase2_writes_artifacts_and_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "phase2"
    exit_code = main(["run-phase2", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run_id=" in captured.out
    summary = output / "summary.md"
    assert summary.exists()
    for name in (
        "selection-baselines-easy",
        "selection-position-bias",
        "selection-distractor-stress",
        "selection-budget-sweep",
    ):
        artifact = output / f"{name}.json"
        assert artifact.exists()
        assert read_result(artifact).results
    assert "Phase 2 report" in summary.read_text(encoding="utf-8")


def test_run_phase2_is_reproducible(tmp_path: Path) -> None:
    first = tmp_path / "one"
    second = tmp_path / "two"
    main(["run-phase2", "--output", str(first)])
    main(["run-phase2", "--output", str(second)])
    first_summary = (first / "summary.md").read_text(encoding="utf-8")
    second_summary = (second / "summary.md").read_text(encoding="utf-8")
    assert first_summary == second_summary


def test_run_phase3_writes_artifacts_and_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "phase3"
    exit_code = main(["run-phase3", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run_id=" in captured.out
    summary = output / "summary.md"
    assert summary.exists()
    for name in (
        "compression-baselines-easy",
        "compression-late-signal",
        "compression-distractor-density",
        "compression-budget-sweep",
    ):
        artifact = output / f"{name}.json"
        assert artifact.exists()
        assert read_result(artifact).results
    assert "Phase 3 report" in summary.read_text(encoding="utf-8")


def test_run_phase3_is_reproducible(tmp_path: Path) -> None:
    first = tmp_path / "one"
    second = tmp_path / "two"
    main(["run-phase3", "--output", str(first)])
    main(["run-phase3", "--output", str(second)])
    assert (first / "summary.md").read_text(encoding="utf-8") == (
        second / "summary.md"
    ).read_text(encoding="utf-8")


def test_run_phase4_writes_artifacts_and_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "phase4"
    exit_code = main(["run-phase4", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run_id=" in captured.out
    summary = output / "summary.md"
    assert summary.exists()
    for name in (
        "temporal-recent-signal",
        "temporal-old-signal",
        "temporal-drift",
        "temporal-budget-sweep",
    ):
        artifact = output / f"{name}.json"
        assert artifact.exists()
        assert read_result(artifact).results
    assert "Phase 4 report" in summary.read_text(encoding="utf-8")


def test_run_phase4_is_reproducible(tmp_path: Path) -> None:
    first = tmp_path / "one"
    second = tmp_path / "two"
    main(["run-phase4", "--output", str(first)])
    main(["run-phase4", "--output", str(second)])
    assert (first / "summary.md").read_text(encoding="utf-8") == (
        second / "summary.md"
    ).read_text(encoding="utf-8")
