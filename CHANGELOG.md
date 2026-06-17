# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Phase 6 — Attention allocation.**
  - An attention interface (`core.attention`): a `Source` grouping, an
    `AttentionAllocator` protocol, the `AllocationDecision` / `AllocationStats` /
    `AllocationResult` records, an observable `source_quality` key, a
    `group_sources` helper, and an `AllocatorStrategy` adapter that runs
    allocators through the existing experiment runner. Kept minimal — no
    scheduler or event loop.
  - Six allocators (`attention`): `uniform-allocation`, `proportional-allocation`
    (by size), `salience-allocation` (by source salience), `adaptive-allocation`
    (quality-led, capacity-aware), `winner-take-most` (concentrates on the top
    source), and an `oracle-allocation` ceiling (reads ground-truth signal
    counts; documented as not deployable).
  - The `attention-source-allocation` synthetic benchmark whose sources mix
    signal and distractors and expose an observable quality score and salience
    profile, with knobs for source count, source size, quality imbalance, signal
    concentration, and an optional large/salient/low-quality trap source.
  - Three benchmark presets: `balanced-sources`, `concentrated-signal`,
    `noisy-dominant-source`.
  - Allocation metrics (`core.attention_metrics`): `allocation_efficiency`,
    `signal_capture_rate`, `wasted_attention_rate`, and `source_coverage`
    (reusing `budget_utilization`), with formulas in `docs/metrics.md`.
  - Four reproducible experiments (`attention-balanced`,
    `attention-concentrated`, `attention-noisy-dominant`,
    `attention-budget-sweep`) and a Markdown report.
  - A `context-lab run-phase6` command and an attention-allocator registry; the
    no-network/LLM guard test now also covers the attention package.
  - Documentation: `docs/attention-benchmarks.md`, `docs/phase-6-summary.md`,
    allocation metric definitions, a Phase 6 status note on RQ8, and a new RQ17
    (when uniform allocation fails). The roadmap marks Phase 6 complete.

- **Phase 5 — Forgetting and retention.**
  - A retention interface (`core.retention`): a `RetentionPolicy` protocol, the
    `RetentionDecision` / `RetentionStats` / `RetentionResult` records, an
    observable `frequency` accessor key, and a `PolicyStrategy` adapter that runs
    policies through the existing experiment runner. Kept minimal — no store or
    persistence.
  - Six retention policies (`retention`): `retain-all` (ignores the budget;
    reference), `recency-retention`, `frequency-retention`, `salience-retention`,
    a `hybrid-retention` blend of the three, and an `oracle-retention` ceiling
    (reads the ground-truth relevance marker; documented as not deployable).
  - The `retention-utility-preservation` synthetic benchmark mixing useful,
    stale, harmful, and neutral items with deliberately misaligned observable
    signals (harmful items recent and high-frequency, useful items spread across
    time), plus knobs for stale/harmful density, memory growth, utility-signal
    noise, and a retention-budget sweep.
  - Three benchmark presets: `low-noise-retention`, `stale-accumulation`,
    `harmful-memory`.
  - Forgetting metrics (`core.retention_metrics`): `retention_precision`,
    `retention_recall`, `useful_retention_rate`, `harmful_retention_rate`,
    `memory_budget_utilization`, and `forgetting_efficiency`, with formulas in
    `docs/metrics.md`.
  - Four reproducible experiments (`retention-baselines`, `stale-accumulation`,
    `harmful-memory`, `retention-budget-sweep`) and a Markdown report.
  - A `context-lab run-phase5` command and a retention-policy registry; the
    no-network/LLM guard test now also covers the retention package.
  - Documentation: `docs/retention-benchmarks.md`, `docs/phase-5-summary.md`,
    retention metric definitions, a Phase 5 status note on RQ7, and a new RQ16
    (which signal a forgetting policy should trust). The roadmap marks Phase 5
    complete.

- **Phase 4 — Temporal context.**
  - Temporal utilities (`core.temporal`): age and relative-age helpers, an
    observable `salience` accessor, and a latest-timestamp ("now") helper. Kept
    minimal — no event store or clock.
  - Five temporal strategies (`strategies.temporal`): `oldest-first`,
    `sliding-window`, `fixed-window` (anchored at the timeline start),
    `age-weighted` (salience discounted by age decay), and an `oracle-temporal`
    ceiling (reads the ground-truth relevance flag; documented as not
    deployable). `recency` is reused unchanged from Phase 2.
  - The `temporal-context-relevance` synthetic benchmark with configurable
    relevant/distractor age bands, temporal drift, sequence length, and an
    item-budget sweep; items carry an observable salience signal and a hidden
    relevance flag.
  - Three benchmark presets: `recent-signal`, `old-signal`, `drift-heavy`.
  - Temporal metrics (`core.temporal_metrics`): `temporal_relevance`,
    `stale_selection_rate`, `age_of_selected_context`, and `relevant_age_gap`,
    with formulas in `docs/metrics.md`.
  - Four reproducible experiments (`temporal-recent-signal`,
    `temporal-old-signal`, `temporal-drift`, `temporal-budget-sweep`) and a
    Markdown report.
  - A `context-lab run-phase4` command; the no-network/LLM guard test now also
    covers the strategies package and the temporal modules.
  - Documentation: `docs/temporal-benchmarks.md`, `docs/phase-4-summary.md`,
    temporal metric definitions, a Phase 4 status note on RQ5, and a new RQ15
    (fixed windows and age-aware weighting). The roadmap marks Phase 4 complete
    and defers forgetting/retention to a later phase.

- **Phase 3.1 — Review cleanup.**
  - Documented that Phase 3 compressors split token budgets evenly across input
    items — a no-op for the single-document `compression-fact-preservation`
    cases, but a simplification that future multi-item benchmarks may need to
    replace with salience-aware or item-length-aware allocation.
  - Added a deferred design note in `docs/architecture.md` on a possible future
    `CompressionBudgetAllocator`, intentionally not built until multi-item
    compression experiments require it.

- **Phase 3 — Compression.**
  - A compression interface (`core.compression`): the `Compressor` protocol,
    `CompressionStats`/`CompressionResult`, and a `CompressorStrategy` adapter so
    compressors run through the existing experiment runner unchanged.
  - Six deterministic compressors: `no-compression` (over-budget reference),
    `head-truncation`, `tail-truncation`, `keyword-preserving`,
    `sentence-boundary`, and an `oracle-compression` ceiling (reads ground-truth
    fact markers; documented as not deployable). No LLM summarization, no
    external API.
  - Fact-token markers (`benchmarks.facts`) and the
    `compression-fact-preservation` synthetic benchmark with configurable target
    position, distractor density, content length, and token-budget sweep.
  - Three benchmark presets: `easy-compression`, `late-signal-compression`,
    `dense-distractor-compression`.
  - Compression metrics (`core.compression_metrics`): `compression_ratio`,
    `information_retention`, `answer_support_after_compression`,
    `distractor_retention`, and `budget_utilization`, with formulas in
    `docs/metrics.md`.
  - Four reproducible experiments (`compression-baselines-easy`,
    `compression-late-signal`, `compression-distractor-density`,
    `compression-budget-sweep`) and a Markdown report.
  - A `context-lab run-phase3` command and a guard test ensuring no network or
    LLM imports appear in the package modules.
  - Documentation: `docs/compression-benchmarks.md`, `docs/phase-3-summary.md`,
    compression metric definitions, and Phase 3 status notes on RQ4/RQ11 plus a
    new RQ14 (extractive vs. truncation).

- **Phase 2.1 — Review cleanup.**
  - Documented that `RandomSelection` is deterministic and content-addressed: its
    variation across Phase 2 seeds comes primarily from the benchmark-generated
    candidate sets, not from the experiment seed reaching the strategy.
  - Added a deferred design note in `docs/architecture.md` on a possible future
    `RunContext`/`StrategyContext` (carrying seed, run id, benchmark id, case id),
    intentionally not built in Phase 2 to avoid overbuilding.

- **Phase 2 — Selection and Budgets.**
  - Five selection strategies beyond recency: `first-n`, `last-n`, deterministic
    `random`, `keyword-overlap`, and an `oracle` ceiling (reads a privileged
    relevance flag; documented as not deployable). A shared greedy budget-fill
    helper backs them and now backs recency too.
  - The `selection-signal-retrieval` synthetic benchmark generator with
    configurable distractor load, target position, distractor similarity, item
    lengths, and budget sweep — all deterministic from a seed.
  - Three benchmark presets: `easy-selection`, `position-biased-selection`,
    `high-distractor-selection`.
  - A Phase 2 derived metric, `budget_utilization`, alongside the existing
    selection metrics.
  - Four reproducible experiments (`selection-baselines-easy`,
    `selection-position-bias`, `selection-distractor-stress`,
    `selection-budget-sweep`) as factory functions.
  - A Markdown reporting module and a `context-lab run-phase2` command that writes
    per-experiment JSON artifacts plus a summary report.
  - Documentation: `docs/selection-benchmarks.md`, `docs/phase-2-summary.md`, and
    Phase 2 status notes on RQ1/RQ2/RQ9 plus a new RQ13 (target position bias).

- **Phase 1.1 — Review cleanup.**
  - Item metadata now accepts JSON-safe scalar values (`str | int | float | bool
    | None`) instead of strings only, via new `JsonValue`/`Metadata` aliases.
  - The runner validates that each `evaluate` call returns exactly the
    benchmark's `declared_metrics`, raising a `ValueError` that names the
    benchmark id, case id, and any missing/extra metrics.
  - Documented the empty-selection precision convention (undefined formally; the
    smoke benchmark records `0.0` for harness convenience).
  - Added `docs/phase-1-summary.md`.

### Changed

- Hardened result reproducibility expectations around declared metrics (see
  above); no behavior change for conforming benchmarks.

- **Phase 1 — Core abstractions.**
  - Typed primitives: `Item`/`ItemId`, `Budget`/`BudgetUnit`, `Context`, `Task`,
    and identifier wrappers for strategies, benchmarks, experiments, and runs.
  - The `Strategy` and `Benchmark` interfaces (protocols) plus a `Case` model.
  - Selection metric functions (precision, recall, answer support).
  - Result models (`MetricValue`, `StrategyRunResult`, `ExperimentResult`) with
    JSON serialization and deterministic `RunMetadata`/`RunId`.
  - A synchronous `ExperimentRunner` and an `Experiment` configuration model.
  - A typed `Registry` and a built-in catalog.
  - One trivial baseline (recency selection) and one harness smoke benchmark.
  - A `context-lab` CLI (`list`, `run-smoke`) and JSON result persistence.
  - Harness documentation (`docs/harness.md`).

- **Phase 0.1 — Review cleanup.**
  - Research-question catalog (`docs/research-questions.md`) with testable
    questions mapped to the taxonomy.
  - Explicit non-goals (`docs/non-goals.md`).
  - Formal metric definitions and formulas in `docs/metrics.md` (selection
    precision/recall, answer support, budget efficiency, distractor and
    poisoning sensitivity, and AUBPC).
  - README links to the research questions and non-goals.

### Changed

- Marked Phase 0 as complete in the roadmap.

- **Phase 0 — Research design.**
  - Repository thesis, shared definitions, and experiment taxonomy.
  - Benchmark philosophy and metrics framework.
  - Architecture overview and architecture decision records (ADR-0001 to
    ADR-0003).
  - Repository layout, definition of done, and phased roadmap.
  - Reproducibility foundations: deterministic seeding utilities
    (`seed_everything`, `derive_seed`, `temporary_seed`).
  - Engineering toolchain: Ruff, MyPy (strict), pytest with coverage, and a
    GitHub Actions CI pipeline building on Python 3.11 and 3.12.
  - Contribution guidelines, code of conduct, and issue/PR templates.
