# Phase 5 summary

Phase 5 runs the first controlled experiments on **forgetting as a policy**: which
items should survive a memory budget and which should be discarded. It studies the
*retention decision* — not a memory store, persistence layer, or eviction
schedule; nothing is written to or read from a database. For the benchmark design
see [retention-benchmarks.md](retention-benchmarks.md).

## What Phase 5 added

- A retention interface (`core.retention`): a `RetentionPolicy` protocol, the
  `RetentionDecision` / `RetentionStats` / `RetentionResult` records, an observable
  `frequency` accessor key, and a `PolicyStrategy` adapter so policies run through
  the existing experiment runner unchanged. Minimal by design — no store, no clock.
- Forgetting metrics (`core.retention_metrics`): `retention_precision`,
  `retention_recall`, `useful_retention_rate`, `harmful_retention_rate`,
  `memory_budget_utilization`, and `forgetting_efficiency`.
- Six retention policies (`retention`): `retain-all`, `recency-retention`,
  `frequency-retention`, `salience-retention`, a `hybrid-retention` blend, and an
  `oracle-retention` ceiling.
- The `retention-utility-preservation` benchmark generator with three presets:
  `low-noise-retention`, `stale-accumulation`, `harmful-memory`.
- Four reproducible experiments and a Markdown report, driven by
  `context-lab run-phase5`.

## Forgetting is distinct from temporal relevance

Phase 4 asked where in time the signal sits. Phase 5 deliberately decouples
utility from age: the benchmark places harmful items recently and spreads useful
items across time, so a policy that forgets by age alone retains harm and drops
old-but-useful items. Forgetting must read utility-bearing signals, not just
recency.

## Policies as bounds

The line-up is structured as a comparison, not a leaderboard of deployable
systems:

- **Reference:** `retain-all` keeps everything and ignores the budget; its
  `memory_budget_utilization` exceeds 1 whenever forgetting was needed.
- **Single-signal:** `recency`, `frequency`, and `salience` each trust one signal.
- **Deployable blend:** `hybrid-retention` normalizes and combines all three.
- **Upper bound:** `oracle-retention` reads the ground-truth relevance marker and
  is **not deployable**; it measures headroom.

## Observations (these benchmarks only)

Run `context-lab run-phase5` to regenerate the tables. The headline patterns,
specific to these synthetic benchmarks, seeds, and budgets:

- **Selective forgetting can beat keeping everything.** Under a budget below the
  memory size, `retain-all` overruns the budget and keeps every harmful item, so
  utility-aware policies reach higher retention precision and forgetting
  efficiency than retaining everything. (RQ7)
- **Recency and frequency retain harm.** Because harmful items are recent and
  recur often, forgetting by recency or by frequency keeps them — retention is not
  automatically good. (RQ16)
- **Salience tracks utility when signals are clean.** On `low-noise-retention` the
  salience policy approaches the oracle's forgetting efficiency; on the high-noise
  `harmful-memory` preset, where harmful salience overlaps useful, every deployable
  policy falls well short of the oracle. (RQ16)
- **The budget frontier is visible.** `retention-budget-sweep` traces useful and
  harmful retention against an item-budget ladder; the oracle recovers useful
  items first, and the deployable policies recover them (or fail to) as the budget
  grows.

These begin to address [research questions](research-questions.md) RQ7 and the
newly added RQ16. They do not close them, and they say nothing about RQ8
(attention budget allocation) or the robustness questions, which remain future
work.

## What Phase 5 does not claim

- **No general conclusions.** Every observation is specific to synthetic
  benchmarks, a handful of seeds, and item budgets. None generalizes to real
  memory systems or to forgetting at large.
- **No memory store.** Forgetting is studied as a one-shot retention decision over
  a fixed candidate memory; there is no persistence, eviction over time, vector
  database, or LLM-based memory.
- **The oracle is not achievable.** `oracle-retention` reads the ground-truth
  relevance marker; it is a measurement ceiling, not a target.
- **The hybrid is not guaranteed to win.** Whether blending beats the best single
  signal depends on the preset and is measured, not assumed.
- **No tuning, no significance testing.** Results are aggregated means over a few
  seeds, reported as-is.

## Running validation

```bash
pip install -e ".[dev]"
ruff check .       # lint
mypy               # strict type check
pytest             # tests
python -m build    # build sdist + wheel
```
