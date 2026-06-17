# Results

Measured evidence from the benchmark suite. This document reports **numbers
only**; interpretation lives in [FINDINGS.md](FINDINGS.md) and the boundaries in
[LIMITATIONS.md](LIMITATIONS.md). Every figure is specific to these synthetic
benchmarks, seeds, and budgets, and regenerates deterministically.

All tables below were produced by:

```bash
context-lab run-phase2  --output artifacts/phase2
context-lab run-phase3  --output artifacts/phase3
context-lab run-phase4  --output artifacts/phase4
context-lab run-phase5  --output artifacts/phase5
context-lab run-phase6  --output artifacts/phase6
context-lab run-phase7  --output artifacts/phase7
context-lab run-phase8  --output artifacts/phase8
context-lab run-phase9  --output artifacts/phase9
context-lab run-phase10 --output artifacts/phase10
```

`oracle*` strategies read ground truth and are ceilings, not deployable. Means
are over seeds `{1, 2, 3}` and the benchmark's budget sweep unless noted.

## Selection (Phase 2)

Mean `answer_support` over seeds and budgets:

| benchmark | first-n | last-n | recency | random | keyword-overlap | oracle |
| --- | --- | --- | --- | --- | --- | --- |
| `easy-selection` | 0.57 | 0.54 | 0.54 | 0.57 | 1.00 | 1.00 |
| `position-biased-selection` | 0.25 | 1.00 | 1.00 | 0.41 | 1.00 | 1.00 |
| `high-distractor-selection` | 0.22 | 0.25 | 0.25 | 0.19 | 0.21 | 1.00 |

On `high-distractor-selection`, every non-oracle strategy stays at or below 0.25
mean `answer_support` while `oracle` is 1.00.

## Compression (Phase 3)

Mean `information_retention` and mean `compression_ratio` (lower ratio = more
compression):

| benchmark | metric | no-compression | head-truncation | tail-truncation | keyword-preserving | sentence-boundary | oracle-compression |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `easy-compression` | information_retention | 1.00 | 1.00 | 0.25 | 1.00 | 0.75 | 1.00 |
| `late-signal-compression` | information_retention | 1.00 | 0.06 | 0.94 | 0.50 | 0.00 | 1.00 |
| `dense-distractor-compression` | information_retention | 1.00 | 0.44 | 0.31 | 0.56 | 0.25 | 1.00 |
| `dense-distractor-compression` | compression_ratio | 1.00 | 0.31 | 0.31 | 0.31 | 0.25 | 0.08 |

On `late-signal-compression`, `head-truncation` retains 0.06 of the target
information versus `tail-truncation` at 0.94; the ordering reverses on
`easy-compression` (1.00 vs 0.25).

## Temporal (Phase 4)

Mean `answer_support`:

| benchmark | recency | oldest-first | fixed-window-5 | age-weighted-hl4 | oracle-temporal |
| --- | --- | --- | --- | --- | --- |
| `recent-signal` | 0.50 | 0.00 | — | — | 0.50 |
| `old-signal` | 0.00 | 0.50 | — | — | 0.50 |
| `drift-heavy` (sweep) | 0.00 | — | — | 0.12 | 0.62 |

`recency` scores 0.50 on `recent-signal` and 0.00 on `old-signal`;
`oldest-first` is the mirror image (0.00 then 0.50).

## Retention (Phase 5)

Mean `forgetting_efficiency` (higher is better; negative means worse than keeping
everything):

| benchmark | salience-retention | recency-retention | oracle-retention |
| --- | --- | --- | --- |
| `low-noise-retention` | 0.60 | -0.48 | 0.60 |
| `stale-accumulation` | 0.83 | -0.56 | 0.83 |
| `harmful-memory` | 0.24 | -0.41 | 0.57 |

`salience-retention` matches `oracle-retention` on `low-noise-retention` (0.60)
and `stale-accumulation` (0.83) but trails it on `harmful-memory` (0.24 vs 0.57).
`recency-retention` is negative on all three.

## Attention (Phase 6)

Mean `signal_capture_rate`:

| benchmark | uniform-allocation | proportional-allocation | winner-take-most-0.7 | oracle-allocation |
| --- | --- | --- | --- | --- |
| `balanced-sources` | 0.72 | — | 0.49 | 0.72 |
| `concentrated-signal` | 0.64 | — | 0.89 | 0.89 |
| `noisy-dominant-source` | — | 0.47 | 0.78 | 0.79 |

The best non-oracle allocator flips by benchmark: `uniform-allocation` leads on
`balanced-sources` (0.72), `winner-take-most-0.7` leads on `concentrated-signal`
(0.89) and `noisy-dominant-source` (0.78).

## Interaction (Phase 7)

On `balanced-interaction`, composing primitives lowers `harmful_retention_rate`
relative to a single primitive, sometimes at a cost in `selection_recall`:

| comparison (benchmark `balanced-interaction`) | metric | from | to |
| --- | --- | --- | --- |
| `retention->selection` vs `keyword-overlap` | harmful_retention_rate | 1.00 | 0.61 |
| `temporal->selection` vs `keyword-overlap` | selection_recall | 0.69 | 0.44 |
| `retention->attention` vs `adaptive-allocation` | harmful_retention_rate | 0.86 | 0.60 |
| `temporal->retention` vs `frequency-retention` | selection_recall | 0.88 | 0.49 |

On `memory-pressure`, `retention->selection` reaches mean `answer_support` 0.75
(equal to `oracle-pipeline`) while `keyword-overlap` and `attention->selection`
reach 0.00.

## Naturalistic (Phase 8)

On `naturalistic-email` (`email-old-signal`), relative to `keyword-overlap`:

| strategy | conflict_selection_rate | harmful_retention_rate | stale_selection_rate |
| --- | --- | --- | --- |
| keyword-overlap (ref) | 0.60 | 0.75 | 0.48 |
| recency | 0.16 | 0.68 | 0.05 |
| salience-retention | 0.21 | 0.60 | 0.11 |
| retention->selection | 0.33 | 0.62 | 0.24 |

On `revision-current-truth`, `temporal->selection` drives
`conflict_selection_rate` and `superseded_fact_retention` to 0.00 (from 0.52 and
0.70 under `keyword-overlap`) while holding `answer_support` at 1.00. On
`memory-log-noisy`, `salience-retention` cuts `harmful_retention_rate` to 0.28
(from 0.58) at mean `answer_support` 0.91.

## Cross-benchmark synthesis (Phase 9)

Aggregated over 23 benchmarks, 35 strategy ids, 26 metrics, 4696 cells.

Dominance (wins/losses/ties over shared `(benchmark, metric, budget)` cells, cost
metrics oriented so higher is better) — best and worst non-oracle deployable
strategies by net:

| strategy | wins | losses | ties | net | win rate |
| --- | --- | --- | --- | --- | --- |
| retention->selection | 589 | 236 | 599 | 353 | 0.414 |
| salience-retention | 469 | 136 | 435 | 333 | 0.451 |
| frequency-retention | 605 | 363 | 376 | 242 | 0.450 |
| keyword-overlap | 310 | 652 | 702 | -342 | 0.186 |
| recency-retention | 10 | 394 | 76 | -384 | 0.021 |
| temporal->selection | 301 | 775 | 348 | -474 | 0.211 |

Oracle gap on each benchmark's primary metric (normalized = strategy / oracle;
deployable strategies only, smallest gaps first):

| strategy | normalized | primary gap |
| --- | --- | --- |
| retention->selection | 0.942 | 0.058 |
| salience-allocation | 0.938 | 0.048 |
| salience-retention | 0.930 | 0.053 |
| winner-take-most-0.7 | 0.889 | 0.081 |
| keyword-overlap | 0.765 | 0.227 |
| temporal->selection | 0.411 | 0.574 |

Stability — lowest and highest seed variance among deployable strategies:
`keyword-overlap` 0.002, `retention->selection` 0.007 (steady); `last-n` 0.033,
`first-n` 0.027 (variable). Budget sensitivity ranges from 0.000
(`no-compression`, `keyword-preserving`) to 0.963
(`hybrid-retention-0.5-0.3-0.2`).

## Robustness (Phase 10)

Strategy sensitivity (mean / worst degradation across all
`(benchmark, perturbation, metric)` comparisons):

| strategy | comparisons | mean degradation | worst degradation |
| --- | --- | --- | --- |
| attention->selection | 10 | 0.305 | 0.500 |
| salience-retention | 26 | 0.131 | 1.000 |
| recency | 26 | 0.065 | 0.592 |
| temporal->selection | 26 | 0.064 | 0.812 |
| retention->selection | 26 | 0.011 | 0.399 |
| keyword-overlap | 26 | 0.004 | 0.181 |
| oracle | 26 | 0.004 | 0.087 |

Largest single degradations, each tagged by strategy / benchmark / perturbation /
metric:

| strategy | benchmark | perturbation | metric | baseline | perturbed | degradation |
| --- | --- | --- | --- | --- | --- | --- |
| salience-retention | support-stale-fix | salience-corruption | answer_support | 1.000 | 0.000 | 1.000 |
| temporal->selection | revision-current-truth | contradiction-injection | conflict_selection_rate | 0.000 | 0.812 | 0.812 |
| attention->selection | support-stale-fix | source-quality-corruption | answer_support | 1.000 | 0.500 | 0.500 |
| retention->selection | memory-log-noisy | stale-amplification | stale_selection_rate | 0.154 | 0.553 | 0.399 |
| recency | email-old-signal | distractor-injection | answer_support | 0.250 | 0.000 | 0.250 |

Oracle gap under perturbation (primary metric `answer_support`): it widened most
for `salience-retention` on `support-stale-fix` under `salience-corruption`
(0.000 → 1.000), and for `temporal->selection` on `revision-current-truth` under
`contradiction-injection` (0.000 → 0.552). Under `distractor-injection` on
`email-old-signal`, `keyword-overlap` did not degrade on `answer_support`
(0.750 → 0.750).
