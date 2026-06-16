# ADR-0003: Reproducibility via explicit deterministic seeding

- **Status:** Accepted
- **Date:** 2026-06-16

## Context

A result that cannot be regenerated is an anecdote. Randomness enters experiments
from many places — data shuffling, model initialization, sampling, distractor
placement — and if any of it is unseeded or seeded inconsistently, results drift
between runs and machines. Python's built-in `hash` is also salted per process by
default, so any derivation built on it is silently non-reproducible.

## Decision

All randomness in an experiment derives from a single integer **root seed**.
Independent random streams are obtained with
`context_engineering_lab.seeding.derive_seed`, which derives stable sub-seeds
from the root seed and human-readable labels using BLAKE2b (stable across
processes and Python versions). The standard-library RNG is seeded through
`seed_everything`, and scoped sub-computations use `temporary_seed` to avoid
perturbing the surrounding stream.

Experiments must not consume entropy from wall-clock time, process IDs,
unseeded RNGs, or the salted built-in `hash` as part of their logic.

## Consequences

- A run is fully defined by `(config, root seed, code version)` and can be
  regenerated bit-for-bit.
- Each experiment component gets an independent, reproducible stream, avoiding
  accidental correlation between, say, the data shuffle and model init.
- The constraint is mildly restrictive: code that needs nondeterminism (e.g.
  wall-clock benchmarking of latency) must isolate it from result-determining
  logic and record it as a measurement, not an input.
- Optional numerical backends (e.g. NumPy) are seeded by the strategies that use
  them, using `derive_seed`, keeping the core dependency-light.
