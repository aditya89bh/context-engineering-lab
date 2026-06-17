"""Deterministic attention-allocation strategies.

Phase 6 allocators split a fixed budget across competing sources before any item
is selected, without external calls or an LLM. They span a uniform baseline,
size- and salience-proportional splits, a capacity-aware adaptive policy, a
winner-take-most concentrator, and an oracle ceiling. See
``docs/attention-benchmarks.md``.
"""

from __future__ import annotations

from context_engineering_lab.attention.adaptive import AdaptiveAllocation
from context_engineering_lab.attention.oracle import OracleAllocation
from context_engineering_lab.attention.proportional import ProportionalAllocation
from context_engineering_lab.attention.salience import SalienceAllocation
from context_engineering_lab.attention.uniform import UniformAllocation
from context_engineering_lab.attention.winner_take_most import (
    WinnerTakeMostAllocation,
)
from context_engineering_lab.core.attention import AttentionAllocator


def default_allocators() -> tuple[AttentionAllocator, ...]:
    """Return the built-in allocators in a stable order.

    Spans a uniform baseline, size- and salience-proportional splits, a
    capacity-aware adaptive policy, a winner-take-most concentrator, and the
    oracle ceiling (which is **not deployable**).
    """
    return (
        UniformAllocation(),
        ProportionalAllocation(),
        SalienceAllocation(),
        AdaptiveAllocation(),
        WinnerTakeMostAllocation(),
        OracleAllocation(),
    )


__all__ = [
    "AdaptiveAllocation",
    "OracleAllocation",
    "ProportionalAllocation",
    "SalienceAllocation",
    "UniformAllocation",
    "WinnerTakeMostAllocation",
    "default_allocators",
]
