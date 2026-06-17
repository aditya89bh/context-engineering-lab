"""Corruption perturbations: distort observable signals, not ground truth.

Where the injection perturbations *add* items, corruption perturbations *rewrite*
the observable metadata of existing items — the source-quality and salience
signals a deployable strategy may read. They never touch ``oracle_relevant`` or
``relevant_ids``/``required_ids``: ground truth (and therefore the oracle ceiling)
is fixed, so any score drop isolates a strategy's reliance on the corrupted signal.

The distortion is *misleading*, not merely noisy: a corrupted signal is pushed
toward the wrong value (down on truly-relevant items, up on irrelevant ones),
scaled by ``intensity``, with a small ``intensity``-scaled jitter. This guarantees
a clear, reproducible robustness signal rather than an averaging-out of noise.
"""

from __future__ import annotations

import random
from dataclasses import replace

from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY
from context_engineering_lab.core.benchmark import Case
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.json_types import JsonValue
from context_engineering_lab.core.temporal import SALIENCE_KEY
from context_engineering_lab.perturbations.base import (
    BasePerturbation,
    PerturbationConfig,
    PerturbationResult,
)
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _distort(
    value: float, *, relevant: bool, intensity: float, rng: random.Random
) -> float:
    """Push ``value`` toward its misleading extreme, scaled by ``intensity``.

    Relevant items are pulled toward ``0.0`` and irrelevant items toward ``1.0``,
    so the signal points away from the truth. A small jitter (also scaled by
    ``intensity``) models residual noise.
    """
    target = 0.0 if relevant else 1.0
    pulled = value + (target - value) * intensity
    jitter = rng.uniform(-0.05, 0.05) * intensity
    return _clamp(pulled + jitter)


def _with_metadata(item: Item, key: str, value: JsonValue) -> Item:
    metadata = dict(item.metadata)
    metadata[key] = value
    return replace(item, metadata=metadata)


def _corrupt_signal(
    case: Case, key: str, intensity: float, rng: random.Random, perturbation_id: str
) -> PerturbationResult:
    """Rewrite ``key`` on every candidate that carries it, distorting it."""
    rewritten: list[Item] = []
    modified = 0
    for item in case.candidates:
        raw = item.metadata.get(key)
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            relevant = bool(item.metadata.get(ORACLE_RELEVANCE_KEY))
            new_value = _distort(
                float(raw), relevant=relevant, intensity=intensity, rng=rng
            )
            rewritten.append(_with_metadata(item, key, new_value))
            modified += 1
        else:
            rewritten.append(item)
    new_case = Case(
        case_id=case.case_id,
        task=case.task,
        candidates=tuple(rewritten),
        relevant_ids=case.relevant_ids,
        required_ids=case.required_ids,
    )
    return PerturbationResult(
        perturbation_id=perturbation_id,
        case=new_case,
        items_added=0,
        items_modified=modified,
    )


class SourceQualityCorruption(BasePerturbation):
    """Distort the ``source_quality`` signal on items that carry it.

    Models noisy source scores and distorted quality metadata: a relevant item's
    quality is pulled down and an irrelevant item's up, so a quality-aware
    attention allocator is misled while content- and ground-truth-based selectors
    are untouched.
    """

    def apply(self, case: Case, rng: random.Random) -> PerturbationResult:
        """Corrupt the source-quality signal across the case's candidates."""
        return _corrupt_signal(
            case, SOURCE_QUALITY_KEY, self._config.intensity, rng, self.id
        )


def source_quality_corruption(intensity: float = 1.0) -> SourceQualityCorruption:
    """Return the default source-quality corruption perturbation."""
    return SourceQualityCorruption(
        PerturbationConfig(
            perturbation_id="source-quality-corruption", intensity=intensity
        )
    )


class SalienceCorruption(BasePerturbation):
    """Distort the ``salience`` signal on items that carry it.

    Models misleading salience and signal dilution: a relevant item's salience is
    pulled down and an irrelevant item's up, so a salience-aware retention policy
    or attention allocator is misled while content- and ground-truth-based
    selectors are untouched.
    """

    def apply(self, case: Case, rng: random.Random) -> PerturbationResult:
        """Corrupt the salience signal across the case's candidates."""
        return _corrupt_signal(
            case, SALIENCE_KEY, self._config.intensity, rng, self.id
        )


def salience_corruption(intensity: float = 1.0) -> SalienceCorruption:
    """Return the default salience corruption perturbation."""
    return SalienceCorruption(
        PerturbationConfig(perturbation_id="salience-corruption", intensity=intensity)
    )
