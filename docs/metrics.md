# Metrics framework

Metrics turn experimental outcomes into numbers we can compare. This lab
measures along three orthogonal dimensions — **quality**, **cost**, and
**robustness** — and refuses to collapse them into a single score by default. A
strategy is described by where it sits in this three-dimensional space, not by a
single rank.

## Dimension 1: quality

Quality measures how well the consumer performs the task given the context the
strategy produced.

- **Task success** — the primary, task-defined outcome (accuracy, exact match,
  success rate). Always reported.
- **Answer support** — whether the items needed to succeed were actually present
  in context (selection recall). Distinguishes "wrong selection" from "right
  selection, wrong consumer."
- **Selection precision/recall** — for tasks with known-relevant items, how much
  of the budget was spent on relevant vs. irrelevant items.
- **Information retention** — for compression, how much task-relevant information
  survives, measured against an uncompressed reference.

## Dimension 2: cost

Cost measures what the strategy consumed to achieve its quality. Quality without
cost is meaningless under a budget.

- **Context size** — tokens (or items/bytes) actually placed in context. The
  budget is the constraint; this is the consumption.
- **Compute cost** — wall-clock latency and, where relevant, model calls incurred
  by the strategy itself (e.g. an abstractive compressor that calls a model).
- **Memory footprint** — store size for forgetting/eviction experiments.
- **Budget efficiency** — quality achieved per unit of budget; the slope of the
  budget-performance curve.

## Dimension 3: robustness

Robustness measures how quality degrades when conditions worsen.

- **Distractor sensitivity** — drop in quality as the proportion of distractors
  rises.
- **Poisoning sensitivity** — drop in quality as poisoned items are introduced.
- **Shift tolerance** — quality retained under distribution shift between tuning
  and evaluation.
- **Variance** — spread of outcomes across seeds; a strategy with high variance
  is less trustworthy even if its mean is high.

## Formal definitions

The notation below is shared by all experiments so that metric names mean the
same thing everywhere. For a single task instance, let:

- `R` = the set of items that are genuinely relevant to the task (ground truth).
- `S` = the set of items the strategy placed in context (the selection), subject
  to the budget `B`.
- `D` = the set of distractor items available in the instance.
- `P` = the set of poisoned items available in the instance.
- `q(·)` = task success of the consumer given a context, in `[0, 1]`.

All instance-level metrics are averaged over instances and over seeds; report the
mean with a measure of spread.

### Selection precision

Fraction of selected items that are relevant — how little of the budget was
wasted on irrelevant items.

```
selection_precision = |S ∩ R| / |S|          (defined when |S| > 0)
```

### Selection recall

Fraction of relevant items that were selected — how much of what mattered made
it into context.

```
selection_recall = |S ∩ R| / |R|             (defined when |R| > 0)
```

### Answer support

Whether *all* items required to answer were present in context. This is a
stricter, task-facing companion to recall: a strategy can have high recall yet
still miss the one item the answer depends on. Let `R_req ⊆ R` be the minimal set
required to succeed.

```
answer_support = 1 if R_req ⊆ S else 0
```

Averaged over instances, `answer_support` is the rate at which the consumer was
*given the chance* to succeed; comparing it to task success isolates selection
failures from consumer failures.

### Budget efficiency

Quality gained per unit of budget spent. Defined pointwise and as a slope of the
budget-performance curve `q(B)`.

```
budget_efficiency(B)      = q(B) / B                       (quality per unit budget)
marginal_efficiency(B)    = [q(B + ΔB) − q(B)] / ΔB        (local slope of the curve)
```

Report the marginal form where diminishing returns matter; it identifies the
budget beyond which extra context stops paying for itself.

### Distractor sensitivity

Rate at which quality falls as the distractor fraction `f_d` increases.
Estimated as the negative slope of `q` with respect to `f_d` (least squares over
a sweep); larger means more fragile.

```
f_d = |D| / (|R| + |D|)                       (distractor fraction)
distractor_sensitivity = − slope( q  vs.  f_d )
```

A value near `0` means the strategy is robust to distractors; large positive
values mean it is easily captured by plausible-but-irrelevant items.

### Poisoning sensitivity

Analogous to distractor sensitivity, but for actively harmful items at poisoning
fraction `f_p`.

```
f_p = |P| / (|R| + |P|)                       (poisoning fraction)
poisoning_sensitivity = − slope( q  vs.  f_p )
```

Also report the **poisoning tolerance**: the largest `f_p` at which `q(f_p)`
stays above a pre-registered failure threshold `τ`.

```
poisoning_tolerance = max { f_p : q(f_p) ≥ τ }
```

### Area under the budget-performance curve (AUBPC)

A single summary of a strategy's quality across the whole budget range, rather
than at one point. For budgets sampled at `B_0 < B_1 < ... < B_n` with qualities
`q_i = q(B_i)`, approximate the area by the trapezoidal rule and normalize by the
budget span so AUBPC lies in `[0, 1]` and is comparable across experiments.

```
AUBPC = ( Σ_{i=1..n} (B_i − B_{i-1}) · (q_i + q_{i-1}) / 2 ) / (B_n − B_0)
```

Higher AUBPC means better quality sustained across budgets. Because it can hide a
cliff, always report AUBPC *alongside* the curve and the location of any cliff,
never as a replacement for them.

## Reporting conventions

**Curves over points.** Where a budget is involved, report the
budget-performance curve. Summarize a curve with the area under it and the
location of any cliff, not a single point.

**Central tendency with spread.** Every reported metric includes a measure of
spread across seeds (standard deviation or a bootstrap interval). A mean without
a spread is not reportable.

**Effect sizes, not just means.** When comparing two strategies, report the
difference and its uncertainty, so readers can judge whether a gap is real.

**Cost always accompanies quality.** No quality number is reported in isolation
from its cost.

## Composite scores

Composite scores (a single number summarizing quality, cost, and robustness)
are permitted only as a convenience for ranking, never as the basis for a claim.
When used, the weighting is stated explicitly, and the underlying per-dimension
numbers are always shown alongside. We assume readers will disagree with any
particular weighting and give them the components to reweight themselves.

## Statistical discipline

- **Seeds are varied, not fixed-and-forgotten.** Each configuration is run over
  multiple seeds; results report the distribution.
- **Multiple comparisons are acknowledged.** When many strategies are compared,
  we are explicit that some apparent winners are noise, and we prefer
  pre-registered primary comparisons.
- **Negative and null results are reported** with the same rigor as positive
  ones. "No significant difference" is a finding.
