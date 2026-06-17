# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Phase 9 — Cross-benchmark synthesis.**
  - A `synthesis` package that reads the Phase 2-8 result artifacts and
    synthesises them, adding no new strategy, benchmark, metric, or algorithm and
    touching no network or LLM:
    - `synthesis.loading` loads artifacts with explicit schema validation and a
      single `ArtifactError` for missing files, malformed JSON, or bad structure.
    - `synthesis.collection` discovers artifacts recursively in sorted order and
      groups loaded results by benchmark or strategy.
    - `synthesis.aggregation` collapses per-seed metric values into one
      `AggregatedResult` cell per `(benchmark, strategy, metric, budget)`
      (`BenchmarkAggregate`, `StrategyAggregate`, `Aggregation`), with a
      metric-orientation table (higher/lower/neutral) and per-benchmark
      primary-metric selection.
    - `synthesis.profiles` builds `StrategyProfile`s (with `StrengthRecord`,
      `WeaknessRecord`, `BudgetScore`): strongest/weakest benchmarks, best/worst
      budgets, and mean oracle distance.
    - `synthesis.dominance` compares strategies pairwise on shared, oriented
      cells (wins/losses/ties), totals each strategy's record, and computes the
      non-dominated (Pareto) frontier.
    - `synthesis.oracle_gap` computes per-cell `OracleGap`s and per-strategy
      `OracleSummary`s, including an oracle-normalized score on the primary metric.
    - `synthesis.failure` flags `BUDGET_FAILURE`, `BENCHMARK_FAILURE`, and
      `METRIC_DEGRADATION` (`FailureMode`, `FailureObservation`); oracles are
      never flagged.
    - `synthesis.stability` computes seed variance, budget sensitivity, and
      ranking volatility (a normalized Kendall-tau distance across budgets).
  - A deterministic Phase 9 Markdown report (`reporting.phase9_report`) with
    provenance, profile, dominance, oracle-gap, failure, and stability tables and
    explicit limitations.
  - A `context-lab run-phase9` command (`experiments.phase9.all_phase_experiments`)
    that re-runs the Phase 2-8 suites, writes their JSON artifacts, and emits the
    synthesis report.
  - The no-network/LLM guard now also covers the `synthesis` modules; tests put
    the `tests` directory on the pytest path for shared synthesis fixtures.
  - Documentation: `docs/synthesis.md`, `docs/phase-9-summary.md`, a new RQ20
    (which strategies dominate, and where do they fail), and a roadmap that marks
    Phase 9 complete and renumbers robustness to Phase 10.

- **Phase 8 — Naturalistic context benchmarks.**
  - Lightweight record helpers (`benchmarks.naturalistic.records`):
    `MessageLikeRecord`, `MeetingNoteRecord`, `TicketRecord`, `RevisionRecord`,
    and `MemoryRecord`, each converting cleanly into a core `Item`, plus a shared
    `NaturalisticBenchmark` engine that centralises deterministic generation and a
    single scoring routine reporting only each family's declared metrics.
  - Five deterministic, fully synthetic benchmark families shaped like real
    context sources: `email-thread-context` (old relevant email under recent
    chatter), `meeting-notes-context` (current decision among superseded notes),
    `support-ticket-context` (working fix among stale/harmful/noisy incidents,
    source-based), `document-revision-context` (current vs superseded facts), and
    `memory-log-context` (useful vs stale/harmful/neutral memories). Each record
    carries ground-truth flags and misaligned observable signals (salience,
    frequency, and — for support — source quality), with query terms embedded at
    full/partial/none overlap.
  - Six presets: `email-old-signal`, `email-conflict-heavy`,
    `meeting-action-items`, `support-stale-fix`, `revision-current-truth`, and
    `memory-log-noisy`, each declaring id, version, construct, parameters, budget
    sweep, and expected failure modes.
  - Three naturalistic metrics (`core.naturalistic_metrics`):
    `current_truth_support`, `superseded_fact_retention`, and
    `conflict_selection_rate`, with formulas in `docs/metrics.md`.
  - Five reproducible experiments (`naturalistic-email`, `naturalistic-meeting`,
    `naturalistic-support`, `naturalistic-revision`, `naturalistic-memory-log`)
    running a curated lineup of *existing* strategies and compositions (`recency`,
    `keyword-overlap`, `salience-retention`, `temporal->selection`,
    `retention->selection`, `attention->selection` for the source-based family) and
    an `oracle` ceiling — no new algorithm — over seeds (1, 2, 3) and multiple
    budgets, plus a Markdown report adapting to each family's metric set.
  - A `context-lab run-phase8` command; the naturalistic presets are registered in
    the benchmark catalog. The no-network/LLM guard now also covers the
    naturalistic modules and asserts the package ships no data fixtures.
  - Documentation: `docs/naturalistic-benchmarks.md`, `docs/phase-8-summary.md`,
    naturalistic metric definitions, and a new RQ19 (do strategies remain useful on
    realistic-shaped context). The roadmap marks Phase 8 complete and renumbers
    robustness to Phase 9.

- **Phase 7 — Interaction effects.**
  - A composition layer (`core.composition`): `PipelineStep`, `StepRecord`,
    `CompositionResult`, and `StrategyComposition` — a linear chain of existing
    strategies that is itself a `Strategy` and runs through the existing
    experiment runner. Non-final stages receive a widened budget; only the final
    stage enforces the real budget. Kept minimal — no workflow engine or DAG.
  - Built-in compositions (`compositions`) reusing existing primitives:
    `temporal->selection`, `attention->selection`, `retention->attention`,
    `temporal->retention`, `retention->selection`, the token-budget
    `selection->compression` and `retention->compression`, and an
    `oracle-pipeline` ceiling (reads ground-truth relevance; documented as not
    deployable). No new primitive algorithm is introduced.
  - The `interaction-context-pipeline` synthetic benchmark whose cases mix
    relevant, harmful, stale, and distractor items across sources and a fixed
    timeline, with deliberately misaligned signals (harmful items carry the query
    terms and are salient/recent but rarely corroborated), plus knobs for source
    count, source imbalance, stale/harmful/distractor density, signal
    concentration, and budget pressure.
  - Three benchmark presets: `balanced-interaction`, `memory-pressure`,
    `noisy-context`.
  - Interaction metrics (`core.interaction_metrics`): a per-case
    `pipeline_efficiency`, plus the comparative `interaction_gain`,
    `degradation_rate`, and `compensation_effect`, with formulas in
    `docs/metrics.md`.
  - Four reproducible experiments (`interaction-balanced`,
    `interaction-memory-pressure`, `interaction-noisy-context`,
    `interaction-budget-sweep`) comparing primitive-only baselines against
    composed pipelines, and a Markdown report with recall, harmful-retention, and
    interaction-metric tables.
  - A `context-lab run-phase7` command and a composition registry; the
    no-network/LLM guard test now also covers the composition modules.
  - Documentation: `docs/interaction-benchmarks.md`, `docs/phase-7-summary.md`,
    interaction metric definitions, a new RQ18 (how primitives interact when
    composed). The roadmap marks Phase 7 complete and renumbers robustness to
    Phase 8.

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
