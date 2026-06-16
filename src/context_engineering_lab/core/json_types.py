"""JSON-safe value types.

Shared type aliases for values that can be serialized to JSON without a custom
encoder. Used for item metadata so that experiments can attach scalars (not just
strings) while keeping results trivially serializable.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias

#: A single JSON-serializable scalar value.
JsonValue: TypeAlias = str | int | float | bool | None

#: A read-only mapping of metadata keys to JSON-safe scalar values.
Metadata: TypeAlias = Mapping[str, JsonValue]
