"""context-engineering-lab.

A research-practice package for experiments in salience, compression, temporal
context, and attention: how intelligent systems decide what context to retain,
compress, retrieve, prioritize, and forget.

This module re-exports the core abstractions that experiments are built from:
items, budgets, contexts, tasks, the strategy and benchmark interfaces, the
experiment runner, result models, and the registry. The experimental labs
themselves are introduced in later phases (see ``docs/roadmap.md``).
"""

from __future__ import annotations

from context_engineering_lab.core.benchmark import Benchmark, Case
from context_engineering_lab.core.budget import Budget, BudgetUnit, item_cost
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import (
    BenchmarkId,
    ExperimentId,
    ItemId,
    RunId,
    StrategyId,
)
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.metadata import RunMetadata
from context_engineering_lab.core.registry import Registry
from context_engineering_lab.core.results import (
    ExperimentResult,
    MetricValue,
    StrategyRunResult,
)
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.core.task import Task
from context_engineering_lab.seeding import (
    DEFAULT_SEED,
    derive_seed,
    seed_everything,
    temporary_seed,
)

__all__ = [
    "DEFAULT_SEED",
    "Benchmark",
    "BenchmarkId",
    "Budget",
    "BudgetUnit",
    "Case",
    "Context",
    "Experiment",
    "ExperimentId",
    "ExperimentResult",
    "ExperimentRunner",
    "Item",
    "ItemId",
    "MetricValue",
    "Registry",
    "RunId",
    "RunMetadata",
    "Strategy",
    "StrategyId",
    "StrategyRunResult",
    "Task",
    "__version__",
    "derive_seed",
    "item_cost",
    "seed_everything",
    "temporary_seed",
]

__version__ = "0.0.0"
