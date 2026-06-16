# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
