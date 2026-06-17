# Phase 7 summary

Phase 7 runs the first controlled experiments on **interaction effects**: how the
primitives built in Phases 2-6 behave when chained into a pipeline. It composes
*existing* primitives — it introduces no new primitive algorithm — and studies
specific compositions, not context systems in general. For the benchmark design
see [interaction-benchmarks.md](interaction-benchmarks.md).

## What Phase 7 added

- A composition layer (`core.composition`): `PipelineStep`, `StepRecord`,
  `CompositionResult`, and `StrategyComposition` — a linear chain of existing
  strategies that is itself a `Strategy`, so it runs through the existing runner
  unchanged. Minimal by design — no workflow engine, no DAG.
- Interaction metrics (`core.interaction_metrics`): a per-case
  `pipeline_efficiency`, plus the comparative `interaction_gain`,
  `degradation_rate`, and `compensation_effect` used at report time.
- Built-in compositions (`compositions`) reusing existing primitives:
  `temporal->selection`, `attention->selection`, `retention->attention`,
  `temporal->retention`, `retention->selection`, the token-budget
  `selection->compression` and `retention->compression`, and an `oracle-pipeline`
  ceiling.
- The `interaction-context-pipeline` benchmark generator with three presets:
  `balanced-interaction`, `memory-pressure`, `noisy-context`.
- Four reproducible experiments (primitive-only baselines and composed pipelines)
  and a Markdown report, driven by `context-lab run-phase7`.

## Composition reuses, it does not reinvent

Every pipeline stage is an existing strategy: a selector, a temporal selector, a
retention policy, or an attention allocator, wrapped through the Phase 3-6
adapters. The value comes from the interaction experiments, not from new
algorithms. A pipeline narrows its candidates stage by stage; only the final
stage enforces the real budget, while earlier stages receive a widened budget so
they prune without committing early.

## Strategies as a comparison

The line-up is structured so a composition can be read against its parts, not as
a leaderboard of deployable systems:

- **Primitive baselines:** `keyword-overlap` (selection), `sliding-window-5`
  (temporal), `frequency-retention` (retention), `adaptive-allocation`
  (attention) — exactly the stages the pipelines chain.
- **Composed pipelines:** five item-budget chains of those primitives.
- **Upper bound:** `oracle-pipeline` reads ground-truth relevance and is **not
  deployable**; it measures headroom.

## Observations (these benchmarks only)

Run `context-lab run-phase7` to regenerate the tables. The headline patterns,
specific to these synthetic benchmarks, seeds, and budgets:

- **A forgetting stage can remove traps a selector keeps.** Harmful items carry
  the query terms, so `keyword-overlap` keeps them; placing `frequency-retention`
  first (`retention->selection`, `retention->attention`) cuts
  `harmful_retention_rate` relative to selection or attention alone, because
  frequency is the one observable cue that separates corroborated-relevant from
  the rarely-seen traps. (RQ18)
- **A temporal stage can discard signal a selector needs.** Because relevant items
  are spread across time, a recency window before selection
  (`temporal->selection`) lowers `selection_recall` relative to `keyword-overlap`
  alone — a composition that *hurts* on this benchmark. (RQ18)
- **Order and which stage runs last matter.** `temporal->retention` and
  `retention->attention` move different metrics in different directions; no single
  composition dominates every preset. (RQ18)
- **The interaction frontier shifts with budget.** `interaction-budget-sweep`
  traces the same line-up over a finer item-budget ladder, locating where a
  tightening budget changes which composition leads.

These begin to address [research questions](research-questions.md) RQ18. They do
not close it, and they say nothing about the robustness questions (RQ9 onward),
which remain future work.

## What Phase 7 does not claim

- **No general conclusions.** Every observation is specific to synthetic
  benchmarks, a handful of seeds, and item budgets, and is about *specific
  compositions* — not how context systems behave in general.
- **No new primitives.** Pipelines reuse existing strategies; nothing here studies
  a new algorithm.
- **No workflow engine.** Compositions are linear chains, not DAGs, schedulers,
  agents, or planners; there is no event system, vector database, or LLM.
- **The oracle is not achievable.** `oracle-pipeline` reads ground-truth
  relevance; it is a measurement ceiling, not a target.
- **Interaction metrics are relative.** They contrast a pipeline with chosen
  baselines and depend on which primitive instance stands in for each stage; the
  report shows the underlying means alongside.
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
