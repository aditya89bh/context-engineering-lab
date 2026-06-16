"""Tasks.

A :class:`Task` describes what the consumer must accomplish. It is intentionally
generic: a query string plus an open payload, so that future experiments can
attach richer state (a partial plan, a conversation, a robot pose) without
changing the strategy interface.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Task:
    """A description of what the consumer is trying to do.

    Args:
        query: A natural-language statement of the task or information need.
        payload: Optional structured state accompanying the query.
    """

    query: str
    payload: Mapping[str, str] = field(default_factory=dict)
