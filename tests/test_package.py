"""Smoke tests for the package surface."""

from __future__ import annotations

import context_engineering_lab as cel


def test_version_is_exposed() -> None:
    assert isinstance(cel.__version__, str)
    assert cel.__version__.count(".") == 2


def test_public_api_is_importable() -> None:
    for name in ("DEFAULT_SEED", "derive_seed", "seed_everything", "temporary_seed"):
        assert hasattr(cel, name), name
