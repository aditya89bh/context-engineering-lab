"""Structural audit tests (Phase 11 release hardening).

These guard repository-wide invariants rather than any single behaviour: the
public API is consistent, every module imports cleanly, the built-in catalog has
unique non-empty ids, the package ships its type marker, and library code does no
stray printing. They are cheap insurance that the published artifact stays
coherent.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
from pathlib import Path

import pytest

import context_engineering_lab as cel
from context_engineering_lab.catalog import (
    build_attention_allocator_registry,
    build_benchmark_registry,
    build_composition_registry,
    build_compressor_registry,
    build_retention_policy_registry,
    build_strategy_registry,
)

_PACKAGE_ROOT = Path(cel.__file__).parent

_CATALOG_BUILDERS = (
    build_strategy_registry,
    build_benchmark_registry,
    build_compressor_registry,
    build_retention_policy_registry,
    build_attention_allocator_registry,
    build_composition_registry,
)


def test_public_all_is_unique_and_exported() -> None:
    names = list(cel.__all__)
    assert len(names) == len(set(names)), "duplicate names in __all__"
    for name in names:
        assert hasattr(cel, name), f"missing exported name: {name}"


def test_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", cel.__version__), cel.__version__


def test_every_submodule_imports_cleanly() -> None:
    failures: list[str] = []
    for module in pkgutil.walk_packages(cel.__path__, cel.__name__ + "."):
        try:
            importlib.import_module(module.name)
        except Exception as exc:  # report which module failed
            failures.append(f"{module.name}: {exc}")
    assert not failures, f"modules failed to import: {failures}"


@pytest.mark.parametrize("build", _CATALOG_BUILDERS)
def test_catalog_registries_have_unique_nonempty_ids(build: object) -> None:
    registry = build()  # type: ignore[operator]
    names = registry.names()
    assert names, "registry is empty"
    assert names == sorted(set(names)), "ids must be unique and sorted"
    assert all(name.strip() for name in names), "ids must be non-empty"


def test_py_typed_marker_ships() -> None:
    assert (_PACKAGE_ROOT / "py.typed").is_file()


def test_library_code_does_no_stray_printing() -> None:
    offenders: list[str] = []
    for path in _PACKAGE_ROOT.rglob("*.py"):
        if path.name == "cli.py":  # the CLI legitimately prints
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("print("):
                offenders.append(f"{path.relative_to(_PACKAGE_ROOT)}:{lineno}")
    assert not offenders, f"unexpected print() in library code: {offenders}"
