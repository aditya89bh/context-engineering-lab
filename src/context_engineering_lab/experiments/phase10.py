"""Phase 10 experiment configurations: robustness under perturbation.

Each :class:`RobustnessSpec` pairs one existing benchmark and a curated strategy
lineup with one or more perturbations. From a spec we build a *baseline*
experiment (the unperturbed benchmark) and one *perturbed* experiment per
perturbation (the benchmark wrapped by
:class:`~context_engineering_lab.perturbations.base.PerturbedBenchmark`). Comparing
the perturbed runs against the baseline isolates how much each strategy degrades
under each stressor.

No new benchmark family or strategy is introduced: the specs reuse the Phase 8
naturalistic presets and the Phase 8 curated lineups verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass

from context_engineering_lab.benchmarks.naturalistic.presets import (
    email_old_signal,
    memory_log_noisy,
    revision_current_truth,
    support_stale_fix,
)
from context_engineering_lab.core.benchmark import Benchmark
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.experiments.phase8 import (
    curated_strategies,
    source_curated_strategies,
)
from context_engineering_lab.perturbations.registry import perturb_by_id

#: Seeds every Phase 10 experiment runs over.
PHASE10_SEEDS: tuple[int, ...] = (1, 2, 3)


@dataclass(frozen=True, slots=True)
class RobustnessSpec:
    """A stress group: a benchmark, a lineup, and the perturbations to apply.

    Args:
        group: Stable name for the stress group (e.g. ``distractor-stress``).
        benchmark: The unperturbed benchmark to stress.
        strategies: The curated strategy lineup to compare.
        perturbations: Ids of the perturbations to apply, each producing one
            perturbed experiment.
    """

    group: str
    benchmark: Benchmark
    strategies: tuple[Strategy, ...]
    perturbations: tuple[str, ...]

    def baseline_name(self) -> str:
        """Experiment id for this group's unperturbed baseline run."""
        return f"{self.group}-baseline"

    def perturbed_name(self, perturbation_id: str) -> str:
        """Experiment id for this group's run under ``perturbation_id``."""
        return f"{self.group}-{perturbation_id}"


def robustness_specs() -> tuple[RobustnessSpec, ...]:
    """Return the Phase 10 stress groups in a stable order."""
    return (
        RobustnessSpec(
            group="distractor-stress",
            benchmark=email_old_signal(),
            strategies=curated_strategies(),
            perturbations=("distractor-injection",),
        ),
        RobustnessSpec(
            group="contradiction-stress",
            benchmark=revision_current_truth(),
            strategies=curated_strategies(),
            perturbations=("contradiction-injection",),
        ),
        RobustnessSpec(
            group="stale-amplification",
            benchmark=memory_log_noisy(),
            strategies=curated_strategies(),
            perturbations=("stale-amplification",),
        ),
        RobustnessSpec(
            group="corruption-stress",
            benchmark=support_stale_fix(),
            strategies=source_curated_strategies(),
            perturbations=("source-quality-corruption", "salience-corruption"),
        ),
    )


def _spec_experiments(spec: RobustnessSpec) -> dict[str, Experiment]:
    experiments: dict[str, Experiment] = {
        spec.baseline_name(): Experiment(
            experiment_id=ExperimentId(spec.baseline_name()),
            benchmark=spec.benchmark,
            strategies=spec.strategies,
            seeds=PHASE10_SEEDS,
        )
    }
    for perturbation_id in spec.perturbations:
        name = spec.perturbed_name(perturbation_id)
        experiments[name] = Experiment(
            experiment_id=ExperimentId(name),
            benchmark=perturb_by_id(spec.benchmark, perturbation_id),
            strategies=spec.strategies,
            seeds=PHASE10_SEEDS,
        )
    return experiments


def robustness_experiments() -> dict[str, Experiment]:
    """Return all Phase 10 baseline and perturbed experiments by id."""
    experiments: dict[str, Experiment] = {}
    for spec in robustness_specs():
        experiments.update(_spec_experiments(spec))
    return experiments
