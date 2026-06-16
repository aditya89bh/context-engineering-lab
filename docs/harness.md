# The harness

Phase 1 turns the Phase 0 design into running infrastructure. This document is a
map of the core abstractions and how an experiment flows through them. It
describes plumbing, not findings.

## Core abstractions

| Concept | Type | Role |
| --- | --- | --- |
| Item | `core.item.Item` | A unit of information with content, length, optional timestamp |
| Budget | `core.budget.Budget` / `BudgetUnit` | A positive limit in items, tokens, or characters |
| Context | `core.context.Context` | A budget-bounded set of items; rejects silent overflow |
| Task | `core.task.Task` | What the consumer must do (a query plus open payload) |
| Strategy | `core.strategy.Strategy` | Turns candidates + task + budget into a context |
| Case / Benchmark | `core.benchmark` | A scored instance / a task + generator + scorer |
| Experiment | `core.experiment.Experiment` | A reproducible config: benchmark, strategies, seeds, budgets |
| Runner | `core.runner.ExperimentRunner` | Executes an experiment, aggregates metrics |
| Results | `core.results` | `MetricValue`, `StrategyRunResult`, `ExperimentResult` |
| Metadata | `core.metadata.RunMetadata` | Deterministic provenance, including a content-addressed `RunId` |
| Registry | `core.registry.Registry` | Looks up strategies and benchmarks by id |

## How a run flows

1. An `Experiment` names a benchmark, one or more strategies, seeds, and budgets.
2. For each strategy, seed, and budget, the runner asks the benchmark to
   `generate(seed)` cases, runs the strategy's `select(...)` per case, and scores
   the resulting context with the benchmark's `evaluate(...)`.
3. Per-case scores are aggregated (mean and standard deviation) into
   `MetricValue`s, grouped into a `StrategyRunResult`, and bundled with
   deterministic `RunMetadata` into an `ExperimentResult`.
4. `reporting.persistence` writes the result to JSON.

## Reproducibility

Randomness derives from the seed via `seeding.derive_seed`
([ADR-0003](adr/0003-deterministic-seeding.md)). The `RunId` is a BLAKE2b digest
of the experiment configuration, so identical configs produce identical ids and
reruns are detectable. Environment details (Python version, platform) are
recorded but excluded from the id, which identifies the configuration rather than
the machine.

## CLI

```bash
context-lab list                                   # registered strategies/benchmarks
context-lab run-smoke --output artifacts/smoke-result.json
context-lab run-smoke --seeds 1 2 3 --output artifacts/smoke.json
```

`run-smoke` exercises the recency baseline on the harness smoke benchmark and
writes a JSON artifact. Artifacts under `artifacts/` are git-ignored.

## What this is not

The included `harness-smoke` benchmark and `recency` baseline exist to prove the
plumbing works. They are not research instruments, and their numbers carry no
conclusions. Real benchmarks and strategies arrive in later phases per the
[roadmap](roadmap.md).
