"""Guard test: the compression code uses no network or LLM dependencies.

Phase 3 compression must be deterministic and local. This test scans the Phase 3
source modules for imports of networking or LLM client libraries, failing if any
appear. It is a coarse guard, not a sandbox, but it catches accidental
introduction of an external dependency.
"""

from __future__ import annotations

from pathlib import Path

import context_engineering_lab

_PACKAGE_ROOT = Path(context_engineering_lab.__file__).parent

_PHASE3_DIRS = (
    _PACKAGE_ROOT / "compression",
    _PACKAGE_ROOT / "benchmarks",
    _PACKAGE_ROOT / "experiments",
    _PACKAGE_ROOT / "reporting",
    _PACKAGE_ROOT / "core",
)

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
    for directory in _PHASE3_DIRS:
        files.extend(sorted(directory.rglob("*.py")))
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
