# Naturalistic benchmarks

Phase 8 introduces five controlled benchmark families that look like realistic
context sources while remaining fully synthetic and deterministic:

- `email-thread-context`
- `meeting-notes-context`
- `support-ticket-context`
- `document-revision-context`
- `memory-log-context`

Everything is generated and scored deterministically from a seed. There is no
external API, no LLM, no real or private data, and no dashboard, agent, or
planner. **Naturalistic means realistic-*shaped*, not real.**

The single question these probe is the Phase 8 question:

> Do context-engineering strategies remain useful when the context resembles real
> working information?

## Reuse, not reinvention

Phase 8 adds **no new strategy**. It reuses the Phase 2-7 selectors, retention
policies, attention allocators, and compositions unchanged, and runs them through
the existing experiment runner. The only genuinely new code is benchmark
generation, three scenario-specific metrics, and reporting.

## Records that become items

Each family is described with a lightweight record helper that converts cleanly
into a core `Item`:

| record | family | shape |
| --- | --- | --- |
| `MessageLikeRecord` | email | sender, subject, body |
| `MeetingNoteRecord` | meeting | label (decision/action/update/note), body |
| `TicketRecord` | support | incident, field (symptom/resolution), body |
| `RevisionRecord` | revision | revision number, body |
| `MemoryRecord` | memory log | body |

Records carry the same ground-truth flags and observable signals, so a single
shared engine (`NaturalisticBenchmark`) handles generation and scoring; a family
only describes how to build its cases.

## Ground truth vs observable signals

Every record sets ground-truth flags — relevant, current, superseded,
conflicting, harmful, stale, required — and two **observable** proxies a
deployable strategy may read:

- **salience** — an importance proxy (e.g. a pinned or flagged item);
- **frequency** — how often the item recurs or is referenced;

plus, for the source-based support family, an observable **source quality**
score. Query terms are embedded at three overlap levels (full / partial / none),
so a keyword selector ranks full-overlap items above partial ones.

The signals are deliberately *misaligned* with the truth so that no single
content-only strategy suffices. The recurring pattern is that the relevant or
current record reads as important (high salience, often referenced) while the
conflicting, superseded, or stale record is just as on-topic textually but reads
as unimportant and old. So keyword overlap is lured by the outdated record, while
an importance-aware policy recovers the answer.

## The five families

### `email-thread-context`

The answer is an *older* relevant message buried in a noisy thread. Cases mix the
relevant message, recent distractor chatter, older stale-conflicting messages,
and an optional harmful misleading message. Recency and recent windows chase the
chatter; keyword overlap is lured by the conflicting messages; salience-aware
retention recovers the older answer.

### `meeting-notes-context`

The answer is a current decision (and its action item) among notes that also
contain an earlier, now-*superseded* decision plus status updates and asides.
Keyword overlap drags in the superseded decision; an importance-aware policy keeps
the current one.

### `support-ticket-context`

A current ticket resembles several past incidents. One incident holds the working
fix, another a *stale* fix, another a *harmful* fix, and every incident repeats
the same noisy symptom lines. Past incidents are **sources** with an observable
quality score, so this family also exercises source-based allocation
(`attention->selection`).

### `document-revision-context`

The answer depends on the *current* revision of a document, not on older ones.
Cases mix current facts with an older revision, deprecated facts, and old facts
that directly conflict with the current answer. Here recency is the *right* signal
(current = newest), which the family makes visible.

### `memory-log-context`

An agent memory log accumulates useful, stale, harmful, and neutral entries over
time — the naturalistic skin over the Phase 5 forgetting question.

## Presets

Six presets, each declaring an id, version, construct, parameters, a budget
sweep, and expected failure modes:

| preset | family | construct |
| --- | --- | --- |
| `email-old-signal` | email | recover an old relevant email under recent distractors |
| `email-conflict-heavy` | email | separate the answer from many on-topic conflicting messages |
| `meeting-action-items` | meeting | find the current decision/action among superseded notes |
| `support-stale-fix` | support | pick the working fix over stale, harmful, noisy incidents |
| `revision-current-truth` | revision | track current document facts, not superseded revisions |
| `memory-log-noisy` | memory log | keep useful memories while dropping stale and harmful ones |

## Metrics

The families reuse the existing selection, retention, and temporal metrics
(`answer_support`, `selection_recall`, `selection_precision`,
`harmful_retention_rate`, `stale_selection_rate`, `signal_capture_rate`,
`budget_utilization`) and add three naturalistic contrasts —
`current_truth_support`, `superseded_fact_retention`, and
`conflict_selection_rate`. Formulas are in [metrics.md](metrics.md). Each family
declares only the metrics that make sense for its scenario.

## Strategy lineup

A small, curated lineup of existing components — not the whole catalog:

- `recency` and `keyword-overlap` (content-blind and content-only baselines);
- `salience-retention` (an importance-aware policy);
- `temporal->selection` and `retention->selection` (Phase 7 compositions);
- `attention->selection` (added only for the source-based support family);
- `oracle` (a ceiling that reads ground-truth relevance, not deployable).

## Running

```
context-lab run-phase8 --output artifacts/phase8
```

writes one JSON artifact per experiment plus a deterministic `summary.md`. Every
result records the benchmark id and version, seeds, strategy ids, budgets, and
metric definitions.

## What these do not show

The benchmarks are synthetic and deterministic. Observable signals are stylised
proxies, not measurements from a real system. The lineup is curated and small,
and metrics are aggregated over a few seeds. Observations describe these
scenarios only; they are **not** claims about all workplace context or all
real-world systems, and `oracle` is an upper bound, not an achievable target.
