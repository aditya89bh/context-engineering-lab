# Repository layout

This document describes where things live and the reasoning behind the layout.
It reflects the repository as built through Phase 11 (release hardening).

## Tree

```
context-engineering-lab/
├── docs/                       # research design, methodology, and per-phase write-ups
│   └── adr/                    # architecture decision records
├── src/
│   └── context_engineering_lab/
│       ├── __init__.py         # public API surface and version
│       ├── py.typed            # PEP 561 marker: the package ships types
│       ├── seeding.py          # deterministic seeding foundations
│       ├── catalog.py          # registries of built-in strategies/benchmarks/...
│       ├── cli.py              # the `context-lab` command-line interface
│       ├── compositions.py     # built-in strategy compositions (Phase 7)
│       ├── core/               # items, budgets, contexts, tasks, interfaces, runner, metrics
│       ├── strategies/         # selection/temporal strategies (positional, recency, ...)
│       ├── compression/        # extractive compressors (Phase 3)
│       ├── retention/          # retention policies (Phase 5)
│       ├── attention/          # attention allocators (Phase 6)
│       ├── benchmarks/         # synthetic + naturalistic benchmark families and presets
│       │   └── naturalistic/   # naturalistic benchmark engine and families (Phase 8)
│       ├── experiments/        # declarative experiment definitions (phase2 … phase10)
│       ├── synthesis/          # cross-benchmark synthesis (Phase 9)
│       ├── perturbations/      # robustness perturbations (Phase 10)
│       └── reporting/          # result persistence and per-phase Markdown reports
├── tests/                      # one test module per source module, plus shared fixtures
├── .github/workflows/          # continuous integration (ci.yml)
├── pyproject.toml              # single source of truth for build + tooling config
├── README.md                  # front door and document index
├── CHANGELOG.md                # human-readable history
├── CONTRIBUTING.md             # how to propose and add work
├── CODE_OF_CONDUCT.md          # community expectations
└── LICENSE
```

Generated experiment outputs (`artifacts/`, `results/`, `runs/`) are git-ignored;
a result is reproduced by rerunning a definition, not by committing a blob.

## Conventions

**`src/` layout.** The package lives under `src/` so that tests run against the
installed package, not the working directory. This catches packaging mistakes
(missing modules, absent `py.typed`) that a flat layout would hide.

**Metrics live beside the abstractions they score.** Rather than a single
`metrics/` package, each metric module sits in `core/` next to the concern it
measures (`metrics.py`, `compression_metrics.py`, `temporal_metrics.py`,
`retention_metrics.py`, `attention_metrics.py`, `interaction_metrics.py`,
`naturalistic_metrics.py`, `robustness_metrics.py`). They are pure functions with
no benchmark or strategy dependencies.

**One package per primitive family.** Strategies, compressors, retention policies,
and attention allocators each get their own package with a small `_common.py` for
shared helpers and one module per implementation, registered explicitly in
`catalog.py` (no plugin discovery or import-time side effects).

**Experiments are data, results are derived.** Experiment *definitions* live in
`experiments/` and are version-controlled and reviewable; experiment *outputs* are
generated artifacts and are git-ignored.

**Tests mirror sources.** `tests/test_<module>.py` corresponds to a source module.
This keeps coverage legible and makes the missing-test gap obvious.

**One config file.** `pyproject.toml` is the single source of truth for build
metadata and every tool (Ruff, MyPy, pytest, coverage). No scattered `.cfg` or
`.ini` files.

**Docs are part of the product.** Because the experiments are the product, their
framing — thesis, taxonomy, metrics, per-phase summaries — is treated as
first-class and lives in `docs/`, reviewed with the same care as code.
