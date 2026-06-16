"""Tests for the compression strategies and the strategy adapter."""

from __future__ import annotations

from context_engineering_lab.compression import default_compressors
from context_engineering_lab.compression.keyword_preserving import (
    KeywordPreservingCompression,
)
from context_engineering_lab.compression.no_compression import NoCompression
from context_engineering_lab.compression.oracle import OracleCompression
from context_engineering_lab.compression.sentence_boundary import (
    SentenceBoundaryCompression,
)
from context_engineering_lab.compression.truncation import (
    HeadTruncationCompression,
    TailTruncationCompression,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit
from context_engineering_lab.core.compression import CompressorStrategy
from context_engineering_lab.core.ids import ItemId, StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.core.task import Task


def doc(content: str) -> Item:
    tokens = content.split()
    return Item(id=ItemId("doc"), content=content, length=len(tokens))


def budget(limit: int) -> Budget:
    return Budget(limit, BudgetUnit.TOKENS)


def tokens_of(result_items: tuple[Item, ...]) -> list[str]:
    return [t for item in result_items for t in item.content.split()]


def test_adapter_satisfies_strategy_protocol() -> None:
    strategy = CompressorStrategy(HeadTruncationCompression())
    assert isinstance(strategy, Strategy)
    assert strategy.id == StrategyId("head-truncation")


def test_no_compression_keeps_all_and_may_overflow() -> None:
    item = doc("a b c d e f")
    result = NoCompression().compress([item], Task(query=""), budget(2))
    assert result.stats.compression_ratio == 1.0
    assert result.context.is_over_budget
    assert tokens_of(result.context.items) == ["a", "b", "c", "d", "e", "f"]


def test_head_truncation_keeps_prefix() -> None:
    item = doc("a b c d e f")
    result = HeadTruncationCompression().compress([item], Task(query=""), budget(3))
    assert tokens_of(result.context.items) == ["a", "b", "c"]
    assert result.stats.compressed_length == 3
    assert not result.context.is_over_budget


def test_tail_truncation_keeps_suffix() -> None:
    item = doc("a b c d e f")
    result = TailTruncationCompression().compress([item], Task(query=""), budget(2))
    assert tokens_of(result.context.items) == ["e", "f"]


def test_keyword_preserving_prioritizes_query_terms() -> None:
    item = doc("x y RF0 z w RF1")
    result = KeywordPreservingCompression().compress(
        [item], Task(query="RF0 RF1"), budget(2)
    )
    # Both query tokens kept, in original order.
    assert tokens_of(result.context.items) == ["RF0", "RF1"]


def test_keyword_preserving_fills_remaining_budget_in_order() -> None:
    item = doc("x y RF0 z")
    result = KeywordPreservingCompression().compress(
        [item], Task(query="RF0"), budget(2)
    )
    # RF0 prioritized, then earliest remaining token (x), reordered by position.
    assert tokens_of(result.context.items) == ["x", "RF0"]


def test_sentence_boundary_keeps_whole_sentences() -> None:
    item = doc("a b . c d . e f .")
    result = SentenceBoundaryCompression().compress([item], Task(query=""), budget(4))
    # Two whole 3-token sentences fit in 4? No: first is 3 tokens, second would be 6.
    assert tokens_of(result.context.items) == ["a", "b", "."]


def test_sentence_boundary_never_splits_a_sentence() -> None:
    item = doc("a b c d e .")
    result = SentenceBoundaryCompression().compress([item], Task(query=""), budget(3))
    # The only sentence is 6 tokens; it does not fit, so nothing is kept.
    assert tokens_of(result.context.items) == []


def test_oracle_keeps_only_target_facts() -> None:
    item = doc("x RF0 y DF0 TF0 z DF1")
    result = OracleCompression().compress([item], Task(query=""), budget(8))
    kept = tokens_of(result.context.items)
    assert kept == ["RF0", "TF0"]  # targets only, distractors and filler dropped


def test_oracle_respects_budget_keeping_earliest_targets() -> None:
    item = doc("RF0 TF0 TF1")
    result = OracleCompression().compress([item], Task(query=""), budget(2))
    assert tokens_of(result.context.items) == ["RF0", "TF0"]


def test_default_compressors_have_distinct_ids() -> None:
    ids = [str(c.id) for c in default_compressors()]
    assert ids == [
        "no-compression",
        "head-truncation",
        "tail-truncation",
        "keyword-preserving",
        "sentence-boundary",
        "oracle-compression",
    ]
