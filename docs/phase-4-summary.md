# Phase 4 summary

Phase 4 runs the first controlled experiments on **temporal context under budget
pressure**: how time should shape what context survives. It studies temporal
*effects* only — there is **no forgetting, no eviction, and no retention
policy**; nothing is removed from a store. For the benchmark design see
[temporal-benchmarks.md](temporal-benchmarks.md).

## What Phase 4 added

- Temporal utilities (`core.temporal`): age and relative-age helpers, an
  observable `salience` accessor, and a "now" (latest timestamp) helper. Minimal
  by design — no event store, no clock.
- Temporal metrics (`core.temporal_metrics`): `temporal_relevance`,
  `stale_selection_rate`, `age_of_selected_context`, and `relevant_age_gap`.
- Five temporal strategies (`strategies.temporal`): `oldest-first`,
  `sliding-window`, `fixed-window`, `age-weighted`, and an `oracle-temporal`
  ceiling. `recency` is reused unchanged from Phase 2.
- The `temporal-context-relevance` benchmark generator with three presets:
  `recent-signal`, `old-signal`, `drift-heavy`.
- Four reproducible experiments and a Markdown report, driven by
  `context-lab run-phase4`.

## Strategies as bounds

The line-up is structured as a comparison, not a leaderboard of deployable
systems:

- **Baseline:** `recency` keeps the newest items.
- **Foils:** `oldest-first` and `fixed-window` (anchored at the timeline start)
  deliberately look away from "now"; `sliding-window` tracks "now".
- **Deployable, age-aware:** `age-weighted` weights an observable salience signal
  by age decay — the one deployable strategy that reads salience.
- **Upper bound:** `oracle-temporal` reads the ground-truth relevance flag and is
  **not deployable**; it measures headroom.

## Observations (these benchmarks only)

Run `context-lab run-phase4` to regenerate the tables. The headline patterns,
specific to these synthetic benchmarks, seeds, and budgets:

- **Recency is not a universal good.** On `recent-signal` it tracks the oracle,
  but on `old-signal` recency (and the sliding window) chase recent distractors
  and miss the old signal entirely, while `oldest-first` and the fixed leading
  window recover it. Recency is a *heuristic about where relevance tends to be*,
  not relevance itself. (RQ5)
- **Windows fail when the signal leaves the window.** The sliding window succeeds
  exactly when the signal is recent and fails when it is old; the fixed leading
  window does the reverse. A fixed window is right only while relevance stays in
  its fixed region. (RQ15)
- **Age-aware weighting can beat recency — until drift.** When salience tags the
  relevant items, `age-weighted` keeps salient-but-not-newest items that recency
  drops. Under `drift-heavy`, recent high-salience decoys pull it off target, and
  no deployable strategy matches the oracle. (RQ5, RQ15)
- **The budget frontier is visible.** `temporal-budget-sweep` traces answer
  support and the relevant-age gap against an item-budget ladder; the oracle
  reaches the signal first, and the deployable strategies recover it (or fail to)
  as the budget grows.

These begin to address [research questions](research-questions.md) RQ5 and the
newly added RQ15. They do not close them, and they say nothing about RQ6 (decay
*shape* vs. a known drift process) or RQ7 (forgetting), which remain future work.

## What Phase 4 does not claim

- **No general conclusions.** Every observation is specific to synthetic
  benchmarks, a handful of seeds, and item budgets. None generalizes to real
  temporal data or to temporal reasoning at large.
- **No forgetting.** Nothing is evicted or decayed out of a store; Phase 4 only
  selects under a budget. Forgetting and retention are deferred (see the
  [roadmap](roadmap.md)).
- **The oracle is not achievable.** `oracle-temporal` reads the ground-truth
  relevance flag; it is a measurement ceiling, not a target.
- **One decay shape only.** `age-weighted` uses a single exponential half-life;
  comparing decay families against a known drift process (RQ6) is out of scope.
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
