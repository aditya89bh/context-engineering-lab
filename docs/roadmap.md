# Roadmap

This repository is built in phases. Each phase is a coherent unit of work that is
reviewed and approved before the next begins. Phases are not committed to in
advance beyond their stated intent; scope is fixed only when a phase is assigned.

The roadmap describes *direction*, not a contract. Later phases may be reordered
or revised based on what earlier phases reveal — that is the point of doing this
empirically.

## Phase 0 — Research design (complete)

**Goal:** establish the intellectual and engineering foundation.

- Repository thesis, shared definitions, experiment taxonomy.
- Benchmark philosophy and metrics framework.
- Architecture decisions and repository layout.
- Reproducibility foundations in code (deterministic seeding).
- Contribution guidelines, definition of done, and this roadmap.
- Working toolchain: Ruff, MyPy (strict), pytest, build, CI.

A follow-up review pass (Phase 0.1) added the research-question catalog,
explicit non-goals, and formal metric definitions.

**Status:** complete.

## Phase 1 — Core abstractions (complete)

**Goal:** turn the design into typed, testable infrastructure.

- Item, budget, context, and task primitives.
- The strategy and benchmark interfaces, plus the experiment runner.
- Result and metric data structures with JSON serialization and deterministic
  run metadata.
- A registry, one trivial baseline (recency selection), one harness smoke
  benchmark, and a CLI skeleton.

See [harness.md](harness.md) for how these fit together.

**Status:** complete. The lab can run a reproducible experiment end to end; it
does not yet produce research conclusions.

## Phase 2 — Selection and budgets (planned)

**Goal:** answer the first flagship questions about selection.

- Salience scorers and selection strategies.
- Synthetic benchmarks with controllable distractors and signal placement.
- Budget-performance curves: where does cutting context break the task?

## Phase 3 — Compression (planned)

**Goal:** map the safe limits of compression.

- Extractive and abstractive compression strategies.
- Information-retention metrics against uncompressed references.
- The compression-quality frontier.

## Phase 4 — Temporal context and forgetting (planned)

**Goal:** study how time should shape context.

- Temporal decay and staleness detection.
- Forgetting and eviction policies under capacity limits.
- Whether active forgetting beats keeping everything.

## Phase 5 — Attention budget allocation (planned)

**Goal:** study how a fixed budget should be split.

- Uniform vs. salience-proportional vs. knapsack allocation.
- Interaction between allocation and selection.

## Phase 6 — Robustness (planned)

**Goal:** stress strategies that work under benign conditions.

- Distractor and poisoning resistance.
- Distribution shift between tuning and evaluation.

## Working agreement

- Only the currently assigned phase is executed.
- Each phase ends with passing validation (`pytest`, `ruff check .`, `mypy`,
  `python -m build`) and a pushed branch.
- Work stops at the end of a phase and awaits review before continuing.
