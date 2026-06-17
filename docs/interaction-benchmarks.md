# Interaction benchmarks

Phase 7 introduces one controlled, synthetic benchmark family —
`interaction-context-pipeline` — and three presets built from it. These study
**how the primitives built in earlier phases interact when chained into a
pipeline**. Everything is generated and scored deterministically from a seed;
there is no external API, no LLM, and no scheduler, agent, or planner.

The single question they probe is the Phase 7 question:

> How do context-engineering primitives interact with each other?

## Composition, not new primitives

Phase 7 adds no new primitive algorithm. A pipeline is a linear chain of existing
strategies (`core.composition.StrategyComposition`): the output items of one
stage become the candidate set of the next, and only the final stage enforces the
real budget — earlier stages get a *widened* budget (a multiple of the final one)
so they prune or transform without prematurely committing. Because every Phase
2-6 primitive already implements the `Strategy` interface (selectors directly,
retention/attention/compression through their adapters), a composition is itself a
`Strategy` and runs through the existing experiment runner unchanged.

## One case, every primitive

Each case is built so several primitives have something to do at once. Items come
in four kinds, spread over a fixed timeline and several sources:

- **relevant** — ground-truth signal: carries the query terms, is salient, is
  *corroborated* (high access frequency), and is spread across time;
- **harmful** — a trap that *looks* relevant: it carries the query terms and is
  salient and recent, but is rarely corroborated (low frequency) and is flagged
  harmful;
- **stale** — old, off-topic items a temporal filter should drop;
- **distractor** — recent, off-topic filler.

The signals are deliberately misaligned, so no single primitive suffices:

- keyword selection is fooled by harmful items (they carry the query terms);
- a salience- or recency-only stage keeps harmful items (they are salient and
  recent);
- only **frequency** separates corroborated-relevant from rarely-seen-harmful, so
  a retention/frequency stage is what removes the trap;
- a recency window drops stale items but, because relevant items are spread over
  time, an aggressive window also drops old-but-relevant ones.

Ground truth (relevance, harmful, stale flags) is hidden and may be read **only**
by the oracle stage. Every item also carries observable cues a deployable stage
may read: `salience`, `frequency`, and per-source `source_quality`, plus a
`timestamp` and a `source` label.

## The generator: `interaction-context-pipeline`

The generator (`benchmarks/interaction.py`) exposes the knobs that matter for the
Phase 7 questions:

| Knob | Values | What it probes |
| --- | --- | --- |
| `num_sources` | `>= 2` | How many sources compete |
| `num_relevant` | `>= 1` | Amount of signal |
| `num_required` | `[1, num_relevant]` | Must-select subset |
| `num_stale` | `>= 0` | Stale density |
| `num_harmful` | `>= 0` | Harmful-trap density |
| `num_distractor` | `>= 0` | Off-topic noise |
| `source_imbalance` | `low`, `high` | Source-quality spread |
| `signal_concentration` | `spread`, `concentrated` | Whether signal sits in one source |
| `budget_sweep` | tuple of item budgets | Budget pressure |

Construction details:

- Timestamps use a fixed integer timeline (independent of memory size) so the
  default recency window covers a stable fraction of it: stale items are the
  oldest tail, harmful items are recent, relevant items run from mid-timeline to
  now, and distractors are mid-to-recent.
- Relevant and harmful items embed the query terms; stale and distractors use a
  disjoint vocabulary, so a keyword selector lands on the on-topic items (signal
  *and* traps) and ignores the off-topic ones.
- Budgets are measured in **items** (each item costs one) for the shipped
  experiments, so item-budget pipelines share one sweep and compare fairly.

### Metrics

The benchmark reports seven metrics per case (formulas in [metrics.md](metrics.md)),
reusing the selection, retention, and temporal metrics and adding one:

- `answer_support` — whether every required item survived.
- `selection_precision` / `selection_recall` — relevant precision and recall.
- `harmful_retention_rate` — fraction of harmful traps kept (lower is better).
- `stale_selection_rate` — fraction of the output that is stale (lower is better).
- `budget_utilization` — fraction of the budget filled.
- `pipeline_efficiency` — relevant items captured per unit of budget.

The comparative interaction metrics (`interaction_gain`, `degradation_rate`,
`compensation_effect`) are computed at report time by contrasting a pipeline with
its constituent baselines; they are not per-case scores.

## Presets

Three presets, each isolating one interaction regime.

### `balanced-interaction`

- **Construct:** composition when traps and stale items are sparse.
- **Parameters:** 3 sources, 8 relevant, 3 stale, 3 harmful, 6 distractors; low
  imbalance, spread signal.
- **Expected failure modes:** composing adds little when one primitive already
  suffices; a temporal pre-filter can drop spread-out relevant items.

### `memory-pressure`

- **Construct:** composition against many harmful traps under tight budgets.
- **Parameters:** 3 sources, 8 relevant, 4 stale, 10 harmful, 6 distractors; high
  imbalance, concentrated signal; budgets 2-8.
- **Expected failure modes:** keyword selection keeps harmful items that carry the
  query terms; salience/recency stages keep them too; only a frequency-aware stage
  separates trap from signal.

### `noisy-context`

- **Construct:** composition under dense stale and distractor noise.
- **Parameters:** 4 sources, 8 relevant, 12 stale, 4 harmful, 14 distractors; high
  imbalance, spread signal.
- **Expected failure modes:** a temporal window drops old-but-relevant items with
  the stale tail; distractors crowd the budget when no stage filters them.

## Compositions under test

The shipped experiments compare primitive-only baselines against composed
pipelines and an oracle ceiling:

| Strategy | Kind | Stages |
| --- | --- | --- |
| `keyword-overlap` | baseline | selection |
| `sliding-window-5` | baseline | temporal |
| `frequency-retention` | baseline | retention |
| `adaptive-allocation` | baseline | attention |
| `temporal->selection` | pipeline | recency window, then selection |
| `attention->selection` | pipeline | allocation, then selection |
| `retention->attention` | pipeline | forgetting, then allocation |
| `temporal->retention` | pipeline | recency window, then forgetting |
| `retention->selection` | pipeline | forgetting, then selection |
| `oracle-pipeline` | ceiling | **reads ground truth — not deployable** |

Two further compositions, `selection->compression` and `retention->compression`,
end in a token-budget compression stage. They are registered and tested to show
the abstraction composes a compressor like any other stage, but they are not part
of the item-budget experiment sweeps (mixing token and item budgets in one sweep
is not well defined).

## Reproducing

```bash
context-lab run-phase7 --output artifacts/phase7
```

This runs all four Phase 7 experiments, writes one JSON artifact per experiment,
and a `summary.md` report. Output is deterministic across repeated runs.

Every result carries its seed, item budget, benchmark id and version, pipeline
composition (the strategy id encodes the chain), and the metric definitions above
— the minimum needed to reproduce and interpret it.
