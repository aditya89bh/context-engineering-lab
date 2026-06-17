# Findings

Interpretation of the evidence in [RESULTS.md](RESULTS.md). Each finding names the
benchmark, strategy, and metric it rests on. These are readings of *these
synthetic benchmarks*, not claims about production systems; see
[LIMITATIONS.md](LIMITATIONS.md).

## 1. No single strategy wins everywhere; the right primitive is benchmark-shaped

The best non-oracle strategy changes with the benchmark, often inverting:

- In temporal selection, `recency` scores mean `answer_support` 0.50 on
  `recent-signal` but 0.00 on `old-signal`, while `oldest-first` does the
  reverse (0.00 then 0.50). The two are mirror images because each encodes one
  assumption about where the signal sits in time.
- In attention allocation, `uniform-allocation` leads `signal_capture_rate` on
  `balanced-sources` (0.72) but is the weakest allocator on `concentrated-signal`
  (0.64), where `winner-take-most-0.7` leads (0.89). Concentration in the data
  rewards concentration in the policy.
- In compression, `head-truncation` retains 0.06 of target `information_retention`
  on `late-signal-compression` versus `tail-truncation`'s 0.94, and the ranking
  flips on `easy-compression` (1.00 vs 0.25).

Reading: each deployable strategy is a bet about the structure of the input.
When the bet matches the benchmark it can reach the oracle; when it does not, it
collapses. This is the central reason the lab measures per-benchmark gaps rather
than a single leaderboard.

## 2. Query-aware selection closes the gap only when the signal is lexical

`keyword-overlap` matches the oracle on `easy-selection` (mean `answer_support`
1.00) and on the naturalistic `email-old-signal`, `meeting-action-items`,
`memory-log-noisy`, `support-stale-fix`, and `revision-current-truth` scenarios
(oracle `answer_support` 1.00 reached by at least one query-aware path). But on
`high-distractor-selection` it falls to 0.21 — below even content-blind `last-n`
(0.25) — because the distractors share the query's vocabulary. Lexical overlap
helps exactly when relevance is lexical, and misleads when distractors imitate it.

## 3. Forgetting helps, but only salience-based forgetting

On the retention benchmarks, `salience-retention` reaches the oracle ceiling on
`low-noise-retention` (mean `forgetting_efficiency` 0.60) and `stale-accumulation`
(0.83), and improves over keeping everything on `harmful-memory` (0.24, vs the
0.57 ceiling). `recency-retention` is *negative* on all three
(-0.48, -0.56, -0.41): forgetting by age alone discards useful items and keeps
harmful recent ones. Forgetting is beneficial here only when it is driven by an
estimate of value, not by time.

## 4. Composition trades recall for safety, and the trade is benchmark-dependent

On `balanced-interaction`, every composition that adds a retention or temporal
stage reduces `harmful_retention_rate` relative to a single primitive
(`retention->selection`: 1.00 → 0.61; `retention->attention`: 0.86 → 0.60), but
some pay for it in `selection_recall` (`temporal->retention`: 0.88 → 0.49). On
`memory-pressure`, the trade pays off cleanly: `retention->selection` reaches mean
`answer_support` 0.75, equal to `oracle-pipeline`, where `keyword-overlap` and
`attention->selection` reach 0.00. Pipelines are not universally better; they
help when a later stage removes the failure mode an earlier stage is blind to.

## 5. Across all benchmarks, retention-led strategies sit closest to the oracle

The synthesis confirms the per-benchmark picture in aggregate.
`retention->selection` has the highest net dominance among deployable strategies
(+353) and the smallest oracle gap (normalized 0.942, primary gap 0.058);
`salience-retention` is second (net +333, normalized 0.930). The lexical and
time-only strategies sit at the bottom: `keyword-overlap` (net -342),
`recency-retention` (net -384, win rate 0.021), and `temporal->selection`
(net -474). The strategies that estimate item value generalize across the
benchmark families; the ones keyed to a single surface cue do not.

## 6. Robustness tracks *what signal a strategy trusts*, not its average quality

The perturbation study shows that a strategy's fragility is predicted by the
signal it depends on:

- `salience-retention`, strong on average, suffers the single largest degradation
  in the suite: on `support-stale-fix` under `salience-corruption`,
  `answer_support` drops 1.000 → 0.000, because the perturbation attacks the exact
  signal it ranks by, and its oracle gap widens from 0.000 to 1.000.
- `temporal->selection` degrades 0.812 in `conflict_selection_rate` on
  `revision-current-truth` under `contradiction-injection`: injecting conflicting
  revisions defeats a time-ordered policy.
- `attention->selection` is the most sensitive on average (mean degradation 0.305
  over 10 comparisons), driven by `source-quality-corruption` and
  `salience-corruption` on `support-stale-fix` (`answer_support` 1.000 → 0.500 and
  → 0.681).
- `keyword-overlap` and `oracle` are the least sensitive (mean degradation 0.004):
  under `distractor-injection` on `email-old-signal`, `keyword-overlap` holds
  `answer_support` at 0.750. Distractors that do not match the query simply do not
  move a lexical selector.

Reading: the same value-estimating strategies that lead on clean benchmarks
(Finding 5) are the ones most exposed when their input signal is corrupted. Mean
quality and robustness are different axes, and a release-quality recommendation
needs both — measured per benchmark and per perturbation.
