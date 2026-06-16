# ADR-0002: Experiments are protocols, not scripts

- **Status:** Accepted
- **Date:** 2026-06-16

## Context

The natural way to write an experiment is a standalone script: load some data,
run a strategy, print a number. This is fast to write and almost impossible to
trust. Scripts drift apart, record different things, seed inconsistently, and
make cross-experiment comparison a manual, error-prone exercise. Since the
experiments *are* the product of this lab, their integrity cannot rest on each
author remembering to do the right thing.

## Decision

Experiments will conform to a shared **protocol** (a typed interface) executed by
a common **harness**, rather than being free-form scripts. An experiment
declares its question, configuration, strategies, benchmark, and seed; the
harness is responsible for running the budget sweep, varying seeds, recording the
resolved configuration and environment, and emitting metrics in a uniform shape.

The concrete protocol interface is introduced in a later phase. This ADR fixes
the *principle* so that all experiment code is built around it from the start.

## Consequences

- Every experiment records the same provenance (config, seeds, environment,
  benchmark version) by construction, not by author diligence.
- Results across experiments are directly comparable because they share a shape.
- The cost is up-front design effort and slightly less freedom for one-off
  exploration; throwaway exploration belongs in scratch space, not in the
  experiment catalog.
- The harness becomes a critical, well-tested component, since all results flow
  through it.
