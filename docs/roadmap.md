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

## Phase 5 — Forgetting and retention (complete)

**Goal:** study forgetting as a policy — what to keep and what to discard under a
memory budget, now that temporal effects are mapped.

- Retention policies spanning a `retain-all` reference, single-signal policies
  (recency, frequency, salience), a `hybrid` blend of the three, and an
  `oracle-retention` ceiling that reads ground-truth utility.
- The synthetic `retention-utility-preservation` benchmark with three presets
  (`low-noise-retention`, `stale-accumulation`, `harmful-memory`) whose items mix
  useful, stale, harmful, and neutral information with deliberately misaligned
  observable signals, and forgetting metrics (retention precision/recall, useful
  and harmful retention rates, memory budget utilization, forgetting efficiency).
- Retention, harmful-retention, and budget-performance tables and a Markdown
  report via `context-lab run-phase5`.

See [phase-5-summary.md](phase-5-summary.md) and
[retention-benchmarks.md](retention-benchmarks.md).

**Status:** complete. Studies forgetting as a one-shot retention *policy* — no
memory store, persistence, or eviction schedule. Forgetting is treated as distinct
from temporal relevance (old can be useful; recent can be harmful). Produces
controlled, benchmark-specific observations only — not general claims about memory
systems; `oracle-retention` is an upper bound, not deployable.

## Phase 6 — Attention allocation (complete)

**Goal:** study how a fixed budget should be split across competing sources.

- Allocation strategies spanning a `uniform` baseline, size-`proportional`,
  `salience`-proportional, a capacity-aware `adaptive` policy, a
  `winner-take-most` concentrator, and an `oracle-allocation` ceiling that reads
  ground-truth signal counts.
- The synthetic `attention-source-allocation` benchmark with three presets
  (`balanced-sources`, `concentrated-signal`, `noisy-dominant-source`) whose
  sources mix signal and distractors and expose an observable quality score and
  salience profile, and allocation metrics (allocation efficiency, signal capture
  rate, wasted attention rate, source coverage, budget utilization).
- Signal-capture, wasted-attention, and budget-performance tables and a Markdown
  report via `context-lab run-phase6`.

See [phase-6-summary.md](phase-6-summary.md) and
[attention-benchmarks.md](attention-benchmarks.md).

**Status:** complete. Studies allocation as a one-shot budget *split* across
sources before selection — no scheduler, agent loop, or event system. Allocation
is treated as distinct from selection (the inner fill is identical across
allocators). Produces controlled, benchmark-specific observations only — not
general claims about attention mechanisms; `oracle-allocation` is an upper bound,
not deployable.

## Phase 7 — Interaction effects (complete)

**Goal:** study how the Phase 2-6 primitives interact when composed, rather than
inventing new primitives.

- A small composition layer (`core.composition`): `PipelineStep`,
  `StrategyComposition`, and `CompositionResult` that chain existing strategies
  into a linear pipeline — itself a `Strategy`, so it runs through the existing
  runner. No workflow engine or DAG.
- Built-in compositions reusing existing primitives (`compositions`):
  `temporal->selection`, `attention->selection`, `retention->attention`,
  `temporal->retention`, `retention->selection`, two compression-ending pipelines,
  and an `oracle-pipeline` ceiling.
- The synthetic `interaction-context-pipeline` benchmark with three presets
  (`balanced-interaction`, `memory-pressure`, `noisy-context`) whose cases mix
  relevant, harmful, stale, and distractor items across sources and a timeline,
  and interaction metrics (`pipeline_efficiency`, plus the comparative
  `interaction_gain`, `degradation_rate`, `compensation_effect`).
- Primitive-only baselines and composed pipelines, recall / harmful-retention /
  interaction-metric tables, and a Markdown report via `context-lab run-phase7`.

See [phase-7-summary.md](phase-7-summary.md) and
[interaction-benchmarks.md](interaction-benchmarks.md).

**Status:** complete. Composes existing primitives only — no new primitive
algorithm, scheduler, agent, or planner. Produces controlled, benchmark-specific
observations about *specific compositions* only — not general claims about
context systems; `oracle-pipeline` is an upper bound, not deployable.

## Phase 8 — Robustness (planned)

**Goal:** stress strategies that work under benign conditions.

- Distractor and poisoning resistance.
- Distribution shift between tuning and evaluation.

## Working agreement

- Only the currently assigned phase is executed.
- Each phase ends with passing validation (`pytest`, `ruff check .`, `mypy`,
  `python -m build`) and a pushed branch.
- Work stops at the end of a phase and awaits review before continuing.
