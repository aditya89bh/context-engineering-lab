# Repository layout

This document describes where things live and the reasoning behind the layout.
Some directories below are introduced in later phases; they are listed here so
the intended structure is clear from the start. The current state of the tree
reflects Phase 0.

## Current tree (Phase 0)

```
context-engineering-lab/
├── docs/                     # research design: thesis, taxonomy, metrics, ADRs
│   └── adr/                  # architecture decision records
├── src/
│   └── context_engineering_lab/
│       ├── __init__.py       # public API surface
│       ├── py.typed          # PEP 561 marker: the package ships types
│       └── seeding.py        # reproducibility foundations
├── tests/                    # mirrors src/ ; one test module per source module
├── .github/workflows/        # continuous integration
├── pyproject.toml            # single source of truth for build + tooling config
├── README.md                 # front door and document index
├── CONTRIBUTING.md           # how to propose and add work
├── CODE_OF_CONDUCT.md        # community expectations
├── CHANGELOG.md              # human-readable history
└── LICENSE
```

## Intended tree (later phases)

The structure below is the target the design is built toward. It is documented
here, not scaffolded, in keeping with the phased plan in
[roadmap.md](roadmap.md).

```
src/context_engineering_lab/
├── core/          # items, stores, budgets, the experiment protocol, harness
├── strategies/    # salience, selection, compression, temporal, forgetting, ...
├── benchmarks/    # tasks, generators, datasets, scoring
├── metrics/       # quality, cost, robustness measures and aggregation
└── reporting/     # tables, curves, result serialization

experiments/       # declarative experiment definitions (one per question)
results/           # generated, git-ignored experiment outputs
```

## Conventions

**`src/` layout.** The package lives under `src/` so that tests run against the
installed package, not the working directory. This catches packaging mistakes
(missing modules, absent `py.typed`) that a flat layout would hide.

**Tests mirror sources.** `tests/test_<module>.py` corresponds to
`src/context_engineering_lab/<module>.py`. This keeps coverage legible and makes
the missing-test gap obvious.

**One config file.** `pyproject.toml` is the single source of truth for build
metadata and every tool (Ruff, MyPy, pytest, coverage). No scattered `.cfg` or
`.ini` files.

**Experiments are data, results are derived.** Experiment *definitions* are
version-controlled and reviewable; experiment *outputs* are generated artifacts
and are git-ignored. A result is reproduced by rerunning a definition, not by
committing a blob.

**Docs are part of the product.** Because the experiments are the product, their
framing — thesis, taxonomy, metrics — is treated as first-class and lives in
`docs/`, reviewed with the same care as code.
