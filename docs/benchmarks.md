# Benchmark philosophy

A benchmark is a task, a dataset, and an evaluation procedure used to score
strategies. Benchmarks are where good intentions meet reality, so we are
deliberate about how we build and use them.

## Principles

**1. The benchmark serves the question, not the other way around.**
We choose or build a benchmark *after* stating a question, and we choose it
because it can discriminate between strategies for that question. A benchmark
that every strategy passes or fails equally tells us nothing.

**2. Prefer controllable synthetic tasks first.**
Synthetic tasks let us vary one factor at a time: number of distractors, signal
position, redundancy, drift rate. This control is what turns an anecdote into a
finding. We graduate to realistic datasets once a mechanism is understood, to
check that it survives messiness.

**3. Always include a baseline and a ceiling.**
Every benchmark reports at least one trivial baseline (e.g. "most recent N") and,
where possible, an oracle or upper bound (e.g. perfect selection). A strategy's
score is meaningful only relative to these anchors.

**4. Measure across the budget, not at one point.**
A single-budget number hides the interesting behavior. Benchmarks sweep the
budget and report budget-performance curves, because the *shape* (cliffs,
plateaus, diminishing returns) is usually the real result.

**5. Separate quality, cost, and robustness.**
A strategy that is slightly better but far more expensive is not strictly better.
Benchmarks report cost (tokens, latency, memory) alongside quality so trade-offs
are visible. See [metrics.md](metrics.md).

**6. Adversarial conditions are part of the benchmark, not an afterthought.**
For any strategy intended for real use, we report performance under distractors
and, where relevant, poisoning. A strategy that only works on clean data is
documented as such.

## Anatomy of a benchmark

Each benchmark in the lab declares:

- **Task** — what the consumer must do and how success is scored.
- **Generator or dataset** — how instances are produced, with all knobs exposed.
- **Budget range** — the budgets swept during evaluation.
- **Baselines** — the reference strategies it always includes.
- **Metrics** — the quality, cost, and robustness measures it reports.
- **Seeds** — the seeds used, so runs are reproducible.

## Construct validity

The central risk of any benchmark is measuring the wrong thing. We mitigate this
explicitly:

- **State the construct.** What real capability is this task a proxy for?
- **Probe for shortcuts.** Can a degenerate strategy score well without the
  capability (e.g. by exploiting position or length)? If so, the benchmark is
  patched or discarded.
- **Report the gap.** Where a synthetic task diverges from real conditions, that
  divergence is documented as a threat to validity, not hidden.

## Reuse and versioning

Benchmarks are shared infrastructure. When a benchmark changes in a way that
affects scores, it is versioned, and results record which version produced them.
A result without a benchmark version is not reproducible and does not count.

## What we explicitly avoid

- **Leaderboard chasing.** We do not optimize a strategy against a single number
  until it overfits the benchmark.
- **Cherry-picked budgets.** Reporting only the budget where a strategy looks
  best is a validity failure.
- **Hidden data leakage.** Generators and splits are designed so that test
  instances cannot be trivially memorized from training or tuning.
