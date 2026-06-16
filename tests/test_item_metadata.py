"""Tests for JSON-safe item metadata."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from context_engineering_lab.core.ids import ItemId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue


def test_metadata_accepts_mixed_json_safe_values() -> None:
    metadata: dict[str, JsonValue] = {
        "source": "wiki",
        "rank": 3,
        "score": 0.75,
        "is_target": True,
        "note": None,
    }
    item = Item(id=ItemId("x"), content="c", metadata=metadata)
    assert item.metadata["source"] == "wiki"
    assert item.metadata["rank"] == 3
    assert item.metadata["score"] == 0.75
    assert item.metadata["is_target"] is True
    assert item.metadata["note"] is None


def test_metadata_is_json_serializable() -> None:
    item = Item(
        id=ItemId("x"),
        content="c",
        metadata={"rank": 1, "score": 0.5, "flag": False, "empty": None, "s": "v"},
    )
    encoded = json.dumps(dict(item.metadata))
    assert json.loads(encoded) == dict(item.metadata)


def test_metadata_defaults_to_empty() -> None:
    item = Item(id=ItemId("x"), content="c")
    assert dict(item.metadata) == {}


def test_item_remains_frozen() -> None:
    item = Item(id=ItemId("x"), content="c", metadata={"rank": 1})
    with pytest.raises(FrozenInstanceError):
        item.metadata = {"rank": 2}  # type: ignore[misc]
