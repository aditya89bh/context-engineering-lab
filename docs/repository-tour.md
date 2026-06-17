# Repository tour

A guided walk for a new contributor. It follows the path data takes through the
lab, so by the end you can find any piece and add your own. Pair it with
[repository-layout.md](repository-layout.md) (where things live) and
[project-summary.md](project-summary.md) (what exists).

## Start here

```bash
git clone https://github.com/aditya89bh/context-engineering-lab
cd context-engineering-lab
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
context-lab list          # the catalog: every registered component
context-lab run-phase2 --output artifacts/phase2
sed -n '1,40p' artifacts/phase2/summary.md
```

If `list` runs and the report appears, your environment is correct.

## The five-minute mental model

Everything is built from a few core types in `src/context_engineering_lab/core/`:

- `Item` — a unit of context, with content, length, timestamp, and metadata.
- `Budget` — a limit in items or tokens.
- `Task` — the query/goal a case poses.
- `Case` — a generated problem instance: candidate items + ground truth.
- `Strategy` — turns candidates into a budgeted `Context` (the decision).
- `Benchmark` — generates cases and `evaluate`s a context into metrics.
- `Experiment` + `ExperimentRunner` — sweep strategies × seeds × budgets and emit
  an `ExperimentResult`.

A run is just: `Benchmark.generate(seed) → Strategy.select(...) →
Benchmark.evaluate(...) → aggregate → report`. The diagram in the
[README](../README.md#architecture-and-phase-map) shows the same loop.

## Follow the data

1. **A benchmark generates cases.** Open
   `benchmarks/selection.py` and its presets in `benchmarks/selection_presets.py`.
   Note how relevance is ground truth, separate from the observable signals a
   strategy may use.
2. **A strategy makes the decision.** Open `strategies/keyword_overlap.py` (a
   query-aware selector) and `strategies/positional.py` (`first-n`/`last-n`,
   content-blind baselines). Every family also has an `oracle.py` ceiling.
3. **The benchmark scores it.** Metrics are pure functions in `core/metrics.py`
   and the `*_metrics.py` siblings — no benchmark or strategy imports.
4. **The runner aggregates.** `core/runner.py` is ~150 lines; read it once and the
   whole harness is demystified.
5. **Reporting renders Markdown.** `reporting/phase2_report.py` turns results into
   the tables you saw in `summary.md`. Persistence is `reporting/persistence.py`.

## The catalog is the index

`catalog.py` registers every built-in strategy, benchmark, compressor, retention
policy, attention allocator, and composition by id. `perturbations/registry.py`
does the same for robustness perturbations. If you want to know what exists, read
these two files (or run `context-lab list`).

## How the phases stack

Primitives (Phases 2–6) each live in their own package. Phase 7 composes them
(`compositions.py`, `benchmarks/interaction.py`). Phase 8 adds naturalistic
families (`benchmarks/naturalistic/`). Phase 9 reads result artifacts and
synthesizes them (`synthesis/`). Phase 10 stress-tests benchmarks
(`perturbations/`). Each phase has a `docs/phase-N-summary.md` and an
`experiments/phaseN.py` suite wired to a `run-phaseN` CLI command.

## Adding your own experiment

The smallest useful contribution is a new experiment over existing components:

1. Add a factory in `experiments/` returning `Experiment` objects (see
   `experiments/phase2.py` for the pattern).
2. Reuse benchmarks and strategies from the catalog; include an oracle and at
   least one content-blind baseline, and sweep budgets.
3. Add a test mirroring an existing one in `tests/`.
4. Run the gate: `ruff check . && mypy && pytest && python -m build`.

To add a new *strategy* or *benchmark*, implement the `Strategy` / `Benchmark`
protocol in the appropriate package, register it in `catalog.py`, and add a
mirrored test. Keep claims benchmark-specific (see [CONTRIBUTING.md](../CONTRIBUTING.md)).

## Where to read next

- [thesis.md](thesis.md) — why the lab exists.
- [harness.md](harness.md) — the core abstractions in depth.
- [metrics.md](metrics.md) — what each metric means.
- [reproducibility.md](reproducibility.md) — the determinism guarantee.
- [RESULTS.md](../RESULTS.md) / [FINDINGS.md](../FINDINGS.md) — what the lab found.
