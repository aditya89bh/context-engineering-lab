# Compression benchmarks

Phase 3 introduces one controlled, synthetic benchmark family —
`compression-fact-preservation` — and three presets built from it. These study
**deterministic** compression: shortening content to fit a budget while keeping
task-relevant facts. There is **no LLM summarization**, no abstractive
generation, and no external API of any kind. Everything is generated and scored
deterministically from a seed.

The single question they probe is the Phase 3 question:

> How much context can be compressed before task-relevant information is lost?

## Facts as ground truth

Each case is a single document whose content embeds *facts* as recognizable
tokens (see `benchmarks/facts.py`):

- `RF<n>` — required target facts (must survive to answer the task),
- `TF<n>` — optional target facts (relevant, not strictly required),
- `DF<n>` — distractor facts (irrelevant; a good compressor discards them).

The rest of the content is filler. Because facts are tokens, scoring is
stateless: it scans the compressed text and checks which fact tokens remain.
These markers are ground truth — only `oracle-compression` is permitted to read
them; deployable strategies rely on position or the task query instead.

## The generator: `compression-fact-preservation`

The generator (`benchmarks/compression.py`) exposes the knobs that matter for
compression under pressure:

| Knob | Values | What it probes |
| --- | --- | --- |
| `content_length` | `>= facts` | Document size to compress |
| `target_position` | `early`, `middle`, `late`, `distributed` | Position bias |
| `num_required_facts` / `num_optional_facts` | `>= 1` / `>= 0` | Required vs. graded retention |
| `num_distractor_facts` | `>= 0` | Distractor density |
| `sentence_length` | `>= 1` | Sentence structure for boundary extraction |
| `budget_sweep` | tuple of token budgets | Where reduction breaks the task |

Construction details:

- Content is laid out as sentences delimited by a `.` token, so the
  sentence-boundary compressor has real boundaries to respect.
- The task query lists the required facts (`RF<n>`), so a query-aware compressor
  can preserve them without seeing the ground-truth markers.
- Budgets are measured in **tokens**. The single document receives the whole
  budget for each case.

### Metrics

The benchmark reports five metrics per case (formulas in
[metrics.md](metrics.md)):

- `compression_ratio` — compressed length over original length (lower = more).
- `information_retention` — fraction of target facts retained.
- `answer_support_after_compression` — whether all required facts survived.
- `distractor_retention` — fraction of distractor facts retained (lower better).
- `budget_utilization` — fraction of the budget consumed (may exceed 1 for the
  no-compression baseline).

`distractor_retention` is reported as `0.0` when a case has no distractors.

## Presets

Three presets, each isolating one construct.

### `easy-compression`

- **Construct:** fact preservation with low interference, target facts early.
- **Parameters:** length 20, 2 required + 2 optional facts, 2 distractors, early.
- **Expected failure modes:** tail truncation drops early facts at small budgets;
  keyword preservation should track the oracle on required facts.

### `late-signal-compression`

- **Construct:** position bias of truncation, target facts placed late.
- **Parameters:** length 30, 2 required + 2 optional facts, 4 distractors, late.
- **Expected failure modes:** head truncation and sentence-boundary extraction
  miss late facts; tail truncation succeeds by position, not by relevance.

### `dense-distractor-compression`

- **Construct:** distractor discarding under heavy distractor density.
- **Parameters:** length 40, 2 required + 2 optional facts, 20 distractors,
  distributed.
- **Expected failure modes:** truncation and keyword preservation retain many
  distractors; only the oracle drops them reliably.

## Compressors under test

| Compressor | Reads | Role |
| --- | --- | --- |
| `no-compression` | nothing | Reference; keeps all content, **ignores the budget** |
| `head-truncation` | position | Lower bound; keeps the prefix |
| `tail-truncation` | position | Lower bound; keeps the suffix |
| `keyword-preserving` | the query | Deployable extractive baseline |
| `sentence-boundary` | structure | Extractive; keeps whole leading sentences |
| `oracle-compression` | fact markers | **Ceiling only — not deployable** |

`no-compression` is the one strategy in the lab that does not honor the budget:
it returns an over-budget context so its `budget_utilization` exceeds 1 whenever
compression was actually needed. That is the point — it shows what perfect
retention costs.

`oracle-compression` reads the ground-truth fact markers and keeps only the
target facts, discarding distractors and filler. No real compressor knows the
facts in advance, so it is an upper bound for comparison, never a strategy to
ship.

## Reproducing

```bash
context-lab run-phase3 --output artifacts/phase3
```

This runs all four Phase 3 experiments, writes one JSON artifact per experiment,
and a `summary.md` report. Output is deterministic across repeated runs.

Every result carries its seed, token budget, benchmark id and version, strategy
id, and the metric definitions above — the minimum needed to reproduce and
interpret it.
