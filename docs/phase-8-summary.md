# Phase 8 summary

Phase 8 runs the first **naturalistic** experiments: it asks whether the
strategies built in Phases 2-7 still behave sensibly when the context *looks* like
real working information — email threads, meeting notes, support tickets, document
revisions, and memory logs. Every benchmark is deterministic and fully synthetic;
**naturalistic means realistic-*shaped*, not real.** For the benchmark design see
[naturalistic-benchmarks.md](naturalistic-benchmarks.md).

## What Phase 8 added

- Lightweight record helpers (`benchmarks.naturalistic.records`):
  `MessageLikeRecord`, `MeetingNoteRecord`, `TicketRecord`, `RevisionRecord`, and
  `MemoryRecord`, each converting cleanly into a core `Item`, plus a shared
  `NaturalisticBenchmark` engine that handles generation and a single scoring
  routine.
- Five deterministic benchmark families — `email-thread-context`,
  `meeting-notes-context`, `support-ticket-context`, `document-revision-context`,
  and `memory-log-context`.
- Six presets: `email-old-signal`, `email-conflict-heavy`, `meeting-action-items`,
  `support-stale-fix`, `revision-current-truth`, and `memory-log-noisy`, each
  declaring an id, version, construct, parameters, budget sweep, and expected
  failure modes.
- Three naturalistic metrics (`core.naturalistic_metrics`):
  `current_truth_support`, `superseded_fact_retention`, and
  `conflict_selection_rate`, layered on the reused selection/retention/temporal
  metrics.
- Five reproducible experiments and a Markdown report, driven by
  `context-lab run-phase8`.

## Reuse, not reinvention

Phase 8 introduces **no new strategy**. The curated lineup is entirely existing
components: `recency`, `keyword-overlap`, an importance-aware `salience-retention`
policy, the Phase 7 `temporal->selection` and `retention->selection` compositions,
`attention->selection` for the source-based support family, and an `oracle`
ceiling. The only new code is benchmark generation, the three metrics, and
reporting.

## Strategies as a comparison

The lineup is structured so each deployable strategy can be read against a
content-only keyword baseline and an oracle ceiling, not as a leaderboard of
products:

- **Content-blind / content-only baselines:** `recency` and `keyword-overlap`.
- **Importance-aware policy:** `salience-retention`.
- **Compositions:** `temporal->selection`, `retention->selection`, and (support
  only) `attention->selection`.
- **Upper bound:** `oracle` reads ground-truth relevance and is **not deployable**;
  it measures headroom.

## Observations (these scenarios only)

Run `context-lab run-phase8` to regenerate the tables. The headline patterns,
specific to these synthetic scenarios, seeds, and budgets:

- **Importance beats keyword matching when the noise is on-topic.** On the email,
  meeting, and revision families the conflicting/superseded records carry the query
  terms, so `keyword-overlap` keeps them; `salience-retention` recovers the answer
  while cutting `conflict_selection_rate` and `superseded_fact_retention`. (RQ19)
- **A forgetting stage removes harmful fixes a selector keeps.** On the support and
  memory-log families, `salience-retention` and `attention->selection` cut
  `harmful_retention_rate` relative to `keyword-overlap`, which keeps the
  on-topic harmful record. (RQ19)
- **The right temporal signal is family-dependent.** A recency window is correct on
  `document-revision-context` (the current truth *is* the newest revision) but
  discards the old relevant message on `email-thread-context` — the same primitive
  helps on one scenario and hurts on another. (RQ19)
- **No deployable strategy reaches the oracle on every metric.** The oracle is the
  answer-support ceiling; deployable strategies trade answer support against
  conflict, superseded, and harmful selection differently by scenario.

These begin to address [research questions](research-questions.md) RQ19. They do
not close it, and they say nothing about the robustness questions (RQ9 onward),
which remain future work.

## What Phase 8 does not claim

- **No real-world validity.** Every observation is specific to synthetic
  scenarios, a handful of seeds, and item budgets; nothing here is a claim about
  all workplace context or all real-world systems.
- **No real data, no LLM.** Cases are generated locally from a seed. No real or
  private data is ingested and no LLM generates any benchmark content.
- **Naturalistic ≠ real.** The scenarios are realistic-*shaped*; observable signals
  (salience, frequency, source quality) are stylised proxies, not measurements.
- **No new primitives.** The lineup reuses existing strategies and compositions.
- **The oracle is not achievable.** It reads ground-truth relevance; it is a
  measurement ceiling, not a target.
- **No tuning, no significance testing.** Results are aggregated means over a few
  seeds, reported as-is.

## Running validation

```bash
pip install -e ".[dev]"
ruff check .       # lint
mypy               # strict type check
pytest             # tests
python -m build    # build sdist + wheel
```
