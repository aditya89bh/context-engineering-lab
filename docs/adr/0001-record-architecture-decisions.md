# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-06-16

## Context

This repository is a long-lived research-practice project. Its value depends on
decisions being consistent over time: how experiments are structured, how
reproducibility is enforced, what stays out of the core. In research code these
decisions are easy to make implicitly and impossible to recover later, which
leads to drift and re-litigation.

## Decision

We will keep architecture decision records (ADRs) in `docs/adr/`. Each
significant, hard-to-reverse decision gets a numbered, immutable record
describing context, decision, and consequences. Decisions are changed by adding a
superseding ADR, never by rewriting an existing one.

## Consequences

- Contributors can understand *why* the system is shaped as it is without
  archaeology.
- The cost is small, ongoing discipline: meaningful decisions must be written
  down before they are merged.
- ADRs become part of code review: a change that contradicts an accepted ADR
  must either be rejected or accompanied by a superseding ADR.
