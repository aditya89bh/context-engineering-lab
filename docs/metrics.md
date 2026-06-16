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
