# Temporal benchmarks

Phase 4 introduces one controlled, synthetic benchmark family —
`temporal-context-relevance` — and three presets built from it. These study how
**time** should shape what context survives a budget. Phase 4 studies temporal
*effects* only: it does **not** implement forgetting, eviction, or any retention
policy. Everything is generated and scored deterministically from a seed; there
is no external API and no LLM.

The single question they probe is the Phase 4 question:

> How should temporal information shape what context survives under limited
> budgets?

## Time as integer positions

Each case lays `sequence_length` items along a timeline. An item's `timestamp` is
its integer position: `0` is the oldest, `sequence_length - 1` is the "now". An
item's *age* is `now - timestamp` — `0` for the newest item, larger for older
ones. Modeling time as evenly spaced positions keeps the benchmark deterministic
and the metrics interpretable; wall-clock timestamps and irregular spacing are
out of scope.

Each item is one of four kinds:

- **relevant** — ground-truth relevant to the task (must be retrieved),
- **stale** — old and no longer relevant (a dated look-alike),
- **distractor** — irrelevant noise placed by the distractor-age knob,
- **filler** — the remaining background.

## Two signals, one ground truth

Every item carries an *observable* `salience` value in `[0, 1]` (metadata key
`salience`) and a hidden ground-truth relevance flag (`oracle_relevant`).
Salience is a **noisy proxy** a deployable strategy may read; the relevance flag
is ground truth that **only** `oracle-temporal` may read. Stale items are flagged
with `stale` for the staleness metric.

This separation is what makes the *drift* knob meaningful: drift controls how far
salience is pulled away from the truth.

## The generator: `temporal-context-relevance`

The generator (`benchmarks/temporal.py`) exposes the knobs that matter for the
Phase 4 questions:

| Knob | Values | What it probes |
| --- | --- | --- |
| `sequence_length` | `>= 2` | Timeline length |
| `num_relevant` | `>= 1` | Size of the signal |
| `num_distractors` / `num_stale` | `>= 0` | Noise and dated look-alikes |
| `relevant_age` | `recent`, `mixed`, `old` | Where the signal sits in time |
| `distractor_age` | `recent`, `mixed`, `old` | Where the noise sits in time |
| `drift` | `none`, `gradual`, `abrupt` | Salience-vs-truth mismatch |
| `budget_sweep` | tuple of item budgets | Where the budget breaks recovery |

Construction details:

- Items are placed by age band; relevant items claim their band first, then stale
  (oldest), then distractors, with collisions resolved to the nearest free slot.
- Salience: relevant items get high salience (mostly `1.0`); other items get low
  salience. Under `gradual`/`abrupt` drift, the most recent non-relevant items
  become **decoys** with moderate/high salience, modeling a recent regime that
  *looks* important but is not.
- Budgets are measured in **items** (each item costs one), so the strategies
  compete on *which* items to keep, not on compressing content.

### Metrics

The benchmark reports eight metrics per case (formulas in
[metrics.md](metrics.md)):

- `answer_support` — whether all relevant items were retrieved.
- `selection_recall` / `selection_precision` — set overlap with the relevant set.
- `budget_utilization` — fraction of the budget consumed.
- `temporal_relevance` — fraction of selected items whose age lands in the
  relevant age band.
- `stale_selection_rate` — fraction of selected items that are stale (lower
  better).
- `age_of_selected_context` — mean normalized age of the selection.
- `relevant_age_gap` — normalized distance in time between the selection and the
  relevant set (lower means temporally aligned).

The temporal metrics describe *where in time* a selection lands, which the
set-overlap metrics ignore.

## Presets

Three presets, each isolating one temporal regime.

### `recent-signal`

- **Construct:** retrieval when the relevant signal is the most recent.
- **Parameters:** length 20, 3 relevant (recent), 8 distractors (mixed), 4 stale,
  no drift.
- **Expected failure modes:** oldest-first and the fixed leading window look in
  the wrong era; recency, sliding-window, and age-weighted should track the
  oracle.

### `old-signal`

- **Construct:** retrieval when the relevant signal is old and recent items are
  distractors.
- **Parameters:** length 20, 3 relevant (old), 8 distractors (recent), 4 stale,
  no drift.
- **Expected failure modes:** recency and sliding-window chase recent
  distractors; oldest-first and the fixed leading window recover the old signal.

### `drift-heavy`

- **Construct:** sensitivity to abrupt temporal drift in the salience signal.
- **Parameters:** length 24, 4 relevant (mixed), 10 distractors (recent), 4
  stale, abrupt drift.
- **Expected failure modes:** age-weighted is pulled toward recent high-salience
  decoys; recency captures only the recent half of a spread-out signal; no
  deployable strategy matches the oracle under abrupt drift.

## Strategies under test

| Strategy | Reads | Role |
| --- | --- | --- |
| `recency` | timestamp | Baseline; keeps the newest |
| `oldest-first` | timestamp | Foil; keeps the oldest |
| `sliding-window-5` | timestamp | Window anchored at "now" |
| `fixed-window-5` | timestamp | Window fixed at the timeline start |
| `age-weighted-hl4` | timestamp + salience | Deployable, age-aware weighting |
| `oracle-temporal` | relevance flag | **Ceiling only — not deployable** |

`age-weighted` ranks items by `salience · 0.5^(age / half_life)`, so it can keep
an older but clearly-salient item over a fresh but dull one — something pure
recency cannot do. It is the one deployable strategy that reads salience, which
is exactly why temporal drift (recent decoys) can fool it.

`oracle-temporal` reads the ground-truth relevance flag and keeps relevant items
first. No real strategy knows relevance in advance, so it is an upper bound for
comparison, never a strategy to ship.

## Reproducing

```bash
context-lab run-phase4 --output artifacts/phase4
```

This runs all four Phase 4 experiments, writes one JSON artifact per experiment,
and a `summary.md` report. Output is deterministic across repeated runs.

Every result carries its seed, item budget, benchmark id and version, strategy
id, and the metric definitions above — the minimum needed to reproduce and
interpret it.
