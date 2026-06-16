"""The compression interface.

A *compressor* transforms item content to reduce its cost while attempting to
preserve task-relevant information. This is a different operation from selection
(which drops whole items); a compressor keeps items but shortens them.

The interface is deliberately small:

* :class:`Compressor` — a protocol with an ``id`` and a ``compress`` method.
* :class:`CompressionStats` — the size accounting a compression produces.
* :class:`CompressionResult` — the compressed context plus its stats.
* :class:`CompressorStrategy` — adapts any compressor to the
  :class:`~context_engineering_lab.core.strategy.Strategy` interface so the
  existing experiment runner can drive it unchanged.

No plugin system, no abstractive/LLM summarization, no network access — Phase 3
compressors are deterministic, local, and synthetic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task


@dataclass(frozen=True, slots=True)
class CompressionStats:
    """Size accounting for a single compression.

    Args:
        strategy_id: Id of the compressor that produced the result.
        original_length: Total length of the input content, in tokens.
        compressed_length: Total length of the output content, in tokens.
    """

    strategy_id: str
    original_length: int
    compressed_length: int

    @property
    def compression_ratio(self) -> float:
        """Compressed length over original length (``1.0`` if original is 0)."""
        if self.original_length <= 0:
            return 1.0
        return self.compressed_length / self.original_length


@dataclass(frozen=True, slots=True)
class CompressionResult:
    """The output of a compressor: a context and its size accounting."""

    context: Context
    stats: CompressionStats


@runtime_checkable
class Compressor(Protocol):
    """A policy that shortens item content under a budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the compressor."""
        ...

    def compress(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> CompressionResult:
        """Compress items to fit a budget, preserving what the policy values.

        Args:
            items: The items to compress (content is shortened, ids preserved).
            task: The task; supplies the query for query-aware compressors.
            budget: The constraint the produced context should satisfy. A
                no-compression baseline may intentionally exceed it.

        Returns:
            The compressed context and its size statistics.
        """
        ...


class CompressorStrategy:
    """Adapt a :class:`Compressor` to the ``Strategy`` interface.

    The experiment runner calls ``select``; this adapter forwards to the wrapped
    compressor's ``compress`` and returns its context, so compressors run through
    the same harness as selection strategies.

    Args:
        compressor: The compressor to wrap.
    """

    def __init__(self, compressor: Compressor) -> None:
        self._compressor = compressor

    @property
    def id(self) -> StrategyId:
        """Stable identifier, taken from the wrapped compressor."""
        return self._compressor.id

    @property
    def compressor(self) -> Compressor:
        """The wrapped compressor."""
        return self._compressor

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Return the compressed context for the candidates under the budget."""
        return self._compressor.compress(candidates, task, budget).context
