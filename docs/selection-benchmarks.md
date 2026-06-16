# Selection benchmarks

Phase 2 introduces one controlled, synthetic benchmark family —
`selection-signal-retrieval` — and three presets built from it. These are
instruments for *controlled comparison*, not realistic corpora. Everything is
generated deterministically from a seed; given the same seed, the same cases come
out every time.

The single question they probe is the Phase 2 question:

> What deserves to enter a limited context window?

## The generator: `selection-signal-retrieval`

Each case is a needle-in-a-haystack: one or more **target** items carry the
query's signal terms, surrounded by **distractors**. A strategy must get the
target(s) into the budget-limited context.

The generator (`benchmarks/selection.py`) exposes the knobs that matter for
selection under pressure:

| Knob | Values | What it probes |
| --- | --- | --- |
| `num_distractors` | `>= 0` | Distractor load |
| `target_position` | `early`, `middle`, `late`, `random` | Position bias |
| `distractor_similarity` | `low`, `medium`, `high` | Content-based selection |
| `num_targets` | `>= 1` | Multi-item retrieval |
| `target_length` / `distractor_length` | `>= 1` | Item cost |
| `budget_sweep` | tuple of budgets | Where reduction breaks the task |

Construction details:

- The query is a fixed set of distinct **signal terms**. Targets contain all of
  them; distractors share a fraction depending on `distractor_similarity`:
  `low` shares none, `medium` shares about half, `high` shares all of them (so
  content can no longer separate target from distractor).
- Item `timestamp` is set to the candidate's index, so *position* and *recency*
  coincide. This is what lets the order-only baselines act as position probes.
- Targets are flagged in metadata with the oracle relevance key. Only
  `OracleSelection` may read it; see [the strategy notes](#strategies-under-test).

### Metrics

The benchmark reports four metrics per case (see [metrics.md](metrics.md) for the
formal selection metrics):

- `answer_support` — did the required target(s) make it into the context?
- `selection_recall` — fraction of relevant items selected.
- `selection_precision` — fraction of the selection that is relevant.
- `budget_utilization` — `context.total_cost / budget.limit`, a Phase 2 derived
  metric describing how fully the budget was used.

`selection_precision` is formally undefined for an empty selection; the benchmark
records `0.0` in that case as a reporting convenience (the same convention as the
smoke benchmark).

Other metrics suggested for Phase 2 (`target_rank_before_selection`,
`selected_target_position`, `budget_cliff_point`) are intentionally **not**
implemented: they describe a strategy's *internal* ranking, which `evaluate`
cannot observe — it only sees the final context. Computing them would require
leaking strategy internals into scoring, so they are deferred rather than faked.

## Presets

Three presets, each isolating one construct. Three is enough; more would add
combinations without adding insight.

### `easy-selection`

- **Construct:** basic signal retrieval with low distractor interference.
- **Parameters:** 4 distractors, `low` similarity, `random` position.
- **Expected failure modes:** position-blind baselines miss the target only at
  budget 1; keyword overlap should track the oracle closely.

### `position-biased-selection`

- **Construct:** position bias of order-only baselines.
- **Parameters:** 7 distractors, `low` similarity, target always `late`.
- **Expected failure modes:** `first-n` misses the late target until the budget
  is large; `last-n` and `recency` succeed by position, not by relevance.

### `high-distractor-selection`

- **Construct:** selection under heavy, content-similar distractor load.
- **Parameters:** 15 distractors, `high` similarity, `random` position.
- **Expected failure modes:** keyword overlap cannot separate target from
  look-alike distractors; non-oracle strategies retrieve the target mostly by
  chance.

## Strategies under test

| Strategy | Reads content? | Role |
| --- | --- | --- |
| `first-n` | no | Lower bound; position probe (front) |
| `last-n` | no | Lower bound; position probe (back) |
| `recency` | no (timestamp only) | Baseline; coincides with `last-n` here |
| `random` | no | Deterministic chance baseline |
| `keyword-overlap` | yes | Crude salience proxy |
| `oracle` | privileged | **Ceiling only — not deployable** |

`OracleSelection` reads a ground-truth relevance flag that benchmarks write into
item metadata. No real system has that at selection time, so the oracle is an
upper bound for comparison, never a strategy to ship.

## Reproducing

```bash
context-lab run-phase2 --output artifacts/phase2
```

This runs all four Phase 2 experiments, writes one JSON artifact per experiment,
and a `summary.md` report. Output is deterministic across repeated runs.

Every result carries its seed, budget, benchmark id and version, strategy id, and
the metric definitions above — the minimum needed to reproduce and interpret it.
