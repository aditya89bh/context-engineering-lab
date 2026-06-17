"""Phase 9 experiment collection.

Phase 9 defines no new experiment. It re-runs the Phase 2-8 suites so their
artifacts can be synthesised together. ``all_phase_experiments`` merges every
prior suite into one mapping, prefixing each name with its phase so artifact
filenames never collide.
"""

from __future__ import annotations

from collections.abc import Callable

from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.experiments.phase2 import phase2_experiments
from context_engineering_lab.experiments.phase3 import phase3_experiments
from context_engineering_lab.experiments.phase4 import phase4_experiments
from context_engineering_lab.experiments.phase5 import phase5_experiments
from context_engineering_lab.experiments.phase6 import phase6_experiments
from context_engineering_lab.experiments.phase7 import phase7_experiments
from context_engineering_lab.experiments.phase8 import phase8_experiments

_SUITES: tuple[tuple[str, Callable[[], dict[str, Experiment]]], ...] = (
    ("phase2", phase2_experiments),
    ("phase3", phase3_experiments),
    ("phase4", phase4_experiments),
    ("phase5", phase5_experiments),
    ("phase6", phase6_experiments),
    ("phase7", phase7_experiments),
    ("phase8", phase8_experiments),
)


def all_phase_experiments() -> dict[str, Experiment]:
    """Merge every Phase 2-8 experiment into one phase-prefixed mapping.

    Returns:
        A dict from ``"<phase>-<name>"`` to its :class:`Experiment`, ordered by
        phase then by the suite's own order.
    """
    merged: dict[str, Experiment] = {}
    for phase, factory in _SUITES:
        for name, experiment in factory().items():
            merged[f"{phase}-{name}"] = experiment
    return merged
