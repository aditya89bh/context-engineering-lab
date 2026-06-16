"""Deterministic compression strategies.

Phase 3 compressors shorten item content under a budget without any external
calls or LLM summarization. They span a no-compression baseline, position-based
truncation, query-aware keyword preservation, sentence-boundary extraction, and
an oracle ceiling. See ``docs/compression-benchmarks.md``.
"""

from __future__ import annotations

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
from context_engineering_lab.core.compression import Compressor


def default_compressors() -> tuple[Compressor, ...]:
    """Return the built-in compressors in a stable order.

    Spans a no-compression reference, two position-based truncators, a query-aware
    keyword preserver, a sentence-boundary extractor, and the oracle ceiling
    (which is **not deployable**).
    """
    return (
        NoCompression(),
        HeadTruncationCompression(),
        TailTruncationCompression(),
        KeywordPreservingCompression(),
        SentenceBoundaryCompression(),
        OracleCompression(),
    )


__all__ = [
    "HeadTruncationCompression",
    "KeywordPreservingCompression",
    "NoCompression",
    "OracleCompression",
    "SentenceBoundaryCompression",
    "TailTruncationCompression",
    "default_compressors",
]
