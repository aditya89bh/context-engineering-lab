"""A registry of perturbations and small loading helpers.

The registry mirrors the strategy/benchmark catalog pattern: explicit
registration (no plugin discovery), duplicate-id rejection, and sorted listing.
The loading helpers turn a benchmark plus a perturbation (or perturbation id)
into a :class:`~context_engineering_lab.perturbations.base.PerturbedBenchmark`
ready for the ordinary experiment runner.
"""

from __future__ import annotations

from collections.abc import Iterable

from context_engineering_lab.core.benchmark import Benchmark
from context_engineering_lab.core.registry import Registry
from context_engineering_lab.perturbations.base import (
    Perturbation,
    PerturbedBenchmark,
)


def default_perturbations() -> tuple[Perturbation, ...]:
    """Return the built-in perturbations in a stable order.

    Built-ins are added as each perturbation family lands; the tuple is the
    single source of truth for what the catalog and CLI expose.
    """
    return ()


def build_perturbation_registry(
    perturbations: Iterable[Perturbation] | None = None,
) -> Registry[Perturbation]:
    """Return a registry populated with perturbations.

    Args:
        perturbations: The perturbations to register. Defaults to
            :func:`default_perturbations`.

    Returns:
        A registry keyed by each perturbation's id.
    """
    chosen = default_perturbations() if perturbations is None else perturbations
    registry: Registry[Perturbation] = Registry("perturbation")
    for perturbation in chosen:
        registry.register(perturbation.id, perturbation)
    return registry


def load_perturbation(
    perturbation_id: str,
    registry: Registry[Perturbation] | None = None,
) -> Perturbation:
    """Look up a perturbation by id.

    Args:
        perturbation_id: The id to resolve.
        registry: The registry to search. Defaults to the built-in registry.

    Returns:
        The registered perturbation.

    Raises:
        KeyError: If no perturbation is registered under ``perturbation_id``.
    """
    reg = build_perturbation_registry() if registry is None else registry
    return reg.get(perturbation_id)


def perturb(benchmark: Benchmark, perturbation: Perturbation) -> PerturbedBenchmark:
    """Wrap ``benchmark`` so each generated case is stressed by ``perturbation``."""
    return PerturbedBenchmark(benchmark, perturbation)


def perturb_by_id(
    benchmark: Benchmark,
    perturbation_id: str,
    registry: Registry[Perturbation] | None = None,
) -> PerturbedBenchmark:
    """Wrap ``benchmark`` with the perturbation resolved from ``perturbation_id``.

    Args:
        benchmark: The benchmark to stress.
        perturbation_id: The perturbation to resolve and apply.
        registry: The registry to resolve against. Defaults to the built-ins.

    Returns:
        A perturbed benchmark ready for the experiment runner.
    """
    return PerturbedBenchmark(benchmark, load_perturbation(perturbation_id, registry))
