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

## Phase 2 — Selection and budgets (complete)

**Goal:** answer the first flagship questions about selection.

- Selection strategies spanning lower bounds (`first-n`, `last-n`, `recency`,
  `random`), a crude content signal (`keyword-overlap`), and an `oracle` ceiling.
- The synthetic `selection-signal-retrieval` benchmark with controllable
  distractor load, target position, and distractor similarity; three presets.
- Budget-performance curves and a Markdown report via `context-lab run-phase2`.

See [phase-2-summary.md](phase-2-summary.md) and
[selection-benchmarks.md](selection-benchmarks.md).

**Status:** complete. Produces controlled, benchmark-specific observations only —
not general claims; `oracle` is an upper bound, not a deployable strategy.

## Phase 3 — Compression (complete)

**Goal:** map the safe limits of compression.

- Deterministic, extractive compression strategies spanning a no-compression
  reference, head/tail truncation, query-aware keyword preservation,
  sentence-boundary extraction, and an `oracle-compression` ceiling. No LLM
  summarization.
- The synthetic `compression-fact-preservation` benchmark with three presets, and
  compression metrics (ratio, information retention, answer support after
  compression, distractor retention, budget utilization).
- Budget-performance / compression-quality tables and a Markdown report via
  `context-lab run-phase3`.

See [phase-3-summary.md](phase-3-summary.md) and
[compression-benchmarks.md](compression-benchmarks.md).

**Status:** complete. Produces controlled, benchmark-specific observations only —
not general claims about compression or summarization; `oracle-compression` is an
upper bound, not deployable. Abstractive/LLM compression is intentionally out of
scope.

## Phase 4 — Temporal context (complete)

**Goal:** study how time should shape what context survives a budget.

- Temporal strategies spanning `recency` (reused), `oldest-first`, sliding and
  fixed windows, an age-aware weighting of an observable salience signal, and an
  `oracle-temporal` ceiling.
- The synthetic `temporal-context-relevance` benchmark with three presets
  (`recent-signal`, `old-signal`, `drift-heavy`) and temporal metrics
  (temporal relevance, stale selection rate, age of selected context, relevant
  age gap).
- Budget-performance and temporal-metric tables and a Markdown report via
  `context-lab run-phase4`.

See [phase-4-summary.md](phase-4-summary.md) and
[temporal-benchmarks.md](temporal-benchmarks.md).

**Status:** complete. Studies temporal *effects* only — no forgetting, eviction,
or retention policy. Produces controlled, benchmark-specific observations only —
not general claims about temporal reasoning; `oracle-temporal` is an upper bound,
not deployable.

## Phase 5 — Forgetting and retention (planned)

**Goal:** study whether discarding helps, now that temporal effects are mapped.

- Forgetting and eviction policies under capacity limits.
- Temporal decay shapes matched to a known drift process.
- Whether active forgetting beats keeping everything.

## Phase 6 — Attention budget allocation (planned)

**Goal:** study how a fixed budget should be split.

- Uniform vs. salience-proportional vs. knapsack allocation.
- Interaction between allocation and selection.

## Phase 7 — Robustness (planned)

**Goal:** stress strategies that work under benign conditions.

- Distractor and poisoning resistance.
- Distribution shift between tuning and evaluation.

## Working agreement

- Only the currently assigned phase is executed.
- Each phase ends with passing validation (`pytest`, `ruff check .`, `mypy`,
  `python -m build`) and a pushed branch.
- Work stops at the end of a phase and awaits review before continuing.
