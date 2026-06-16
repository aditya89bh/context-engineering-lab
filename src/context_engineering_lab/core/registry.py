"""A small, typed registry.

Used to look up strategies and benchmarks by id. It is deliberately tiny: it
registers entries, rejects duplicate ids, lists what is available, and retrieves
by id with a helpful error. No plugin discovery, no entry points.
"""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """An ordered, duplicate-rejecting mapping from string ids to entries.

    Args:
        kind: A human-readable label (e.g. ``"strategy"``) used in error
            messages.
    """

    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._entries: dict[str, T] = {}

    def register(self, key: str, value: T) -> None:
        """Register ``value`` under ``key``.

        Args:
            key: The id to register under.
            value: The entry to store.

        Raises:
            ValueError: If ``key`` is already registered.
        """
        if key in self._entries:
            raise ValueError(f"{self._kind} id already registered: {key!r}")
        self._entries[key] = value

    def get(self, key: str) -> T:
        """Retrieve the entry registered under ``key``.

        Args:
            key: The id to look up.

        Returns:
            The registered entry.

        Raises:
            KeyError: If nothing is registered under ``key``.
        """
        try:
            return self._entries[key]
        except KeyError:
            available = ", ".join(self.names()) or "<none>"
            raise KeyError(
                f"no {self._kind} registered under {key!r}; available: {available}"
            ) from None

    def names(self) -> list[str]:
        """Return the registered ids in sorted order."""
        return sorted(self._entries)

    def __contains__(self, key: object) -> bool:
        return key in self._entries

    def __len__(self) -> int:
        return len(self._entries)
