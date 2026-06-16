# Phase 1 summary

Phase 1 turned the Phase 0 research design into typed, testable infrastructure:
the experimental harness the later labs build on. This document summarizes what
was added and, just as importantly, what it does not claim. For a structural map
see [harness.md](harness.md).

## What Phase 1 added

- Typed core primitives and identifiers.
- The strategy and benchmark interfaces.
- A synchronous experiment runner with deterministic metadata.
- Result models with JSON serialization and on-disk persistence.
- A registry and a built-in catalog.
- One trivial baseline (recency selection) and one harness smoke benchmark.
- A `context-lab` command-line interface.

## Core abstractions

| Concept | Type | Role |
| --- | --- | --- |
| Item | `core.item.Item` | Content, length, optional timestamp, JSON-safe metadata |
| Budget | `core.budget.Budget` / `BudgetUnit` | A positive limit in items, tokens, or characters |
| Context | `core.context.Context` | Budget-bounded items; rejects silent overflow |
| Task | `core.task.Task` | What the consumer must do |
| Strategy | `core.strategy.Strategy` | `select(candidates, task, budget) -> Context` |
| Benchmark / Case | `core.benchmark` | A task + generator + scorer / one scored instance |
| Experiment | `core.experiment.Experiment` | Benchmark, strategies, seeds, budgets |
| Runner | `core.runner.ExperimentRunner` | Executes an experiment, aggregates metrics |
| Results | `core.results` | `MetricValue`, `StrategyRunResult`, `ExperimentResult` |
| Metadata | `core.metadata.RunMetadata` | Deterministic provenance and content-addressed `RunId` |
| Registry | `core.registry.Registry` | Looks up strategies and benchmarks by id |

Items, budgets, contexts, tasks, and identifiers are immutable (frozen) and
validate their invariants on construction: non-negative item length, strictly
positive budget limit, non-empty identifiers, and contexts that refuse to exceed
their budget unless `allow_overflow` is set explicitly.

Item metadata accepts JSON-safe scalar values — `str | int | float | bool |
None` — not just strings, so experiments can attach typed annotations that
serialize without a custom encoder.

## Runner behavior

For each strategy, seed, and budget, the runner:

1. asks the benchmark to `generate(seed)` cases;
2. runs the strategy's `select(...)` for each case;
3. scores the resulting context with the benchmark's `evaluate(...)`;
4. **validates** that the metric names returned by `evaluate` exactly match the
   benchmark's `declared_metrics` — a missing or extra metric raises a
   `ValueError` naming the benchmark id, the case id, and the missing/extra
   names;
5. aggregates per-case scores into `MetricValue`s (mean and population standard
   deviation) grouped by strategy.

The run records deterministic `RunMetadata`, including a `RunId` derived from the
experiment configuration (not wall-clock time), so identical configurations
produce identical ids and reruns are detectable.

## The smoke benchmark

`harness-smoke` is a tiny needle-in-a-haystack task: each case has one target
item among several distractors, and the task is to retrieve the target. It
reports `answer_support`, `selection_recall`, and `selection_precision`, swept
over item budgets of 1, 2, and 4. It exists ONLY to validate the harness end to
end and is not a research instrument.

### Empty-selection precision convention

The formal `core.metrics.selection_precision` treats an empty selection as
*undefined* and raises. For harness convenience, the smoke benchmark records
precision as `0.0` when nothing is selected, so a degenerate tiny-budget run
never crashes. This is a reporting convenience, not a claim about precision at
zero selection.

## CLI commands

```bash
context-lab list                                   # registered strategies/benchmarks
context-lab run-smoke --output artifacts/smoke-result.json
context-lab run-smoke --seeds 1 2 3 --output artifacts/smoke.json
```

`run-smoke` runs the recency baseline on the smoke benchmark and writes a JSON
artifact. Artifacts under `artifacts/` are git-ignored.

## What Phase 1 does not claim

- **No research findings.** The baseline and smoke benchmark exist to exercise
  the plumbing. Their numbers carry no conclusions.
- **No strategy comparison.** Recency selection is a reference point, not a
  recommendation.
- **No real benchmark.** `harness-smoke` is a synthetic sanity check, not a
  measure of any real capability.

Real strategies, benchmarks, and conclusions arrive in later phases per the
[roadmap](roadmap.md).

## Running validation

```bash
pip install -e ".[dev]"
ruff check .       # lint
mypy               # strict type check
pytest             # tests
python -m build    # build sdist + wheel
```

## Result JSON shape

A run produces an `ExperimentResult` serialized as JSON. Abridged to two of the
metric entries:

```json
{
  "metadata": {
    "benchmark_id": "harness-smoke",
    "benchmark_version": "1.0",
    "budgets": [[1, "items"], [2, "items"], [4, "items"]],
    "code_version": "0.0.0",
    "experiment_id": "harness-smoke",
    "platform": "Darwin 25.5.0",
    "python_version": "3.14.5",
    "run_id": "cfe60d3811fa53f8bcc84a13b0c46ef5",
    "seeds": [1],
    "strategy_ids": ["recency"]
  },
  "results": [
    {
      "strategy_id": "recency",
      "metrics": [
        {
          "name": "answer_support",
          "value": 0.25,
          "seed": 1,
          "budget_limit": 1,
          "budget_unit": "items",
          "sample_size": 8,
          "stddev": 0.4330127018922193
        },
        {
          "name": "selection_recall",
          "value": 0.25,
          "seed": 1,
          "budget_limit": 1,
          "budget_unit": "items",
          "sample_size": 8,
          "stddev": 0.4330127018922193
        }
      ]
    }
  ]
}
```

The `value` and `stddev` numbers above come from the smoke benchmark and are
illustrative only.
