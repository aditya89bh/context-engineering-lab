"""Built-in catalog.

Builds registries populated with the strategies and benchmarks that ship with
the package. Registration is explicit (no import-time side effects or plugin
discovery) so the available entries are easy to reason about.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.compression_presets import (
    all_compression_presets,
)
from context_engineering_lab.benchmarks.retention_presets import (
    all_retention_presets,
)
from context_engineering_lab.benchmarks.selection_presets import all_selection_presets
from context_engineering_lab.benchmarks.smoke import SmokeBenchmark
from context_engineering_lab.benchmarks.temporal_presets import all_temporal_presets
from context_engineering_lab.compression import default_compressors
from context_engineering_lab.core.benchmark import Benchmark
from context_engineering_lab.core.compression import Compressor
from context_engineering_lab.core.registry import Registry
from context_engineering_lab.core.retention import RetentionPolicy
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.retention import default_policies
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection
from context_engineering_lab.strategies.oracle import OracleSelection
from context_engineering_lab.strategies.positional import (
    FirstNSelection,
    LastNSelection,
)
from context_engineering_lab.strategies.random_selection import RandomSelection
from context_engineering_lab.strategies.recency import RecencySelection
from context_engineering_lab.strategies.temporal import (
    AgeWeightedSelection,
    FixedWindowSelection,
    OldestFirstSelection,
    OracleTemporalSelection,
    SlidingWindowSelection,
)


def build_strategy_registry() -> Registry[Strategy]:
    """Return a registry populated with the built-in strategies."""
    registry: Registry[Strategy] = Registry("strategy")
    strategies: tuple[Strategy, ...] = (
        FirstNSelection(),
        LastNSelection(),
        RecencySelection(),
        RandomSelection(),
        KeywordOverlapSelection(),
        OracleSelection(),
        OldestFirstSelection(),
        SlidingWindowSelection(),
        FixedWindowSelection(),
        AgeWeightedSelection(),
        OracleTemporalSelection(),
    )
    for strategy in strategies:
        registry.register(str(strategy.id), strategy)
    return registry


def build_benchmark_registry() -> Registry[Benchmark]:
    """Return a registry populated with the built-in benchmarks."""
    registry: Registry[Benchmark] = Registry("benchmark")
    benchmarks: tuple[Benchmark, ...] = (
        SmokeBenchmark(),
        *all_selection_presets(),
        *all_compression_presets(),
        *all_temporal_presets(),
        *all_retention_presets(),
    )
    for benchmark in benchmarks:
        registry.register(str(benchmark.id), benchmark)
    return registry


def build_compressor_registry() -> Registry[Compressor]:
    """Return a registry populated with the built-in compressors."""
    registry: Registry[Compressor] = Registry("compressor")
    for compressor in default_compressors():
        registry.register(str(compressor.id), compressor)
    return registry


def build_retention_policy_registry() -> Registry[RetentionPolicy]:
    """Return a registry populated with the built-in retention policies."""
    registry: Registry[RetentionPolicy] = Registry("retention-policy")
    for policy in default_policies():
        registry.register(str(policy.id), policy)
    return registry
