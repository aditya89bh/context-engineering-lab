# Retention benchmarks

Phase 5 introduces one controlled, synthetic benchmark family —
`retention-utility-preservation` — and three presets built from it. These study
**forgetting as a policy**: which items should survive a memory budget and which
should be discarded. Everything is generated and scored deterministically from a
seed; there is no external API, no LLM, and no memory store or persistence layer.

The single question they probe is the Phase 5 question:

> What information should be retained, and what should be removed, under limited
> memory budgets?

## Forgetting is not temporal relevance

Phase 4 asked where *in time* the signal sits. Phase 5 deliberately decouples
utility from age: **old information may still be useful, and recent information may
be harmful**. The generator places harmful items at the most recent positions and
spreads useful items across time, so a policy that forgets by age alone keeps harm
and drops old-but-useful items. Good forgetting must read *utility-bearing*
signals (salience, frequency, or a blend), not just recency.

## Four kinds of memory

Each case is a small memory of `memory_size` items, one of four kinds:

- **useful** — ground-truth relevant; should be kept. A required subset
  (`num_required`) is the minimal must-keep set the task depends on.
- **stale** — once useful, now outdated; should be forgotten. Placed at the oldest
  positions.
- **harmful** — actively misleading; must be forgotten. Placed at the most recent
  positions and made to recur often (high frequency).
- **neutral** — forgettable background filler.

## Observable signals vs. ground truth

Every item carries observable signals a deployable policy may read — a `salience`
value in `[0, 1]` and an integer access `frequency` count — plus hidden
ground-truth markers (`oracle_relevant`, `harmful`, `stale`, `required`) that
**only** scoring and `oracle-retention` may read.

The `noise` knob controls how well the observable salience separates useful from
harmful items:

- `low` — useful items are clearly high-salience and harmful items low-salience,
  so a salience policy can tell them apart.
- `high` — useful and harmful salience ranges overlap, so salience becomes
  unreliable and single-signal policies degrade.

Harmful items are high-frequency under both settings, so a frequency policy
retains them regardless of noise — this is what makes "retention can be harmful"
visible.

## The generator: `retention-utility-preservation`

The generator (`benchmarks/retention.py`) exposes the knobs that matter for the
Phase 5 questions:

| Knob | Values | What it probes |
| --- | --- | --- |
| `num_useful` / `num_required` | `>= 1` | Size of the signal and must-keep core |
| `num_stale` | `>= 0` | Stale-information density |
| `num_harmful` | `>= 0` | Harmful-information density |
| `num_neutral` | `>= 0` | Memory growth (background accumulation) |
| `noise` | `low`, `high` | Utility-distribution clarity |
| `budget_sweep` | tuple of item budgets | Where the budget breaks utility recovery |

Construction details:

- Timestamps are dense integer positions `0 … memory_size - 1`. Stale items take
  the oldest positions, harmful items the most recent, and useful items are spread
  evenly across the middle, with neutral filling the rest.
- Budgets are measured in **items** (each item costs one), so policies compete on
  *which* items to keep, not on compressing content.

### Metrics

The benchmark reports seven metrics per case (formulas in
[metrics.md](metrics.md)):

- `answer_support` — whether all required useful items were kept.
- `retention_precision` — fraction of kept items that are useful.
- `retention_recall` — fraction of *required* useful items kept.
- `useful_retention_rate` — fraction of *all* useful items kept.
- `harmful_retention_rate` — fraction of harmful items kept (lower is better).
- `memory_budget_utilization` — fraction of the budget consumed (`> 1` for
  retain-all).
- `forgetting_efficiency` — useful retention rate minus harmful retention rate.

These describe how cleanly a policy keeps utility and discards harm; they are not
combined into a single quality score.

## Presets

Three presets, each isolating one forgetting regime.

### `low-noise-retention`

- **Construct:** retention with well-separated useful and harmful signals (the
  sanity floor).
- **Parameters:** 4 useful (2 required), 3 stale, 3 harmful, 6 neutral, low noise.
- **Expected failure modes:** frequency retains high-frequency harm; recency
  retains recent harm and forgets old useful items.

### `stale-accumulation`

- **Construct:** retention as stale and neutral memory accumulates.
- **Parameters:** 4 useful (2 required), 10 stale, 2 harmful, 10 neutral, low
  noise.
- **Expected failure modes:** retain-all overruns the budget as stale piles up;
  recency forgets old useful items along with the stale ones.

### `harmful-memory`

- **Construct:** forgetting harm under heavy, signal-overlapping harmful load.
- **Parameters:** 4 useful (2 required), 3 stale, 10 harmful, 3 neutral, high
  noise.
- **Expected failure modes:** frequency and recency retain many harmful items;
  salience is unreliable when harmful salience overlaps useful; no deployable
  policy matches the oracle under high noise.

## Policies under test

| Policy | Reads | Role |
| --- | --- | --- |
| `retain-all` | nothing | Reference; never forgets (ignores the budget) |
| `recency-retention` | timestamp | Foil; keeps the newest |
| `frequency-retention` | frequency | Keeps the most accessed (retains recurring harm) |
| `salience-retention` | salience | Keeps the most salient (tracks utility when clean) |
| `hybrid-retention` | salience + frequency + recency | Deployable, normalized blend |
| `oracle-retention` | relevance marker | **Ceiling only — not deployable** |

`hybrid-retention` min-max normalizes the three signals across the memory and
keeps the highest weighted sum (default weights favor salience). Blending lets it
temper any single signal, but whether it beats the best single signal is an
empirical question the experiments measure, not a guarantee.

`oracle-retention` reads the ground-truth relevance marker and keeps useful items
first. No real memory knows utility at retention time, so it is an upper bound for
comparison, never a policy to ship.

## Reproducing

```bash
context-lab run-phase5 --output artifacts/phase5
```

This runs all four Phase 5 experiments, writes one JSON artifact per experiment,
and a `summary.md` report. Output is deterministic across repeated runs.

Every result carries its seed, retention budget, benchmark id and version, policy
id, and the metric definitions above — the minimum needed to reproduce and
interpret it.
