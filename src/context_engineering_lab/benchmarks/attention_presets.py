"""Named presets of the attention benchmark.

Three presets, each isolating one allocation regime built from the
``attention-source-allocation`` generator: balanced sources, signal concentrated
in one source, and a noisy dominant source that baits volume- and salience-based
allocation. Three is intentionally enough; more would add combinations without
adding insight.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.attention import (
    AttentionBenchmark,
    AttentionConfig,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit

_BUDGET_SWEEP: tuple[Budget, ...] = (
    Budget(4, BudgetUnit.ITEMS),
    Budget(8, BudgetUnit.ITEMS),
    Budget(12, BudgetUnit.ITEMS),
    Budget(16, BudgetUnit.ITEMS),
)


def balanced_sources() -> AttentionBenchmark:
    """Similar sources with signal spread evenly.

    Construct: when every source is comparably useful, does any clever allocation
    beat a plain even split? It should not — this is the preset where uniform is
    hard to beat, and concentrating allocators should give up capture.
    """
    return AttentionBenchmark(
        AttentionConfig(
            benchmark_id="balanced-sources",
            version="1.0",
            construct="allocation across comparably useful sources",
            num_cases=24,
            num_sources=4,
            source_size=6,
            quality_imbalance="low",
            signal_concentration="spread",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "winner-take-most starves the other useful sources",
                "no allocator should clearly beat uniform here",
            ),
        )
    )


def concentrated_signal() -> AttentionBenchmark:
    """Most signal sits in one high-quality source.

    Construct: when one source holds the signal, uniform wastes budget on the
    weak sources; quality-aware and winner-take-most allocators should
    concentrate and approach the oracle.
    """
    return AttentionBenchmark(
        AttentionConfig(
            benchmark_id="concentrated-signal",
            version="1.0",
            construct="allocation when signal is concentrated in one source",
            num_cases=24,
            num_sources=4,
            source_size=6,
            quality_imbalance="high",
            signal_concentration="concentrated",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "uniform spends most of the budget on near-empty sources",
                "proportional follows size, not signal",
            ),
        )
    )


def noisy_dominant_source() -> AttentionBenchmark:
    """A large, high-salience, low-quality source baits the budget.

    Construct: the real signal is in one small high-quality source while a big
    source shouts (high salience) but holds little signal. Size- and
    salience-based allocation pour budget into the trap; quality-aware and oracle
    allocation avoid it.
    """
    return AttentionBenchmark(
        AttentionConfig(
            benchmark_id="noisy-dominant-source",
            version="1.0",
            construct="allocation against a large, salient, low-signal trap source",
            num_cases=24,
            num_sources=4,
            source_size=6,
            quality_imbalance="high",
            signal_concentration="concentrated",
            noisy_dominant=True,
            dominant_size_factor=3,
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "proportional pours budget into the oversized trap source",
                "salience is fooled by the trap's inflated salience",
                "uniform wastes a full share on the trap",
            ),
        )
    )


def all_attention_presets() -> tuple[AttentionBenchmark, ...]:
    """Return all three attention presets."""
    return (
        balanced_sources(),
        concentrated_signal(),
        noisy_dominant_source(),
    )
