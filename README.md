# context-engineering-lab

> Experiments in salience, compression, temporal context, attention, and their
> interactions.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy-lang.org/)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-orange)](https://docs.astral.sh/ruff/)

A research-practice repository investigating how intelligent systems decide
**what context to retain, compress, retrieve, prioritize, and forget**.

### The problem

Every system that reasons over information works inside a bounded context: a
finite window, a memory budget, an attention span. The hard part is rarely
*fetching* information — it is deciding what deserves the limited room that
remains, and what to drop. Get that decision wrong and the right answer is
crowded out by plausible noise, stale facts, or sheer volume. This is the
context-engineering problem, and it sits underneath retrieval systems, agent
memories, long-context models, and summarizers alike.

### The thesis

The decision can be studied as its own object, separately from any particular
model or product. By isolating each primitive — selection, compression, temporal
relevance, forgetting, attention allocation — on small, fully controlled
benchmarks, and by always measuring against an *oracle ceiling* and content-blind
*baselines*, we can say precisely when a strategy helps, when it does not, and how
far it sits from the best any method could do. **The experiments themselves are
the product**: each is built to answer one question and to produce a number a
careful reader can reproduce and argue with.

### Research scope

This is **not** a RAG framework, a vector database, or a production library. It
ships no external APIs, no LLM calls, and no network access; every benchmark is
generated deterministically from a seed, so results regenerate bit-for-bit. The
scope is deliberately narrow — synthetic and naturalistic-*shaped* benchmarks that
probe context decisions in isolation and in composition — and the claims stay
strictly benchmark-specific. See the [non-goals](docs/non-goals.md) for the
boundaries and [limitations](LIMITATIONS.md) for what the evidence does not show.

---

## The questions

- What information deserves to enter a limited context window?
- How much can context be compressed before task performance degrades?
- When does *forgetting* improve, rather than harm, downstream performance?
- How should the passage of time shape what gets retrieved?
- How should a fixed attention budget be allocated across competing items?
- How do these primitives interact when composed into a pipeline?
- Do these strategies remain useful when the context resembles real working information?
- Taken together across benchmarks, which strategies dominate, and where do they fail?
- How robust are these strategies when the input is adversarial?

A fuller statement of intent lives in the [repository thesis](docs/thesis.md),
the testable form in the [research questions](docs/research-questions.md), and the
boundaries in the [non-goals](docs/non-goals.md).

## Architecture and phase map

Every experiment flows through one small, synchronous harness. A `Benchmark`
generates `Case`s from a seed; a `Strategy` turns each case's candidate items into
a budgeted `Context`; the benchmark scores that context; the `ExperimentRunner`
sweeps strategies, seeds, and budgets and emits a serializable `ExperimentResult`
that the reporting layer renders to Markdown.

```
            seed
             │
             ▼
      ┌─────────────┐      candidates      ┌────────────┐      Context
      │  Benchmark  │ ───────────────────► │  Strategy  │ ──────────────┐
      │ generate()  │                      │  select()  │               │
      └─────────────┘                      └────────────┘               ▼
             ▲                                                    ┌────────────┐
             │  Case + Context                                    │  Benchmark │
             └──────────────────────────────────────────────────│ evaluate() │
                                                                  └────────────┘
                                                                         │ metrics
      ┌──────────────────┐     ExperimentResult      ┌──────────────┐    │
      │ ExperimentRunner │ ◄─────────────────────────│  aggregate   │ ◄──┘
      │ strategies×seeds │ ──────────────────────────►   per-seed   │
      │     ×budgets     │                            └──────────────┘
      └──────────────────┘
             │ JSON artifact + Markdown report
             ▼
        artifacts/
```

The work is layered in phases. Phases 2–6 build and isolate the **primitives**;
Phase 7 studies how they **interact** when composed; Phase 8 moves to
**naturalistic** scenarios; Phase 9 **synthesises** all prior results; Phase 10
**stresses** them with perturbations; Phase 11 hardens the repository for release.

```
 Phase 0–1   Research design + core harness (items, budgets, runner, registry)
     │
     ▼
 ┌──────────────────────── primitives (one benchmark family each) ───────────────────────┐
 │ Phase 2 selection   Phase 3 compression   Phase 4 temporal                              │
 │ Phase 5 retention   Phase 6 attention                                                   │
 └───────────────────────────────────────────────────────────────────────────────────────┘
     │ compose
     ▼
 Phase 7  interaction effects  (pipelines of existing primitives)
     │ apply to realistic-shaped context
     ▼
 Phase 8  naturalistic benchmarks  (email / meeting / support / revision / memory)
     │ read all result artifacts
     ▼
 Phase 9  cross-benchmark synthesis  (profiles, dominance, oracle gap, failure, stability)
     │ stress-test the benchmarks
     ▼
 Phase 10 robustness  (distractor / contradiction / stale / corruption perturbations)
     │ harden for publication
     ▼
 Phase 11 release hardening  (audit, docs, reproducibility, publication artifacts)
```

Each primitive family ships an `oracle` ceiling and content-blind baselines, so
every result is read as a gap to the best achievable and a lift over doing nothing.
See the [architecture](docs/architecture.md) and [harness](docs/harness.md) docs
for detail.

## How this repository is organized

This is a phased project. Phase 0 establishes the research design: shared
definitions, an experiment taxonomy, a benchmarking philosophy, a metrics
framework, and the engineering conventions that keep results reproducible.
Implementation phases follow the [roadmap](docs/roadmap.md).

| Document | Purpose |
| --- | --- |
| [Thesis](docs/thesis.md) | Why this lab exists and what counts as a result |
| [Research questions](docs/research-questions.md) | The testable questions the lab pursues |
| [Non-goals](docs/non-goals.md) | What this repository deliberately is not |
| [Definitions](docs/definitions.md) | Shared vocabulary used across experiments |
| [Taxonomy](docs/taxonomy.md) | The space of experiments and how they relate |
| [Benchmarks](docs/benchmarks.md) | What we measure against and why |
| [Metrics](docs/metrics.md) | How quality, cost, and robustness are quantified |
| [Architecture](docs/architecture.md) | System design and key decisions |
| [Repository layout](docs/repository-layout.md) | Where things live and why |
| [Definition of done](docs/definition-of-done.md) | The bar every experiment must clear |
| [Harness](docs/harness.md) | The core abstractions and how a run flows |
| [Phase 1 summary](docs/phase-1-summary.md) | What the Phase 1 harness adds and does not claim |
| [Selection benchmarks](docs/selection-benchmarks.md) | The Phase 2 synthetic selection benchmark and presets |
| [Phase 2 summary](docs/phase-2-summary.md) | The first selection experiments and what they do not claim |
| [Compression benchmarks](docs/compression-benchmarks.md) | The Phase 3 synthetic compression benchmark and presets |
| [Phase 3 summary](docs/phase-3-summary.md) | The first compression experiments and what they do not claim |
| [Temporal benchmarks](docs/temporal-benchmarks.md) | The Phase 4 synthetic temporal benchmark and presets |
| [Phase 4 summary](docs/phase-4-summary.md) | The first temporal experiments and what they do not claim |
| [Retention benchmarks](docs/retention-benchmarks.md) | The Phase 5 synthetic retention benchmark and presets |
| [Phase 5 summary](docs/phase-5-summary.md) | The first forgetting experiments and what they do not claim |
| [Attention benchmarks](docs/attention-benchmarks.md) | The Phase 6 synthetic attention benchmark and presets |
| [Phase 6 summary](docs/phase-6-summary.md) | The first allocation experiments and what they do not claim |
| [Interaction benchmarks](docs/interaction-benchmarks.md) | The Phase 7 synthetic interaction benchmark and presets |
| [Phase 7 summary](docs/phase-7-summary.md) | The first interaction experiments and what they do not claim |
| [Naturalistic benchmarks](docs/naturalistic-benchmarks.md) | The Phase 8 synthetic naturalistic benchmark families and presets |
| [Phase 8 summary](docs/phase-8-summary.md) | The first naturalistic experiments and what they do not claim |
| [Synthesis](docs/synthesis.md) | The Phase 9 cross-benchmark synthesis methodology |
| [Phase 9 summary](docs/phase-9-summary.md) | The cross-benchmark synthesis and what it does not claim |
| [Robustness benchmarks](docs/robustness-benchmarks.md) | The Phase 10 perturbations, robustness metrics, and limitations |
| [Phase 10 summary](docs/phase-10-summary.md) | The robustness experiments and what they do not claim |
| [Roadmap](docs/roadmap.md) | Phase plan and current status |
| [ADRs](docs/adr/) | Architecture decision records |

## Benchmark map

The catalog registers **24 research benchmark presets** across eight families
(plus a `harness-smoke` sanity check), exercised by **11 strategies**,
**6 compressors**, **6 retention policies**, **6 attention allocators**,
**8 compositions**, and **5 robustness perturbations**. Run `context-lab list`
to print every registered id.

| Family | Phase | Presets |
| --- | --- | --- |
| Selection | 2 | `easy-selection`, `position-biased-selection`, `high-distractor-selection` |
| Compression | 3 | `easy-compression`, `late-signal-compression`, `dense-distractor-compression` |
| Temporal | 4 | `recent-signal`, `old-signal`, `drift-heavy` |
| Retention | 5 | `low-noise-retention`, `stale-accumulation`, `harmful-memory` |
| Attention | 6 | `balanced-sources`, `concentrated-signal`, `noisy-dominant-source` |
| Interaction | 7 | `balanced-interaction`, `memory-pressure`, `noisy-context` |
| Naturalistic | 8 | `email-old-signal`, `email-conflict-heavy`, `meeting-action-items`, `support-stale-fix`, `revision-current-truth`, `memory-log-noisy` |

Phase 9 reads the artifacts these produce and synthesises them; Phase 10 wraps the
Phase 8 presets in perturbations (`distractor-injection`, `contradiction-injection`,
`stale-amplification`, `source-quality-corruption`, `salience-corruption`).

## Quickstart

```bash
pip install -e ".[dev]"          # install the package and dev tooling
context-lab list                 # see every registered strategy and benchmark
context-lab run-phase2 --output artifacts/phase2
cat artifacts/phase2/summary.md  # read the generated Markdown report
```

Every run is deterministic: the same command regenerates byte-identical artifacts.
See [docs/reproducibility.md](docs/reproducibility.md) for the full protocol.

## Status

**Phase 10 — Robustness and perturbation analysis.** Building on the Phase 8
benchmarks, the lab now *stress-tests* its existing strategies. A `perturbations`
package wraps a benchmark in a `PerturbedBenchmark` and rewrites the cases it
generates — injecting distractors, contradictions, or amplified stale items, or
corrupting the observable `source_quality` and `salience` signals — while leaving
ground truth and the oracle ceiling untouched. Robustness metrics (`degradation`,
`robustness_score`) compare each strategy's baseline against its perturbed run per
`(strategy, benchmark, perturbation, metric)`, and oracle-gap shifts track whether
the gap to the ceiling widens. Four stress groups (`distractor-stress`,
`contradiction-stress`, `stale-amplification`, `corruption-stress`) over the
Phase 8 presets, a deterministic Markdown report, and a `context-lab run-phase10`
command tie it together. Phase 10 **adds no new primitive, strategy, or benchmark
family** and touches no network or LLM. Conclusions are **specific to these
synthetic stressors** — not claims about real-world systems; `oracle` strategies
are ceilings, not deployable. See the
[Phase 10 summary](docs/phase-10-summary.md) and
[robustness benchmarks](docs/robustness-benchmarks.md).

Earlier phases (selection, compression, temporal, retention, attention,
interaction effects, naturalistic benchmarks, cross-benchmark synthesis) remain
available; see the [roadmap](docs/roadmap.md).

## Running the harness

```bash
context-lab list                                   # registered strategies/benchmarks
context-lab run-smoke --output artifacts/smoke-result.json
context-lab run-phase2 --output artifacts/phase2   # Phase 2 selection suite + report
context-lab run-phase3 --output artifacts/phase3   # Phase 3 compression suite + report
context-lab run-phase4 --output artifacts/phase4   # Phase 4 temporal suite + report
context-lab run-phase5 --output artifacts/phase5   # Phase 5 retention suite + report
context-lab run-phase6 --output artifacts/phase6   # Phase 6 attention suite + report
context-lab run-phase7 --output artifacts/phase7   # Phase 7 interaction suite + report
context-lab run-phase8 --output artifacts/phase8   # Phase 8 naturalistic suite + report
context-lab run-phase9 --output artifacts/phase9   # Phase 9 synthesis of all suites
context-lab run-phase10 --output artifacts/phase10 # Phase 10 robustness experiments + report
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

ruff check .       # lint
mypy               # strict type check
pytest             # tests
python -m build    # build sdist + wheel
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). New experiments should follow the
[definition of done](docs/definition-of-done.md).

## License

Released under the [MIT License](LICENSE).
