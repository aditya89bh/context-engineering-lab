# context-engineering-lab

> Experiments in salience, compression, temporal context, and attention.

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
| [Roadmap](docs/roadmap.md) | Phase plan and current status |
| [ADRs](docs/adr/) | Architecture decision records |

## Status

**Phase 3 — Compression.** Building on the Phase 1 harness and the Phase 2
selection work, the lab now runs controlled experiments on *deterministic
compression under budget pressure*. It ships six compressors (`no-compression`,
`head-truncation`, `tail-truncation`, `keyword-preserving`, `sentence-boundary`,
and an `oracle-compression` ceiling), a synthetic `compression-fact-preservation`
benchmark with three presets, compression metrics, four reproducible experiments,
and a Markdown report. There is **no LLM summarization** and no external API.
Results are **early and benchmark-specific**: they use controlled synthetic data,
`oracle-compression` is an upper bound (not deployable), and nothing here is a
general claim about summarization or context engineering. See the
[Phase 3 summary](docs/phase-3-summary.md) and
[compression benchmarks](docs/compression-benchmarks.md).

## Running the harness

```bash
context-lab list                                   # registered strategies/benchmarks
context-lab run-smoke --output artifacts/smoke-result.json
context-lab run-phase2 --output artifacts/phase2   # Phase 2 selection suite + report
context-lab run-phase3 --output artifacts/phase3   # Phase 3 compression suite + report
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
