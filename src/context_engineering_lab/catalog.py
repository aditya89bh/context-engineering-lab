"""Built-in catalog.

Builds registries populated with the strategies and benchmarks that ship with
the package. Registration is explicit (no import-time side effects or plugin
discovery) so the available entries are easy to reason about.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.selection_presets import all_selection_presets
from context_engineering_lab.benchmarks.smoke import SmokeBenchmark
from context_engineering_lab.core.benchmark import Benchmark
from context_engineering_lab.core.registry import Registry
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.strategies.keyword_overlap import KeywordOverlapSelection
from context_engineering_lab.strategies.oracle import OracleSelection
from context_engineering_lab.strategies.positional import (
    FirstNSelection,
    LastNSelection,
)
from context_engineering_lab.strategies.random_selection import RandomSelection
from context_engineering_lab.strategies.recency import RecencySelection


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
    )
    for strategy in strategies:
        registry.register(str(strategy.id), strategy)
    return registry


def build_benchmark_registry() -> Registry[Benchmark]:
    """Return a registry populated with the built-in benchmarks."""
    registry: Registry[Benchmark] = Registry("benchmark")
    benchmarks: tuple[Benchmark, ...] = (SmokeBenchmark(), *all_selection_presets())
    for benchmark in benchmarks:
        registry.register(str(benchmark.id), benchmark)
    return registry
