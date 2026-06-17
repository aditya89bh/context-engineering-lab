# context-engineering-lab

> Experiments in salience, compression, temporal context, attention, and their
> interactions.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy-lang.org/)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-orange)](https://docs.astral.sh/ruff/)

A research-practice repository investigating how intelligent systems decide
**what context to retain, compress, retrieve, prioritize, and forget**.

This is not another RAG implementation. The experiments themselves are the
product. Each one is built to answer a specific question and to produce a
result a careful reader can reproduce and argue with.

---

## The questions

- What information deserves to enter a limited context window?
- How much can context be compressed before task performance degrades?
- When does *forgetting* improve, rather than harm, downstream performance?
- How should the passage of time shape what gets retrieved?
- How should a fixed attention budget be allocated across competing items?
- How do these primitives interact when composed into a pipeline?
- How robust are these strategies when the input is adversarial?

A fuller statement of intent lives in the [repository thesis](docs/thesis.md),
the testable form in the [research questions](docs/research-questions.md), and the
boundaries in the [non-goals](docs/non-goals.md).

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
| [Roadmap](docs/roadmap.md) | Phase plan and current status |
| [ADRs](docs/adr/) | Architecture decision records |

## Status

**Phase 7 — Interaction effects.** Building on the Phase 1 harness and the
selection, compression, temporal, retention, and attention work, the lab now runs
controlled experiments on *interactions between primitives*: how those primitives
behave when chained into a pipeline. It adds a small composition layer
(`PipelineStep`, `StrategyComposition`, `CompositionResult`), built-in
compositions that reuse existing primitives (`temporal->selection`,
`attention->selection`, `retention->attention`, `temporal->retention`,
`retention->selection`, two compression-ending pipelines, and an `oracle-pipeline`
ceiling), a synthetic `interaction-context-pipeline` benchmark with three presets
(`balanced-interaction`, `memory-pressure`, `noisy-context`), interaction metrics,
four reproducible experiments comparing primitive-only baselines against composed
pipelines, and a Markdown report. Phase 7 **composes existing primitives only** —
no new primitive algorithm, scheduler, agent, or planner — with no external API
and no LLM. Results are **early and benchmark-specific**: they use controlled
synthetic data, `oracle-pipeline` is an upper bound (not deployable), and every
observation is about a *specific composition*, not a general claim about context
systems. See the [Phase 7 summary](docs/phase-7-summary.md) and
[interaction benchmarks](docs/interaction-benchmarks.md).

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
