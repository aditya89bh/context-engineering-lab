"""Shared helpers for deterministic compressors.

Compressors differ only in *which tokens they keep* for each item. These helpers
handle the parts they share: splitting a budget across items, tokenizing, and
assembling the compressed :class:`~context_engineering_lab.core.context.Context`
and its :class:`~context_engineering_lab.core.compression.CompressionStats`.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.compression import (
    CompressionResult,
    CompressionStats,
)
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.item import Item


def tokenize(content: str) -> list[str]:
    """Split content into whitespace-delimited tokens."""
    return content.split()


def per_item_budgets(total_limit: int, item_count: int) -> list[int]:
    """Split a total token budget across items as evenly as possible.

    Any remainder is given to the earliest items, so the split is deterministic.

    Args:
        total_limit: The total token budget.
        item_count: Number of items to split across (must be positive).

    Returns:
        A list of per-item token budgets summing to ``total_limit``.
    """
    if item_count <= 0:
        raise ValueError("item_count must be positive")
    base, remainder = divmod(total_limit, item_count)
    return [base + (1 if i < remainder else 0) for i in range(item_count)]


def build_result(
    strategy_id: str,
    originals: Sequence[Item],
    kept_tokens: Sequence[Sequence[str]],
    budget: Budget,
    *,
    allow_overflow: bool = False,
) -> CompressionResult:
    """Assemble a compression result from per-item kept-token lists.

    Each output item keeps the original item's id, timestamp, source, and
    metadata; only its content and token length change.

    Args:
        strategy_id: Id of the compressor producing the result.
        originals: The original items, aligned with ``kept_tokens``.
        kept_tokens: The tokens retained for each item.
        budget: The budget for the produced context.
        allow_overflow: Whether the context may exceed the budget (used only by
            the no-compression baseline).

    Returns:
        The compressed context and its size statistics.
    """
    new_items = tuple(
        Item(
            id=original.id,
            content=" ".join(tokens),
            length=len(tokens),
            timestamp=original.timestamp,
            source=original.source,
            metadata=original.metadata,
        )
        for original, tokens in zip(originals, kept_tokens, strict=True)
    )
    context = Context(items=new_items, budget=budget, allow_overflow=allow_overflow)
    stats = CompressionStats(
        strategy_id=strategy_id,
        original_length=sum(item.length for item in originals),
        compressed_length=sum(len(tokens) for tokens in kept_tokens),
    )
    return CompressionResult(context=context, stats=stats)
