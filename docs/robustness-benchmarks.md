# Robustness benchmarks (Phase 10)

Phase 10 does not add a new benchmark family, strategy, or primitive. It asks a
single question of the work already built: **how robust are context-engineering
strategies when a benchmark's assumptions are deliberately stressed?** It answers
it by *perturbing* the existing Phase 8 naturalistic benchmarks and measuring how
far each existing strategy falls from its own unperturbed baseline.

Everything below is mechanical and specific to the synthetic benchmarks, seeds,
and budgets behind the artifacts. Nothing here is a claim about real-world
systems, and `oracle` strategies are ceilings, not deployable approaches.

## Perturbation philosophy

A perturbation is a deterministic transform from a benchmark
[`Case`](../src/context_engineering_lab/core/benchmark.py) to a stressed case. Two
rules make the results interpretable:

1. **Ground truth is never touched.** A perturbation never changes `relevant_ids`,
   `required_ids`, or the privileged `oracle_relevant` marker. Injected items are
   always non-relevant; corrupted signals leave the relevance labels intact. The
   oracle ceiling therefore stays fixed, recall denominators stay fixed, and any
   score drop isolates a strategy's reliance on the stressed signal rather than a
   change in the task.
2. **Same scoring, comparable numbers.** A
   [`PerturbedBenchmark`](../src/context_engineering_lab/perturbations/base.py)
   wraps an existing benchmark, rewrites only the cases it generates, and delegates
   scoring back to the inner benchmark unchanged. A metric measured under
   perturbation is directly comparable to the baseline, so degradation is just
   `baseline - perturbed` on the oriented value.

Perturbations are seeded from the run seed (via `derive_seed`), so a stressed run
is as reproducible as the baseline.

## Perturbation types

Two families live in `src/context_engineering_lab/perturbations/`.

**Injection** (`injection.py`) — *adds* competing candidate items:

- `distractor-injection` — on-topic-but-irrelevant items that repeat the query
  terms and carry high salience and recent timestamps, tempting content-, salience-
  and recency-based selectors to spend budget on noise.
- `contradiction-injection` — on-topic items flagged `conflicting`, designed to be
  kept by selectors that cannot tell a conflicting fact from the real one (raising
  `conflict_selection_rate`).
- `stale-amplification` — repeated stale / superseded items with old timestamps and
  a high `frequency`, modelling an obsolete fact that keeps resurfacing and tempting
  frequency-sensitive policies (raising `stale_selection_rate` and
  `superseded_fact_retention`).

**Corruption** (`corruption.py`) — *rewrites* observable signals on existing items,
pushing each toward its misleading extreme (down on relevant items, up on
irrelevant ones), scaled by `intensity`:

- `source-quality-corruption` — distorts the `source_quality` signal, misleading a
  quality-aware attention allocator.
- `salience-corruption` — distorts the `salience` signal, misleading a
  salience-aware retention policy or allocator.

## Robustness metrics

The [robustness metrics](../src/context_engineering_lab/core/robustness_metrics.py)
are intentionally simple and operate on *oriented* values (higher is better; cost
metrics are negated first):

- `degradation(baseline, perturbed) = baseline - perturbed` — positive means the
  perturbation hurt. `degradation_under_noise` and `degradation_under_conflict` are
  named aliases so a report can attribute a drop to a specific stressor.
- `robustness_score(baseline, perturbed) = clamp(perturbed / baseline, 0, 1)` — the
  fraction of baseline performance retained; `1.0` means no degradation.

`perturbations/comparison.py` lines up matching `(strategy, metric)` cells between a
baseline and a perturbed aggregation; `perturbations/aggregation.py` groups those
comparisons by stress group and also computes **oracle-gap shifts** — how far each
strategy sits below the oracle on a benchmark's primary metric, baseline vs
perturbed, and whether that gap widened.

## Stress groups

`experiments/phase10.py` defines four stress groups, each reusing a Phase 8 preset
and the Phase 8 curated lineups verbatim:

| group | benchmark | perturbation(s) |
| --- | --- | --- |
| `distractor-stress` | `email-old-signal` | `distractor-injection` |
| `contradiction-stress` | `revision-current-truth` | `contradiction-injection` |
| `stale-amplification` | `memory-log-noisy` | `stale-amplification` |
| `corruption-stress` | `support-stale-fix` | `source-quality-corruption`, `salience-corruption` |

## Reproducibility

```bash
context-lab run-phase10 --output artifacts/phase10
```

runs each baseline and perturbed experiment, writes every result as
`artifacts/phase10/<group>-<run>.json`, and writes the robustness report to
`artifacts/phase10/robustness.md`. Output is deterministic: run ids derive from the
configuration, seeds are fixed, perturbations are seeded, and tables are sorted, so
reruns diff cleanly.

## Reporting rules

Every statement in the report names the **strategy**, **benchmark**,
**perturbation**, and **metric** it refers to, e.g. *"Under `contradiction-injection`
on the `revision-current-truth` benchmark, `temporal->selection` showed the largest
degradation in `conflict_selection_rate`."* Blanket labels such as "strategy X is
fragile" are deliberately avoided.

## Limitations

- Results reflect only the four stress groups, the chosen perturbation intensities
  and counts, and the Phase 8 seeds and budgets; they do not characterise a strategy
  in general.
- Corruption is adversarial by construction (it reads ground truth to point the
  signal the wrong way); it measures worst-case signal reliance, not average noise.
- Degradation compares oriented means over budgets; it does not separate which
  budget drove a drop.
- Injection counts and corruption intensity are fixed defaults, not swept.
- `oracle` strategies are upper bounds; their gaps describe headroom, not a
  deployable result.
