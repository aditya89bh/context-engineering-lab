"""Robustness perturbations (Phase 10).

Phase 10 adds no new primitive, strategy, or benchmark family. It *stress-tests*
the existing benchmarks by transforming the cases they generate — injecting
distractors, contradictions, or amplified stale information, or corrupting the
observable source/salience signals — and then measuring how much each existing
strategy degrades relative to the unperturbed baseline.

A :class:`~context_engineering_lab.perturbations.base.Perturbation` rewrites a
:class:`~context_engineering_lab.core.benchmark.Case`; a
:class:`~context_engineering_lab.perturbations.base.PerturbedBenchmark` wraps an
existing benchmark so a perturbed run flows through the ordinary experiment
runner unchanged. Nothing here reads real data, calls a network, or uses an LLM.
See ``docs/robustness-benchmarks.md``.
"""

from __future__ import annotations
