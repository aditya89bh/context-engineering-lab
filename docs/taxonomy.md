# Experiment taxonomy

This taxonomy organizes the space of experiments so that each one has a clear
home, a clear question, and clear neighbors to compare against. It also guards
against a real risk: producing many experiments that are superficially different
but investigate the same thing.

Experiments are classified along two axes: the **operation** under study and the
**question family** being asked.

## Axis 1: operation

| Operation | Core decision | Example strategies |
| --- | --- | --- |
| Salience | How valuable is this item? | recency, frequency, novelty, semantic relevance, learned scoring |
| Selection | Which items survive the budget? | top-k, greedy marginal-gain, diversity-aware (MMR-style) |
| Compression | How do we shrink while preserving value? | extractive summary, abstractive summary, deduplication, clustering |
| Temporal | How does time change value? | exponential decay, power-law decay, staleness detection |
| Forgetting | What should leave the store? | LRU, lowest-salience eviction, decayed eviction, capacity policies |
| Attention budget | How is a fixed budget allocated? | uniform, proportional-to-salience, knapsack allocation |
| Robustness | Does it survive adversarial input? | distractor resistance, poisoning resistance, shift tolerance |

## Axis 2: question family

Each experiment belongs to exactly one question family. The family determines
what a "result" looks like.

1. **Existence** — *Does strategy X ever help?* Establishes whether an effect is
   real under favorable conditions. The weakest claim; a necessary first step.
2. **Comparison** — *Does X beat baseline B (or rival X')?* The default family.
   Requires matched budgets and shared benchmarks.
3. **Boundary** — *Where does X stop helping?* Maps the budget-performance curve
   or the point at which compression/forgetting begins to hurt.
4. **Mechanism** — *Why does X help or fail?* Uses ablations and controlled
   perturbations to attribute the effect to a cause.
5. **Robustness** — *Does X survive adversarial or shifted input?* Stresses a
   strategy that already works under benign conditions.

## The experiment matrix

Crossing the two axes yields the space of candidate experiments. Not every cell
is worth filling. A cell is worth an experiment only if it asks something we do
not already know and cannot trivially predict.

The flagship questions for the lab (to be addressed across implementation
phases, not now) sit in these cells:

- **Selection × Boundary** — *How much can we cut before the task breaks?*
- **Compression × Boundary** — *How aggressively can we compress safely?*
- **Forgetting × Comparison** — *Does active forgetting beat keeping everything?*
- **Temporal × Mechanism** — *Is recency a good proxy, or does it just correlate
  with relevance?*
- **Attention budget × Comparison** — *Does salience-proportional allocation beat
  uniform allocation?*
- **Robustness × Robustness** — *Which selection strategies resist distractors
  and poisoning?*

## Anti-redundancy rule

Before a new experiment is added, it must be placed in a cell and justified
against existing occupants of that cell. If an experiment cannot articulate how
it differs from its neighbors in both operation and question family, it is a
duplicate and is omitted. This rule exists to keep the repository's value in
insight density, not file count.

## Naming convention

Experiments are named `<operation>-<question>-<short-handle>`, e.g.
`selection-boundary-token-cliff` or `temporal-mechanism-recency-vs-relevance`.
The name encodes its place in the taxonomy so the catalog stays navigable.
