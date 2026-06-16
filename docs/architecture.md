# Architecture

This document describes the intended shape of the system. During Phase 0 only
the reproducibility foundations exist in code; the abstractions below define the
contract that later phases implement. Architectural choices that carry weight are
recorded as [ADRs](adr/).

## Design goals

1. **Strategies are pluggable and comparable.** Adding a new salience scorer or
   compressor must not require touching the harness that evaluates it.
2. **Experiments are declarative and reproducible.** An experiment is a
   configuration plus a protocol, not a bespoke script. The same configuration
   always yields the same result.
3. **Substrate independence.** Core abstractions describe *items*, *budgets*, and
   *operations*, not a specific model or database, so a strategy can be studied
   in isolation.
4. **Measurement is built in.** The harness records metrics, seeds, and
   environment automatically, so a result is never undermined by a missing log.

## Conceptual components

The system is organized as a small number of stable interfaces, each with many
interchangeable implementations.

```
            +-------------------+
            |   Experiment      |   declares: question, config, seed
            |   (protocol)      |
            +---------+---------+
                      |
          +-----------v-----------+
          |       Harness         |   runs protocol, records results
          +-----------+-----------+
                      |
    +-----------------+------------------+
    |                 |                  |
+---v----+      +-----v------+     +-----v------+
| Items  |      | Strategy   |     | Benchmark  |
| & store|      | (operation)|     | (task+data)|
+--------+      +-----+------+     +-----+------+
                      |                  |
                +-----v------+     +-----v------+
                |  Metrics   |<----+ Consumer   |
                +------------+     +------------+
```

- **Item & store** — the data layer: items with content and metadata, plus a
  store that supports retrieval, eviction, and forgetting.
- **Strategy** — a named implementation of one operation (salience, selection,
  compression, temporal weighting, forgetting, allocation). The unit under test.
- **Benchmark** — a task, a data generator or dataset, and a scoring procedure.
- **Consumer** — the process that uses the produced context to perform the task.
- **Harness** — orchestrates a run: applies a strategy under a benchmark across a
  budget sweep and seeds, then emits metrics.
- **Experiment** — the declarative top layer binding a question to a config.

## Key decisions (summarized)

These are recorded in full as ADRs:

- **Experiments are protocols, not scripts** ([ADR-0002](adr/0002-experiment-protocol-as-core-abstraction.md)).
  A shared protocol guarantees every experiment records what it must.
- **Reproducibility via explicit seeding** ([ADR-0003](adr/0003-deterministic-seeding.md)).
  Single root seed, deterministic sub-seed derivation, no hidden randomness.

## Deferred: a strategy run context

**Design note (deferred — do not build yet).** The current strategy interface is
`select(candidates, task, budget) -> Context`. It intentionally does *not* pass
the run's `seed`, `run_id`, `benchmark_id`, or `case_id` to the strategy. A
future interface may introduce a `RunContext` / `StrategyContext` value carrying
those fields, so that, for example, a randomized strategy could seed itself from
the experiment seed rather than content-addressing its own randomness from the
candidate ids (see the `random` determinism note in
[phase-2-summary.md](phase-2-summary.md)).

This is **deliberately deferred** to avoid overbuilding Phase 2. Adding a context
object now would widen the most-implemented interface in the package for a single
present consumer. It should be introduced only when a concrete strategy genuinely
needs run-scoped identity or seeding — at which point it warrants its own ADR.

## Reproducibility model

Every run is defined by `(experiment config, root seed, code version)`. The
harness derives all randomness from the root seed via
`context_engineering_lab.seeding.derive_seed`, records the resolved
configuration and environment, and writes results to a content-addressable
location so reruns are detectable. No experiment is permitted to read wall-clock
time, process IDs, or unseeded randomness as part of its logic.

## Dependency posture

The core stays dependency-light and standard-library-first. Heavy or optional
dependencies (numerical backends, model clients) are confined to the strategies
or benchmarks that need them and are declared as optional extras, never in the
core. This keeps the foundations fast to install and easy to reason about.

## Error handling and logging

- Failures in a single run are isolated and recorded; one failed seed does not
  abort a sweep.
- Logging is structured (key-value) so runs can be aggregated and queried, not
  grepped.
- Configuration errors fail fast and loudly, before any compute is spent.
