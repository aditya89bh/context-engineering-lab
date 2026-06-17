# Attention benchmarks

Phase 6 introduces one controlled, synthetic benchmark family —
`attention-source-allocation` — and three presets built from it. These study **how
a fixed budget should be split across competing sources** before any item is
selected. Everything is generated and scored deterministically from a seed; there
is no external API, no LLM, and no scheduler, agent loop, or event system.

The single question they probe is the Phase 6 question:

> How should limited context capacity be distributed across multiple competing
> sources of information?

## Allocation is not selection

Selection chooses items; allocation chooses how much budget each source gets. In
this benchmark a strategy first splits the budget into per-source shares, and only
then a **fixed inner selection** (highest observable salience first) fills each
share. That inner selection is identical for every allocator, so any difference in
results comes purely from the split — the benchmark cannot be solved by a better
item ranking, only by a better allocation.

## Sources, signal, and two observable cues

Each case holds several **sources**. A source is a named group of items mixing
*signal* items (ground-truth relevant) and *distractor* items. Each source exposes
two observable cues a deployable allocator may read:

- a per-source **quality** score (metadata key `source_quality`) — a *noisy* proxy
  for the source's latent signal richness, and
- a **salience** profile — the per-item salience, whose source mean a salience
  allocator reads.

Ground truth (which items are signal) is hidden and may be read **only** by
`oracle-allocation`. Because quality is noisy, a quality-aware allocator is good
but not perfect; because salience can be inflated on a trap source, a
salience-aware allocator can be misled.

## The generator: `attention-source-allocation`

The generator (`benchmarks/attention.py`) exposes the knobs that matter for the
Phase 6 questions:

| Knob | Values | What it probes |
| --- | --- | --- |
| `num_sources` | `>= 2` | How many sources compete |
| `source_size` | `>= 1` | Items per regular source |
| `quality_imbalance` | `low`, `high` | How different sources are |
| `signal_concentration` | `spread`, `concentrated` | Whether signal sits in one source |
| `noisy_dominant` | `bool` | Adds a large, salient, low-quality trap source |
| `dominant_size_factor` | `>= 1` | How oversized the trap source is |
| `budget_sweep` | tuple of item budgets | Where a tightening budget forces commitment |

Construction details:

- Each source is assigned a latent richness; its signal count is `round(richness ·
  size)` and its observable quality is the richness plus bounded noise, so quality
  tracks signal imperfectly.
- Signal items (and every item in a trap source) get high salience; ordinary
  distractors get low salience. The trap source therefore *shouts* (high mean
  salience) while holding little signal and honestly low quality.
- Budgets are measured in **items** (each item costs one), so allocators compete
  on *how much* of each source to admit, not on compressing content.

### Metrics

The benchmark reports five metrics per case (formulas in [metrics.md](metrics.md)):

- `allocation_efficiency` — fraction of selected items that are signal.
- `signal_capture_rate` — fraction of all available signal captured.
- `wasted_attention_rate` — fraction of the budget that did not become signal
  (lower is better).
- `source_coverage` — fraction of sources that contributed an item (a descriptor).
- `budget_utilization` — fraction of the budget actually filled.

These describe how well a split converted into captured signal; they are not
combined into a single quality score.

## Presets

Three presets, each isolating one allocation regime.

### `balanced-sources`

- **Construct:** allocation across comparably useful sources (the sanity floor).
- **Parameters:** 4 sources of size 6, low quality imbalance, spread signal.
- **Expected failure modes:** winner-take-most starves the other useful sources;
  no allocator should clearly beat uniform.

### `concentrated-signal`

- **Construct:** allocation when the signal sits in one high-quality source.
- **Parameters:** 4 sources of size 6, high quality imbalance, concentrated
  signal.
- **Expected failure modes:** uniform spends most of the budget on near-empty
  sources; proportional follows size, not signal.

### `noisy-dominant-source`

- **Construct:** allocation against a large, salient, low-signal trap source.
- **Parameters:** 4 sources of size 6 plus a trap source three times larger, high
  quality imbalance, concentrated signal.
- **Expected failure modes:** proportional pours budget into the oversized trap;
  salience is fooled by its inflated salience; uniform wastes a full share on it.

## Allocators under test

| Allocator | Reads | Role |
| --- | --- | --- |
| `uniform-allocation` | nothing | Baseline; equal split |
| `proportional-allocation` | source size | Spends by volume (baited by big sources) |
| `salience-allocation` | source salience | Spends by salience (baited by the trap) |
| `adaptive-allocation` | source quality | Deployable; quality-led, capacity-aware |
| `winner-take-most-0.7` | source quality | Concentrates on the top source |
| `oracle-allocation` | true signal counts | **Ceiling only — not deployable** |

`adaptive-allocation` weights sources by observable quality and never hands a
source more budget than it can fill, redistributing the slack — the strongest
*deployable* allocator here, but still bounded by quality being a noisy proxy.

`oracle-allocation` weights sources by their true signal counts and apportions
capacity-aware. No real allocator knows where the signal is in advance, so it is
an upper bound for comparison, never a strategy to ship.

## Reproducing

```bash
context-lab run-phase6 --output artifacts/phase6
```

This runs all four Phase 6 experiments, writes one JSON artifact per experiment,
and a `summary.md` report. Output is deterministic across repeated runs.

Every result carries its seed, item budget, benchmark id and version, allocator
id, and the metric definitions above — the minimum needed to reproduce and
interpret it.
