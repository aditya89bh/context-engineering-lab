# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
