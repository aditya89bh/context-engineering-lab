"""Experiment configuration.

An :class:`Experiment` binds a question to a concrete, reproducible
configuration: which benchmark, which strategies, which seeds, and which
budgets. It is plain data; the experiment runner turns it into results.
"""

from __future__ import annotations

from dataclasses import dataclass

from context_engineering_lab.core.benchmark import Benchmark
from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.seeding import DEFAULT_SEED


@dataclass(frozen=True, slots=True)
class Experiment:
    """A reproducible experiment configuration.

    Args:
        experiment_id: Stable identifier for the experiment.
        benchmark: The benchmark to evaluate against.
        strategies: The strategies to compare (at least one).
        seeds: Seeds to run over. Defaults to the project-wide default seed.
        budgets: Budgets to sweep. When ``None``, the benchmark's declared
            ``budget_sweep`` is used.
    """

    experiment_id: ExperimentId
    benchmark: Benchmark
    strategies: tuple[Strategy, ...]
    seeds: tuple[int, ...] = (DEFAULT_SEED,)
    budgets: tuple[Budget, ...] | None = None

    def __post_init__(self) -> None:
        if not self.strategies:
            raise ValueError("an experiment needs at least one strategy")
        if not self.seeds:
            raise ValueError("an experiment needs at least one seed")

    def resolved_budgets(self) -> tuple[Budget, ...]:
        """Return the budgets to use, falling back to the benchmark's sweep.

        Raises:
            ValueError: If neither explicit budgets nor a benchmark sweep exist.
        """
        budgets = self.budgets
        if budgets is None:
            budgets = self.benchmark.budget_sweep
        if not budgets:
            raise ValueError(
                "no budgets to run: set Experiment.budgets or a benchmark sweep"
            )
        return tuple(budgets)
