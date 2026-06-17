# Phase 6 summary

Phase 6 runs the first controlled experiments on **attention allocation**: how a
fixed budget should be split across competing sources before any item is selected.
It studies the *allocation policy* — not a scheduler, agent loop, or event system.
For the benchmark design see [attention-benchmarks.md](attention-benchmarks.md).

## What Phase 6 added

- An attention interface (`core.attention`): a `Source` grouping, an
  `AttentionAllocator` protocol, the `AllocationDecision` / `AllocationStats` /
  `AllocationResult` records, an observable `source_quality` key, and an
  `AllocatorStrategy` adapter so allocators run through the existing experiment
  runner unchanged. Minimal by design — no scheduler, no event loop.
- Allocation metrics (`core.attention_metrics`): `allocation_efficiency`,
  `signal_capture_rate`, `wasted_attention_rate`, and `source_coverage`
  (`budget_utilization` is reused).
- Six allocators (`attention`): `uniform-allocation`, `proportional-allocation`,
  `salience-allocation`, `adaptive-allocation`, `winner-take-most`, and an
  `oracle-allocation` ceiling.
- The `attention-source-allocation` benchmark generator with three presets:
  `balanced-sources`, `concentrated-signal`, `noisy-dominant-source`.
- Four reproducible experiments and a Markdown report, driven by
  `context-lab run-phase6`.

## Allocation is distinct from selection

Selection chooses items; allocation chooses how much budget each source gets. In
this benchmark the inner selection that fills each source's share is identical for
every allocator, so the experiments isolate the quality of the *split* — the task
cannot be won by a better item ranking, only by a better allocation.

## Allocators as bounds

The line-up is structured as a comparison, not a leaderboard of deployable
systems:

- **Baseline:** `uniform` splits evenly, ignoring source value.
- **Single-cue:** `proportional` (size) and `salience` each trust one observable
  cue and can be baited by a big or loud source.
- **Deployable, quality-led:** `adaptive` weights observable quality and
  redistributes budget a source cannot use.
- **Concentrator:** `winner-take-most` bets most of the budget on the top source.
- **Upper bound:** `oracle-allocation` reads ground-truth signal counts and is
  **not deployable**; it measures headroom.

## Observations (these benchmarks only)

Run `context-lab run-phase6` to regenerate the tables. The headline patterns,
specific to these synthetic benchmarks, seeds, and budgets:

- **Uniform is hard to beat only when sources are balanced.** On
  `balanced-sources` no allocator clearly beats uniform, and winner-take-most
  underperforms by starving the other useful sources. (RQ8, RQ17)
- **Concentration helps when signal is concentrated.** On `concentrated-signal`,
  uniform and size-proportional waste budget on near-empty sources, while
  winner-take-most and the quality-led adaptive allocator approach the oracle.
  (RQ8, RQ17)
- **Volume and salience can be baited.** On `noisy-dominant-source`, proportional
  pours budget into the oversized trap and salience is drawn by its inflated
  salience, raising wasted attention; the quality-led adaptive allocator resists
  the trap and stays close to the oracle. (RQ17)
- **The budget frontier is visible.** `attention-budget-sweep` traces signal
  capture and wasted attention against an item-budget ladder; the oracle commits
  to the signal first, and the deployable allocators recover it (or fail to) as
  the budget grows.

These begin to address [research questions](research-questions.md) RQ8 and the
newly added RQ17. They do not close them, and they say nothing about the
robustness questions (RQ9 onward), which remain future work.

## What Phase 6 does not claim

- **No general conclusions.** Every observation is specific to synthetic
  benchmarks, a handful of seeds, and item budgets. None generalizes to real
  attention mechanisms or to attention at large.
- **No scheduler or agent.** Allocation is studied as a one-shot budget split over
  a fixed set of sources; there is no scheduling, agent loop, event system, vector
  database, or LLM-based attention.
- **The oracle is not achievable.** `oracle-allocation` reads ground-truth signal
  counts; it is a measurement ceiling, not a target.
- **No single allocator wins everywhere.** Which allocator is best depends on the
  preset and is measured, not assumed.
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
