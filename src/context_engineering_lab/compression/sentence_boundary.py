"""Sentence-boundary compression.

An extractive compressor that respects sentence structure. Content is treated as
a sequence of sentences delimited by a ``.`` token; the compressor greedily keeps
whole leading sentences while the next one still fits the budget, never cutting a
sentence in half. It reads no query, so like head truncation it favors early
content — but it keeps coherent units rather than an arbitrary token prefix.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.compression._common import (
    build_result,
    per_item_budgets,
    tokenize,
)
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.compression import CompressionResult
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.task import Task


def _split_sentences(tokens: list[str]) -> list[list[str]]:
    sentences: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        current.append(token)
        if token == ".":
            sentences.append(current)
            current = []
    if current:
        sentences.append(current)
    return sentences


def _keep_sentences(tokens: list[str], k: int) -> list[str]:
    kept: list[str] = []
    for sentence in _split_sentences(tokens):
        if len(kept) + len(sentence) > k:
            break
        kept.extend(sentence)
    return kept


class SentenceBoundaryCompression:
    """Keep whole leading sentences that fit the budget."""

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the compressor."""
        return StrategyId("sentence-boundary")

    def compress(
        self,
        items: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> CompressionResult:
        """Keep leading whole sentences of each item within its budget share."""
        budgets = per_item_budgets(budget.limit, len(items))
        kept = [
            _keep_sentences(tokenize(item.content), k)
            for item, k in zip(items, budgets, strict=True)
        ]
        return build_result(str(self.id), items, kept, budget)
