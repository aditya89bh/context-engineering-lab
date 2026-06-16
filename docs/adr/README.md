# Architecture decision records

This directory records the significant architectural decisions made in this
repository, using lightweight ADRs in the style of Michael Nygard.

An ADR captures a single decision: the context that forced it, the options
considered, the choice made, and the consequences accepted. ADRs are immutable
once accepted — if a decision changes, a new ADR supersedes the old one rather
than editing history.

## Why ADRs

Research code accumulates decisions that are invisible later: why seeding works
the way it does, why experiments are protocols rather than scripts, why a
dependency was kept out of the core. Without a record, these are re-litigated or,
worse, silently violated. ADRs make the reasoning durable.

## Status values

- **Proposed** — under discussion.
- **Accepted** — in effect.
- **Superseded by ADR-NNNN** — replaced by a later decision.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-experiment-protocol-as-core-abstraction.md) | Experiments are protocols, not scripts | Accepted |
| [0003](0003-deterministic-seeding.md) | Reproducibility via explicit deterministic seeding | Accepted |

## Writing a new ADR

Copy the structure of an existing record. Number it sequentially. Keep it short:
if it takes more than a page, the decision is probably several decisions.
