"""Guard test: the lab code uses no network or LLM dependencies.

Compression (Phase 3), temporal (Phase 4), retention (Phase 5), attention
(Phase 6), interaction (Phase 7), naturalistic (Phase 8), and synthesis (Phase 9)
work must be deterministic and local. This test scans the source modules for
imports of networking or LLM client libraries,
failing if any appear. It is a coarse guard, not a sandbox, but it catches
accidental introduction of an external dependency.
"""

from __future__ import annotations

from pathlib import Path

import context_engineering_lab

_PACKAGE_ROOT = Path(context_engineering_lab.__file__).parent

_SCANNED_DIRS = (
    _PACKAGE_ROOT / "compression",
    _PACKAGE_ROOT / "retention",
    _PACKAGE_ROOT / "attention",
    _PACKAGE_ROOT / "benchmarks",
    _PACKAGE_ROOT / "experiments",
    _PACKAGE_ROOT / "reporting",
    _PACKAGE_ROOT / "strategies",
    _PACKAGE_ROOT / "core",
    _PACKAGE_ROOT / "synthesis",
)

_SCANNED_FILES = (_PACKAGE_ROOT / "compositions.py",)

_FORBIDDEN = (
    "import requests",
    "import httpx",
    "import urllib",
    "import http.client",
    "import socket",
    "import aiohttp",
    "import openai",
    "import anthropic",
    "from requests",
    "from httpx",
    "from urllib",
    "from openai",
    "from anthropic",
)


def _python_files() -> list[Path]:
    files: list[Path] = []
    for directory in _SCANNED_DIRS:
        files.extend(sorted(directory.rglob("*.py")))
    files.extend(path for path in _SCANNED_FILES if path.exists())
    return files


def test_no_network_or_llm_imports() -> None:
    offenders: list[str] = []
    for path in _python_files():
        text = path.read_text(encoding="utf-8")
        for needle in _FORBIDDEN:
            if needle in text:
                offenders.append(f"{path.name}: {needle}")
    assert not offenders, f"forbidden external imports found: {offenders}"


def test_guard_covers_the_compression_modules() -> None:
    names = {path.name for path in _python_files()}
    assert "compression.py" in names  # the benchmark
    assert "oracle.py" in names  # a compressor


def test_guard_covers_the_temporal_modules() -> None:
    names = {path.name for path in _python_files()}
    assert "temporal.py" in names  # temporal strategies and benchmark
    assert "temporal_metrics.py" in names


def test_guard_covers_the_retention_modules() -> None:
    names = {path.name for path in _python_files()}
    assert "retention.py" in names  # retention interface and benchmark
    assert "retention_metrics.py" in names
    assert "hybrid.py" in names  # a retention policy


def test_guard_covers_the_attention_modules() -> None:
    names = {path.name for path in _python_files()}
    assert "attention.py" in names  # attention interface and benchmark
    assert "attention_metrics.py" in names
    assert "adaptive.py" in names  # an allocator


def test_guard_covers_the_interaction_modules() -> None:
    names = {path.name for path in _python_files()}
    assert "composition.py" in names  # the composition abstraction
    assert "interaction_metrics.py" in names
    assert "interaction.py" in names  # the benchmark
    assert "compositions.py" in names  # the built-in compositions


def test_guard_covers_the_naturalistic_modules() -> None:
    names = {path.name for path in _python_files()}
    assert "records.py" in names  # the naturalistic engine and record helpers
    assert "naturalistic_metrics.py" in names
    assert "email.py" in names  # a benchmark family
    assert "phase8.py" in names  # the experiments
    assert "phase8_report.py" in names  # the report


def test_guard_covers_the_synthesis_modules() -> None:
    names = {path.name for path in _python_files()}
    assert "aggregation.py" in names  # aggregation models and orientation
    assert "dominance.py" in names  # dominance analysis
    assert "oracle_gap.py" in names  # oracle-gap analysis
    assert "phase9_report.py" in names  # the synthesis report


def test_naturalistic_package_ships_no_data_fixtures() -> None:
    """The naturalistic benchmarks are generated, not loaded from data files."""
    naturalistic = _PACKAGE_ROOT / "benchmarks" / "naturalistic"
    non_python = [
        path.name
        for path in naturalistic.rglob("*")
        if path.is_file()
        and path.suffix != ".py"
        and "__pycache__" not in path.parts
    ]
    assert not non_python, f"unexpected data fixtures present: {non_python}"
