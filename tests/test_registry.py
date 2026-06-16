"""Tests for the typed registry."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.registry import Registry


def test_register_and_get() -> None:
    reg: Registry[int] = Registry("number")
    reg.register("one", 1)
    reg.register("two", 2)
    assert reg.get("one") == 1
    assert "two" in reg
    assert len(reg) == 2


def test_register_rejects_duplicates() -> None:
    reg: Registry[int] = Registry("number")
    reg.register("one", 1)
    with pytest.raises(ValueError):
        reg.register("one", 11)


def test_names_are_sorted() -> None:
    reg: Registry[int] = Registry("number")
    reg.register("b", 2)
    reg.register("a", 1)
    assert reg.names() == ["a", "b"]


def test_get_missing_raises_with_available() -> None:
    reg: Registry[int] = Registry("number")
    reg.register("one", 1)
    with pytest.raises(KeyError) as info:
        reg.get("missing")
    assert "one" in str(info.value)
