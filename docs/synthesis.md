# Cross-benchmark synthesis (Phase 9)

Phase 9 does not run a new experiment. It reads the result artifacts produced by
the Phase 2-8 suites and synthesises them into a single, mechanical picture:
which strategies dominate where, how far each sits below its oracle, where each
fails, and how stable the rankings are. It adds **no new strategy, benchmark,
metric, or algorithm**, and it touches no network, LLM, dashboard, or notebook.

Everything below is computed from the aggregated numbers. The conclusions are
specific to the synthetic benchmarks, seeds, and budgets behind the artifacts and
are **not** claims about real-world systems. `oracle` strategies are ceilings,
not deployable approaches.

## Pipeline

1. **Load** (`synthesis.loading`) — read each artifact with explicit schema
   validation; a missing file, malformed JSON, or invalid structure raises a
   single `ArtifactError`.
2. **Collect** (`synthesis.collection`) — recursively discover artifacts in a
   directory in sorted order and group them by benchmark or strategy.
3. **Aggregate** (`synthesis.aggregation`) — collapse the per-seed metric values
   into one cell per `(benchmark, strategy, metric, budget)`, recording the mean
   and the across-seed standard deviation. Each metric is tagged with an
   *orientation* (higher-is-better, lower-is-better, or neutral); neutral metrics
   such as budget utilisation are excluded from ranking.
4. **Analyse** — profiles, dominance, oracle gap, failure, and stability.
5. **Report** (`reporting.phase9_report`) — render a deterministic Markdown
   document; `context-lab run-phase9` re-runs the suites and writes it.

## Primary metric and orientation

Benchmarks declare different metrics, so synthesis picks one **primary quality
metric** per benchmark from a fixed priority order (e.g. `answer_support`, then
`answer_support_after_compression`, …, falling back to `signal_capture_rate` for
the attention family). The primary metric is always higher-is-better, which makes
cross-benchmark numbers comparable in direction (though not in absolute scale).

For dominance and oracle gaps, cost metrics (lower-is-better) are *oriented* by
negation so that "higher is better" holds uniformly.

## Analyses

- **Strategy profiles** (`synthesis.profiles`) — per strategy: the benchmarks it
  ran on, mean primary score, strongest and weakest benchmarks, best and worst
  budgets, and the mean **oracle distance** (primary-metric gap to each
  benchmark's oracle).
- **Dominance** (`synthesis.dominance`) — compare every pair of strategies on the
  `(benchmark, metric, budget)` cells they *share*, counting wins, losses, and
  ties; report each strategy's totals and the **non-dominated frontier** (Pareto
  over shared cells). Strategies evaluated on disjoint benchmarks share no cells
  and are all non-dominated.
- **Oracle gap** (`synthesis.oracle_gap`) — per-cell gaps from each strategy to
  the best oracle, plus per-strategy summaries including an oracle-normalized
  score (`strategy / oracle` on the primary metric; 1.0 matches the oracle).
- **Failure analysis** (`synthesis.failure`) — three mechanical flags:
  `BUDGET_FAILURE` (primary collapses at the tightest budget), `BENCHMARK_FAILURE`
  (wide oracle gap on a benchmark), and `METRIC_DEGRADATION` (a quality metric
  gets worse as the budget grows). Oracles are never flagged.
- **Stability** (`synthesis.stability`) — seed variance (across-seed spread),
  budget sensitivity (primary range across budgets), and ranking volatility (how
  much the strategy ordering reshuffles between adjacent budgets, a normalized
  Kendall-tau distance).

## Reproducibility

```bash
context-lab run-phase9 --output artifacts/phase9
```

re-runs every Phase 2-8 experiment, writes each result as
`artifacts/phase9/<phase>-<name>.json`, and writes the synthesis report to
`artifacts/phase9/synthesis.md`. Output is deterministic: run ids derive from the
configuration, seeds are fixed, and tables are sorted, so reruns diff cleanly.

## Limitations

- Synthesis only reflects the benchmarks, strategies, seeds, and budgets present
  in the artifacts; gaps in coverage are gaps in the conclusions.
- Primary metrics differ by benchmark, so cross-benchmark numbers mix metrics;
  comparisons are strongest *within* a benchmark.
- Budgets are compared by numeric limit even though units differ (items vs
  tokens) between benchmarks.
- Dominance is restricted to shared cells; it never compares strategies that ran
  on disjoint benchmarks.
- `oracle` strategies are upper bounds, not deployable approaches; a negative
  oracle distance only means a budget-ignoring reference (e.g. `retain-all`)
  trivially exceeded a budgeted oracle on one metric.
- Failure flags are threshold checks, not root-cause explanations.
