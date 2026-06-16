"""Deterministic seeding utilities for reproducible experiments.

Reproducibility is a first-class requirement for this lab (see
``docs/definition-of-done.md``). Every experiment must be able to declare a
single integer seed and derive all of its randomness from it, so that a result
can be regenerated bit-for-bit on another machine.

This module deliberately depends only on the standard library. Optional
numerical backends (e.g. NumPy) are seeded by the experiments that use them,
using :func:`derive_seed` to obtain independent, reproducible sub-seeds.
"""

from __future__ import annotations

import contextlib
import hashlib
import random
from collections.abc import Iterator

__all__ = [
    "DEFAULT_SEED",
    "derive_seed",
    "seed_everything",
    "temporary_seed",
]

#: Project-wide default seed used when an experiment does not specify its own.
DEFAULT_SEED: int = 20_260_101

#: Upper bound (exclusive) for derived seeds; keeps values within a 63-bit range
#: so they remain safe for every common RNG backend.
_SEED_MODULUS: int = 2**63


def seed_everything(seed: int = DEFAULT_SEED) -> int:
    """Seed the standard-library RNG and return the seed used.

    Args:
        seed: The integer seed to apply.

    Returns:
        The seed that was applied, so callers can log it alongside results.
    """
    random.seed(seed)
    return seed


def derive_seed(base_seed: int, *labels: str) -> int:
    """Derive a stable sub-seed from a base seed and one or more labels.

    Unlike the built-in :func:`hash`, this derivation is stable across
    processes and Python versions because it is built on BLAKE2b. Use it to
    give each component of an experiment (data shuffle, model init, sampler,
    ...) an independent yet reproducible stream of randomness.

    Args:
        base_seed: The experiment's root seed.
        *labels: Human-readable labels identifying the sub-stream.

    Returns:
        A non-negative integer seed in ``[0, 2**63)``.
    """
    payload = "::".join((str(base_seed), *labels)).encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).digest()
    return int.from_bytes(digest, "big") % _SEED_MODULUS


@contextlib.contextmanager
def temporary_seed(seed: int) -> Iterator[None]:
    """Temporarily seed the standard-library RNG, restoring prior state on exit.

    This is useful for deterministic sub-computations that must not perturb the
    surrounding random stream.

    Args:
        seed: The seed to apply within the context.

    Yields:
        ``None``. The previous RNG state is restored when the context closes.
    """
    state = random.getstate()
    try:
        random.seed(seed)
        yield
    finally:
        random.setstate(state)
