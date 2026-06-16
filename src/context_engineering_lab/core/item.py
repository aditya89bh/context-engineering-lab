"""Information items.

An :class:`Item` is the atomic unit of information that may or may not be placed
in a context (see ``docs/definitions.md``). It carries content, a length used for
token-style budgeting, an optional timestamp for temporal strategies, and free
-form metadata.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from context_engineering_lab.core.ids import ItemId


@dataclass(frozen=True, slots=True)
class Item:
    """A single piece of candidate information.

    Args:
        id: Stable identifier for the item.
        content: The item's textual content.
        length: Token-style length, used when budgeting in tokens. Must be >= 0.
        timestamp: Optional creation/access time as a POSIX-style float. Used by
            temporal strategies; ``None`` means "no temporal information".
        source: Optional provenance label.
        metadata: Optional read-only key/value metadata.
    """

    id: ItemId
    content: str
    length: int = 0
    timestamp: float | None = None
    source: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.length < 0:
            raise ValueError(f"item length cannot be negative, got {self.length}")
