"""context-engineering-lab.

A research-practice package for experiments in salience, compression, temporal
context, and attention: how intelligent systems decide what context to retain,
compress, retrieve, prioritize, and forget.

This package is intentionally minimal during Phase 0 (Research Design). It
exposes only the foundations required for reproducible experimentation. The
experimental machinery is introduced in later phases as described in
``docs/roadmap.md``.
"""

from __future__ import annotations

from context_engineering_lab.seeding import (
    DEFAULT_SEED,
    derive_seed,
    seed_everything,
    temporary_seed,
)

__all__ = [
    "DEFAULT_SEED",
    "__version__",
    "derive_seed",
    "seed_everything",
    "temporary_seed",
]

__version__ = "0.0.0"
