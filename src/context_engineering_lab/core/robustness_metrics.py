"""Robustness metrics (Phase 10).

Simple, explicit functions comparing a strategy's score on an unperturbed
*baseline* run to its score on a *perturbed* run. All functions operate on
*oriented* values where higher is better: orient cost metrics (negate them) with
:func:`context_engineering_lab.synthesis.aggregation.direction` before calling
these, so a drop always means "got worse".

* :func:`degradation` — the oriented drop ``baseline - perturbed`` (positive means
  the perturbation hurt; negative means it helped).
* :func:`robustness_score` — the fraction of baseline performance retained, in
  ``[0.0, 1.0]`` (``1.0`` means no degradation).
* :func:`degradation_under_noise` / :func:`degradation_under_conflict` — named
  aliases of :func:`degradation` for distractor/noise and contradiction/conflict
  perturbations respectively, so a caller can label the stressor explicitly.
"""

from __future__ import annotations


def degradation(baseline: float, perturbed: float) -> float:
    """Return the oriented drop from ``baseline`` to ``perturbed``.

    Args:
        baseline: The oriented (higher-is-better) score without perturbation.
        perturbed: The oriented score under perturbation.

    Returns:
        ``baseline - perturbed``. Positive means the perturbation reduced
        performance; ``0.0`` means it was unaffected; negative means it improved.
    """
    return baseline - perturbed


def degradation_under_noise(baseline: float, perturbed: float) -> float:
    """Oriented drop attributable to noise/distractor perturbations.

    Alias of :func:`degradation`; named so reports can attribute the drop to a
    distractor-style stressor.
    """
    return degradation(baseline, perturbed)


def degradation_under_conflict(baseline: float, perturbed: float) -> float:
    """Oriented drop attributable to contradiction/conflict perturbations.

    Alias of :func:`degradation`; named so reports can attribute the drop to a
    contradiction-style stressor.
    """
    return degradation(baseline, perturbed)


def robustness_score(baseline: float, perturbed: float) -> float:
    """Return the fraction of baseline performance retained, in ``[0.0, 1.0]``.

    Defined on oriented (higher-is-better) values as
    ``clamp(perturbed / baseline, 0, 1)``. When the baseline is non-positive the
    ratio is undefined, so the result is ``1.0`` if the perturbed score is at
    least the baseline (no degradation) and ``0.0`` otherwise.

    Args:
        baseline: The oriented score without perturbation.
        perturbed: The oriented score under perturbation.

    Returns:
        ``1.0`` when fully robust, decreasing toward ``0.0`` as the perturbed
        score falls relative to the baseline.
    """
    if baseline <= 0.0:
        return 1.0 if perturbed >= baseline else 0.0
    return max(0.0, min(1.0, perturbed / baseline))
