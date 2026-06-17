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

### Compression metrics (Phase 3)

Compression transforms item *content* to reduce its cost while preserving
task-relevant information. The Phase 3 compression benchmark embeds ground-truth
**facts** in content as tokens (see `benchmarks/facts.py`), so fidelity is scored
by which facts survive. For a single case, let:

- `L_o` = original content length (tokens); `L_c` = compressed content length.
- `T` = the set of target facts in the original (required ∪ optional).
- `R_f ⊆ T` = the required facts (the minimal set needed to answer).
- `D_f` = the set of distractor facts in the original.
- `K` = the set of facts present after compression (the retained facts).
- `U` = the cost actually used by the produced context; `B` = the budget limit.

**Compression ratio** — compressed size relative to the original. Lower is more
aggressive; `1.0` means no reduction.

```
compression_ratio = L_c / L_o                (defined when L_o > 0)
```

**Information retention** — fraction of target facts that survive compression.

```
information_retention = |T ∩ K| / |T|        (defined when |T| > 0)
```

**Answer support after compression** — whether *all* required facts survived. A
stricter, task-facing companion to retention.

```
answer_support_after_compression = 1 if R_f ⊆ K else 0   (defined when |R_f| > 0)
```

**Distractor retention** — fraction of distractor facts that survive. Lower is
better: a good compressor discards distractors rather than laundering them into
the output.

```
distractor_retention = |D_f ∩ K| / |D_f|     (defined when |D_f| > 0)
```

**Budget utilization** — fraction of the budget consumed. May exceed `1.0` for a
strategy that does not honor the budget (e.g. the no-compression baseline).

```
budget_utilization = U / B                   (defined when B > 0)
```

These are deliberately *not* combined into a composite score. A compressor is
described by where it sits across retention, ratio, distractor retention, and
utilization — for example, the oracle ceiling attains full retention at a very
low ratio because it keeps only the target facts.

### Temporal metrics (Phase 4)

The temporal benchmark (`temporal-context-relevance`) places items along a
timeline and asks which to keep under a budget. These metrics describe *where in
time* a selection lands, which the set-overlap metrics above ignore. For a single
case, let:

- `now` = the largest timestamp (the timeline's reference time).
- `age(x) = now - timestamp(x)` = the age of item `x` (`0` for the newest item).
- `span` = the timeline span used to normalize ages (`now - min timestamp`).
- `S` = the selected items; `R` = the ground-truth relevant items.
- `stale` = the items flagged stale (old, no longer relevant).
- `[a_lo, a_hi]` = the closed interval of ages spanned by `R` (its age band).

**Temporal relevance** — fraction of the selection whose age falls in the
relevant age band. An item can be in the right *era* without itself being the
signal, so this is distinct from precision.

```
temporal_relevance = |{ x ∈ S : a_lo ≤ age(x) ≤ a_hi }| / |S|   (defined when |S| > 0)
```

**Stale selection rate** — fraction of the selection that is stale. Lower is
better: it penalizes keeping dated look-alikes.

```
stale_selection_rate = |S ∩ stale| / |S|        (defined when |S| > 0)
```

**Age of selected context** — mean normalized age of the selection. Describes how
old, on average, the kept context is.

```
age_of_selected_context = mean_{x ∈ S} age(x) / span   (defined when |S| > 0, span > 0)
```

**Relevant age gap** — normalized distance in time between the average selected
item and the average relevant item. `0` means the selection is temporally aligned
with where relevance actually is; larger means the selector is looking in the
wrong era.

```
relevant_age_gap = | mean_{x ∈ S} age(x) − mean_{x ∈ R} age(x) | / span
                                                 (defined when |S| > 0, |R| > 0, span > 0)
```

These are deliberately *not* combined into a composite score. A temporal strategy
is described by where it sits across answer support, the age gap, the stale rate,
and budget utilization — for example, oldest-first attains a small age gap on an
old signal precisely where recency's gap is largest.

### Retention metrics (Phase 5)

The retention benchmark (`retention-utility-preservation`) holds a small memory of
items of four kinds and asks which to *keep* under a memory budget. Phase 5 studies
forgetting as a policy; these metrics describe how cleanly a policy keeps useful
items and forgets harmful ones. Forgetting is **distinct from temporal relevance**:
old items may still be useful and recent items may be harmful, so these metrics
partition by ground-truth *utility*, not age. For a single case, let:

- `U` = the ground-truth useful items; `U_req ⊆ U` = the required (must-keep)
  subset.
- `H` = the ground-truth harmful items.
- `R` = the items the policy kept (the retention); `B` = the memory budget limit.

**Retention precision** — fraction of kept items that are useful. Higher means a
cleaner memory.

```
retention_precision = |R ∩ U| / |R|             (defined when |R| > 0)
```

**Retention recall** — fraction of *required* useful items kept. The graded,
task-facing companion to `answer_support` (which is all-or-nothing over `U_req`).

```
retention_recall = |R ∩ U_req| / |U_req|        (defined when |U_req| > 0)
```

**Useful retention rate** — fraction of *all* useful items kept. The survival rate
of the broad useful population, the counterpart to `harmful_retention_rate`.

```
useful_retention_rate = |R ∩ U| / |U|           (defined when |U| > 0)
```

**Harmful retention rate** — fraction of harmful items kept. Lower is better: a
good policy forgets harm. Reported as `0` when a case has no harmful items.

```
harmful_retention_rate = |R ∩ H| / |H|          (defined when |H| > 0)
```

**Memory budget utilization** — fraction of the memory budget consumed. May exceed
`1.0` for a policy that does not honor the budget (e.g. the retain-all reference).

```
memory_budget_utilization = |R| / B             (defined when B > 0)
```

**Forgetting efficiency** — useful survival minus harmful survival. This is a
transparent *contrast*, not a composite quality score: it is positive when a
policy keeps more of the useful than of the harmful, `0` when it cannot tell them
apart, and negative when it preferentially keeps harm. Its two component rates are
always reported alongside it (the harmful term is `0` when `H` is empty).

```
forgetting_efficiency = useful_retention_rate − harmful_retention_rate
                                                (defined when |U| > 0)
```

These are deliberately *not* combined into a single quality score. A retention
policy is described by where it sits across these rates — for example, on a
low-noise benchmark a salience policy approaches the oracle's forgetting
efficiency while a frequency policy retains high-frequency harm.

### Attention-allocation metrics (Phase 6)

The attention benchmark (`attention-source-allocation`) splits a budget across
several **sources** before a fixed inner selection fills each share. Phase 6
studies allocation as a policy; these metrics describe how well a budget split
converted into captured signal. Allocation is **distinct from selection**: the
inner selection is identical for every allocator, so these metrics isolate the
quality of the split. For a single case, let:

- `G` = the ground-truth signal items across all sources.
- `S` = the items actually placed in context (the union of filled shares).
- `B` = the total budget (in items).
- `C` = the set of sources that contributed at least one selected item;
  `srcs` = all sources in the case.

**Allocation efficiency** — fraction of selected items that are signal. The
precision of where attention landed.

```
allocation_efficiency = |S ∩ G| / |S|          (defined when |S| > 0)
```

**Signal capture rate** — fraction of all available signal captured. The recall
of the allocation across every source.

```
signal_capture_rate = |S ∩ G| / |G|            (defined when |G| > 0)
```

**Wasted attention rate** — fraction of the budget that did not become signal.
Lower is better. Because `|S ∩ G| ≤ |S| ≤ B`, this captures budget lost both to
selected distractors and to capacity an allocator handed a source that could not
fill it.

```
wasted_attention_rate = (B − |S ∩ G|) / B      (defined when B > 0)
```

**Source coverage** — fraction of sources that contributed a selected item. A
descriptor of spread, not a quality score: concentrating on the right source can
beat broad coverage.

```
source_coverage = |C ∩ srcs| / |srcs|          (defined when |srcs| > 0)
```

**Budget utilization** — fraction of the budget actually filled (reused from the
compression metrics). Below `1` when an allocator wasted budget on a source too
small to fill its share.

```
budget_utilization = |S| / B                   (defined when B > 0)
```

These are deliberately *not* combined into a single quality score. An allocator
is described by where it sits across capture, efficiency, waste, and coverage —
for example, on a concentrated signal a winner-take-most split approaches the
oracle's capture while uniform wastes budget on near-empty sources.

## Interaction metrics (Phase 7)

Phase 7 chains existing primitives into pipelines and measures how a composition
compares to its parts on the `interaction-context-pipeline` benchmark. It reuses
the selection, retention, and temporal metrics above; the only metric scored
per case is `pipeline_efficiency`. The other three are *comparative*: they
contrast already-aggregated mean values between runs and are computed at report
time, never as a single opaque quality score. Let `R` be the relevant ids, `S`
the pipeline's selected ids, and `B` the final budget.

**Pipeline efficiency** — relevant items captured per unit of budget. A
throughput view of the whole pipeline; with an item budget it lies in `[0, 1]`.

```
pipeline_efficiency = |S ∩ R| / B              (defined when B > 0)
```

For the comparative metrics, let `q_pipe` be a pipeline's mean of a quality
metric (Phase 7 uses `selection_recall`) and `q_base` the same mean for a chosen
baseline (the primitive standing in for the pipeline's final stage).

**Interaction gain** — the signed change a composition produced on a metric
relative to a baseline. Positive means the composition scored higher.

```
interaction_gain = q_pipe − q_base
```

**Degradation rate** — relative quality lost when a composition scores *below* a
baseline; `0` when it matches or beats it. Defined for higher-is-better metrics.

```
degradation_rate = max(0, q_base − q_pipe) / q_base     (defined when q_base > 0)
```

**Compensation effect** — how much a pipeline beats the best of its own
constituent primitives run alone (`q_best` = max over constituents). Positive
means one stage compensated for another's weakness.

```
compensation_effect = q_pipe − q_best          (defined with ≥ 1 constituent)
```

These contrasts depend on which primitive instance stands in for each stage, so
the report always shows the underlying means alongside the differences. They
describe specific compositions on a synthetic benchmark, not interactions in
general.

## Naturalistic metrics (Phase 8)

Phase 8 scores the same strategies on deterministic, synthetic benchmarks shaped
like realistic working information (email threads, meeting notes, support
tickets, document revisions, memory logs). It reuses the selection, retention,
and temporal metrics above and adds three contrasts that the naturalistic
scenarios make meaningful. Each operates on sets of item ids: `S` selected, `C`
current-truth, `D` superseded, `K` conflicting.

**Current-truth support** — recall over the items that carry the *current*
answer, as opposed to superseded or stale versions. Higher is better.

```
current_truth_support = |S ∩ C| / |C|          (defined when |C| > 0)
```

**Superseded-fact retention** — the fraction of superseded items (old versions a
later decision or revision replaced) that survived selection. Lower is better.

```
superseded_fact_retention = |S ∩ D| / |D|      (defined when |D| > 0)
```

**Conflict selection rate** — the fraction of the selection that contradicts the
current answer. Lower is better.

```
conflict_selection_rate = |S ∩ K| / |S|        (defined when |S| > 0)
```

Each function raises rather than returning a misleading zero when its
denominator set is empty; the Phase 8 scorer records those undefined cases as
`0.0` and notes the convention. These metrics describe specific synthetic
scenarios, not real workplace context or real-world systems.

## Robustness metrics (Phase 10)

Phase 10 introduces no new task metric; it compares an existing metric measured on
an unperturbed *baseline* run against the same metric on a *perturbed* run. All
robustness functions operate on **oriented** values where higher is better — cost
(lower-is-better) metrics are negated first, and neutral metrics are excluded — so
a drop always means "got worse". Let `b` be the oriented baseline value and `p` the
oriented perturbed value.

**Degradation** — the oriented drop. Positive means the perturbation hurt;
negative means it helped.

```
degradation = b - p
```

`degradation_under_noise` and `degradation_under_conflict` are named aliases of
`degradation`, used to attribute a drop to a distractor/noise or a
contradiction/conflict perturbation respectively.

**Robustness score** — the fraction of baseline performance retained, clamped to
`[0, 1]`; `1.0` means no degradation. When the baseline is non-positive the ratio
is undefined, so the score is `1.0` if `p ≥ b` and `0.0` otherwise.

```
robustness_score = clamp(p / b, 0, 1)            (defined when b > 0)
```

**Oracle-gap shift** — the change in a strategy's oriented distance from the oracle
ceiling on a benchmark's primary metric, baseline vs perturbed. A positive increase
means the perturbation widened the gap to the ceiling.

```
gap_increase = perturbed_gap - baseline_gap
```

These are mechanical comparisons specific to the four stress groups, perturbation
intensities, seeds, and budgets behind the artifacts — not general claims.

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
