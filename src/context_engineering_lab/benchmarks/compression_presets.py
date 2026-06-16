"""Named presets of the compression benchmark.

Three presets, each isolating one construct. They share the
``compression-fact-preservation`` generator but fix its knobs to probe a specific
question. Three is intentionally enough.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.compression import (
    CompressionBenchmark,
    CompressionConfig,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit

_DEFAULT_SWEEP = (
    Budget(4, BudgetUnit.TOKENS),
    Budget(8, BudgetUnit.TOKENS),
    Budget(16, BudgetUnit.TOKENS),
    Budget(32, BudgetUnit.TOKENS),
)


def easy_compression() -> CompressionBenchmark:
    """Short content, few distractors, target facts early.

    Construct: can a compressor keep the required facts when little stands in the
    way and the facts sit at the front? Head and sentence-boundary compressors
    should do well; tail truncation should struggle at tight budgets.
    """
    return CompressionBenchmark(
        CompressionConfig(
            benchmark_id="easy-compression",
            version="1.0",
            construct="fact preservation with low interference, target facts early",
            num_cases=24,
            content_length=20,
            num_required_facts=2,
            num_optional_facts=2,
            num_distractor_facts=2,
            target_position="early",
            budget_sweep=_DEFAULT_SWEEP,
            expected_failure_modes=(
                "tail truncation drops early facts at small budgets",
                "keyword preservation should track the oracle on required facts",
            ),
        )
    )


def late_signal_compression() -> CompressionBenchmark:
    """Target facts placed late: exposes position bias in truncation.

    Construct: does a compressor succeed for the wrong reason? With facts at the
    end, head truncation and sentence-boundary extraction should fail at small
    budgets while tail truncation succeeds by position, not by relevance.
    """
    return CompressionBenchmark(
        CompressionConfig(
            benchmark_id="late-signal-compression",
            version="1.0",
            construct="position bias of truncation (target facts placed late)",
            num_cases=24,
            content_length=30,
            num_required_facts=2,
            num_optional_facts=2,
            num_distractor_facts=4,
            target_position="late",
            budget_sweep=_DEFAULT_SWEEP,
            expected_failure_modes=(
                "head truncation and sentence-boundary miss late facts",
                "tail truncation succeeds by position, not by relevance",
            ),
        )
    )


def dense_distractor_compression() -> CompressionBenchmark:
    """Many distractor facts spread through the content.

    Construct: does compression discard distractors or launder them into the
    output? Position-based and keyword compressors retain distractors they happen
    to keep; only the oracle reliably drops them.
    """
    return CompressionBenchmark(
        CompressionConfig(
            benchmark_id="dense-distractor-compression",
            version="1.0",
            construct="distractor discarding under heavy distractor density",
            num_cases=24,
            content_length=40,
            num_required_facts=2,
            num_optional_facts=2,
            num_distractor_facts=20,
            target_position="distributed",
            budget_sweep=_DEFAULT_SWEEP,
            expected_failure_modes=(
                "truncation and keyword preservation retain many distractors",
                "only the oracle drops distractors reliably",
            ),
        )
    )


def all_compression_presets() -> tuple[CompressionBenchmark, ...]:
    """Return all three compression presets."""
    return (
        easy_compression(),
        late_signal_compression(),
        dense_distractor_compression(),
    )
