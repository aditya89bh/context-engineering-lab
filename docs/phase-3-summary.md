# Phase 3 summary

Phase 3 runs the first controlled experiments on **compression under budget
pressure**: how much a document can be shortened before task-relevant facts are
lost. It studies *deterministic* compression only — no LLM summarization, no
abstractive generation, no external calls. For the benchmark design see
[compression-benchmarks.md](compression-benchmarks.md).

## What Phase 3 added

- A compression interface (`core.compression`): the `Compressor` protocol,
  `CompressionStats`/`CompressionResult`, and a `CompressorStrategy` adapter so
  compressors run through the existing Phase 1 experiment runner unchanged.
- Six compressors: `no-compression`, `head-truncation`, `tail-truncation`,
  `keyword-preserving`, `sentence-boundary`, and an `oracle-compression` ceiling.
- Fact-token markers (`benchmarks.facts`) and the `compression-fact-preservation`
  benchmark generator with three presets: `easy-compression`,
  `late-signal-compression`, `dense-distractor-compression`.
- Compression metrics (`core.compression_metrics`): `compression_ratio`,
  `information_retention`, `answer_support_after_compression`,
  `distractor_retention`, and `budget_utilization`.
- Four reproducible experiments and a Markdown report, driven by
  `context-lab run-phase3`.

## Compressors as bounds

The line-up is structured as bounds, not as a leaderboard of deployable systems:

- **Reference:** `no-compression` keeps everything but ignores the budget; its
  `budget_utilization` exceeds 1 whenever compression was needed.
- **Lower bounds:** `head-truncation` and `tail-truncation` read only position.
- **Deployable middle:** `keyword-preserving` (reads the query) and
  `sentence-boundary` (keeps whole leading sentences).
- **Upper bound:** `oracle-compression` reads the ground-truth fact markers and
  keeps only target facts. It is **not deployable**; it measures headroom.

### Note on budget allocation across items

Phase 3 compressors split a token budget *evenly* across the input items (any
remainder goes to the earliest items; see `compression/_common.py`). This is
acceptable for the current `compression-fact-preservation` benchmark because each
case contains a single document, so the whole budget applies to it and the split
is a no-op. It is, however, a simplification: future *multi-item* compression
benchmarks would likely need smarter allocation — salience-aware (spend more on
items that carry the facts) or item-length-aware (proportional to each item's
size) — rather than an even split. That allocator is intentionally deferred; see
the `CompressionBudgetAllocator` note in [architecture.md](architecture.md).

## Observations (these benchmarks only)

Run `context-lab run-phase3` to regenerate the tables. The headline patterns,
specific to these synthetic benchmarks, seeds, and budgets:

- **Truncation is position-bound.** On `easy-compression` (facts early) head
  truncation keeps every required fact at all budgets while tail truncation fails
  until the budget covers the whole document; on `late-signal-compression` (facts
  late) the two swap. Position-blind compression can be right for the wrong
  reason. (RQ4, RQ13)
- **A query-aware extractor preserves required facts well.** `keyword-preserving`
  keeps the required facts (the query names them) across budgets, but misses
  optional facts the query omits, so its information retention sits below the
  oracle. Extractive selection beats naive truncation when content position is
  adversarial. (RQ14)
- **Compression can launder distractors.** On `dense-distractor-compression`,
  truncation and keyword preservation retain a sizeable fraction of distractors,
  while `oracle-compression` drops them entirely — full retention at a low
  compression ratio. (RQ11)
- **The frontier is visible.** `compression-budget-sweep` traces information
  retention against the token budget; the oracle holds full retention at a small
  ratio while the deployable compressors climb with the budget.

These begin to address [research questions](research-questions.md) RQ4, RQ11, and
the newly added RQ14, and connect to the Phase 2 position-bias question RQ13. They
do not close any of them.

## What Phase 3 does not claim

- **No general conclusions.** Every observation is specific to synthetic
  benchmarks, a handful of seeds, and token budgets. None generalizes to real
  documents or to summarization at large.
- **No summarization.** All compressors are deterministic and extractive. Nothing
  here speaks to abstractive or LLM-based compression.
- **The oracle is not achievable.** It reads ground-truth facts; it is a
  measurement ceiling, not a target.
- **No tuning, no significance testing.** Results are aggregated means over a few
  seeds, reported as-is.

Later phases (temporal decay, forgetting, attention allocation) are out of scope
here; see the [roadmap](roadmap.md).

## Running validation

```bash
pip install -e ".[dev]"
ruff check .       # lint
mypy               # strict type check
pytest             # tests
python -m build    # build sdist + wheel
```
