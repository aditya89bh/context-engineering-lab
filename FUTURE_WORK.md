# Future work

Directions that extend this lab without abandoning what makes it useful:
determinism, isolation of one decision at a time, and oracle-anchored measurement.
These are open questions and natural extensions, not committed roadmap items —
development of the current artifact ends at Phase 11.

## Open questions raised by the results

- **Why does value-estimation generalize but surface cues do not?**
  `retention->selection` and `salience-retention` sit closest to the oracle across
  benchmarks (RESULTS, Phase 9), while `keyword-overlap` and `recency` do not. Is
  the advantage intrinsic to estimating item value, or an artifact of how the
  generators encode value? A generator ablation that varies how much signal is
  lexical vs. salience-bearing would separate the two.
- **Can a strategy be both strong and robust?** The strategies that lead on clean
  benchmarks are often the most fragile under perturbation (FINDINGS 6:
  `salience-retention` degrades `answer_support` 1.000 → 0.000 under
  `salience-corruption`). Is there a strategy on the Pareto frontier of mean
  quality *and* worst-case degradation, or is the trade-off fundamental for these
  benchmarks?
- **When does composition help rather than hurt?** Pipelines help on
  `memory-pressure` but cost recall on `balanced-interaction` (FINDINGS 4). A
  predictive account — given a benchmark's structure, which composition order
  wins — would turn the current case-by-case observations into a rule.

## Natural extensions within scope

- **More perturbations.** The five current perturbations are not an exhaustive
  adversary model (LIMITATIONS). Order shuffling, partial-relevance noise, budget
  shocks, and adversarial paraphrase of the query would broaden the robustness
  picture while staying deterministic.
- **Cost-aware budgets.** Budgets are currently item- or token-counts. A unit that
  models heterogeneous item cost would let the harness study quality-per-cost
  rather than quality-per-slot.
- **Confidence intervals.** Replacing small multi-seed means with bootstrapped
  intervals over more seeds would make cross-strategy gaps defensible rather than
  indicative.
- **Sensitivity surfaces.** The synthesis reports single stability numbers; a
  systematic sweep over generator parameters (distractor density, signal position,
  staleness rate) would map where each strategy's assumptions break.

## Larger research directions

- **Validation on real data.** The decisive next step is to re-test the
  hypotheses from FINDINGS on real corpora (email, tickets, code-review threads)
  with the same oracle-gap framing. The benchmarks here are a hypothesis
  generator; only real data can confirm transfer.
- **Learned strategies.** Every strategy here is hand-written. A learned selector
  or retention policy, trained on one generator and tested on another (and under
  perturbation), would test whether learning recovers the oracle gap or merely
  overfits the generator.
- **Bridging to model context windows.** The abstractions (items, budgets,
  selection, compression) map onto real context-window management. Connecting the
  harness to an actual long-context model — strictly behind the existing
  no-network boundary, e.g. via a local model — would be the bridge from
  controlled study to applied tool.

## How to propose any of this

These extensions should follow the existing bar: a clear question, a deterministic
benchmark, an oracle and content-blind baselines, and benchmark-specific claims.
See [CONTRIBUTING.md](CONTRIBUTING.md) and
[docs/definition-of-done.md](docs/definition-of-done.md).
