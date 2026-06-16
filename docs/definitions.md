# Definitions

A shared vocabulary keeps experiments comparable. These terms are used
precisely throughout the repository; where a word has a loose colloquial meaning,
the definition here takes precedence.

## Core objects

**Item.** The atomic unit of information that may or may not be placed in
context. An item could be a document chunk, a past observation, a tool result, a
memory entry, or a fact. Every item carries content and metadata (e.g.
timestamp, source, length).

**Context.** The bounded set of items made available to a consumer (a model, a
policy, a reasoning process) at decision time. Context is always subject to a
budget.

**Budget.** The hard constraint on context. Usually expressed in tokens, but may
be a count of items, bytes, or a latency ceiling. A strategy that ignores the
budget is not a context strategy.

**Consumer.** The downstream process that uses the context to perform a task. The
consumer defines what "good" context means, because it defines the task.

**Task.** A well-defined objective the consumer must achieve, with a measurable
notion of success (e.g. answer correctly, retrieve the relevant fact, complete
the plan).

## Operations on context

**Salience.** The estimated value of an item to the current task. Salience is a
score, not a binary; selection turns scores into membership under a budget.

**Selection.** Choosing which items enter context given their salience and the
budget. Selection is the central act this lab studies.

**Compression.** Reducing the size of an item or a set of items while preserving
task-relevant information. Includes summarization, abstraction, deduplication,
and quantization of information.

**Retrieval.** Producing a candidate set of items from a larger store in response
to a query or state. Retrieval narrows the field that selection then prunes.

**Prioritization.** Ordering items by salience so that, under a budget, the most
valuable survive. Distinct from selection only in that it produces a ranking
rather than a set.

**Forgetting.** Deliberately removing items from a store or from eligibility for
future context. Forgetting is an *active* policy, not the absence of one.

**Eviction.** The mechanism by which forgetting is enacted under a budget (e.g.
least-recently-used, lowest-salience-first, time-decayed).

## Temporal concepts

**Recency.** How recently an item was created or last accessed. A common but
imperfect proxy for salience.

**Temporal decay.** A function that reduces an item's salience as time passes,
modeling the assumption that older information is less likely to be relevant.

**Staleness.** The degree to which an item's content no longer reflects the
current state of the world. Distinct from age: an old fact can be fresh, a recent
observation can be stale.

## Evaluation concepts

**Strategy.** A concrete, named policy for one or more of the operations above
(e.g. a salience scorer, a compressor, an eviction rule). Strategies are the
units we compare.

**Baseline.** A deliberately simple strategy used as a reference point (e.g.
"keep the most recent N items"). A new strategy earns its keep only by beating
relevant baselines.

**Benchmark.** A task plus a dataset plus an evaluation procedure, used to score
strategies. See [benchmarks.md](benchmarks.md).

**Metric.** A quantitative measure of an outcome, spanning quality, cost, and
robustness. See [metrics.md](metrics.md).

**Budget-performance curve.** Performance measured across a range of budgets,
rather than at a single budget. The shape of this curve is often the real result.

## Adversarial concepts

**Distractor.** An item that is plausible but irrelevant or misleading, included
to test whether a strategy can avoid being captured by surface similarity.

**Poisoning.** The deliberate insertion of harmful items into a store to degrade
downstream performance, used to probe robustness.

**Robustness.** The degree to which a strategy maintains performance under
distribution shift, distractors, or poisoning.
