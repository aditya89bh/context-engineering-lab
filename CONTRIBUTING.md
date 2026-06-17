# Contributing

Thank you for considering a contribution. This repository is a research-practice
lab: the experiments are the product, so the bar for what we merge is set by
intellectual quality and reproducibility, not by volume.

Please read the [thesis](docs/thesis.md) and
[definition of done](docs/definition-of-done.md) before starting.

## Ways to contribute

- **Propose an experiment.** Open an issue using the experiment proposal
  template. Strong proposals state a question, place it in the
  [taxonomy](docs/taxonomy.md), and explain how it differs from existing work.
- **Improve a benchmark or metric.** Sharper measurement benefits every
  experiment.
- **Report a reproducibility failure.** If a documented result does not
  regenerate, that is a high-priority bug.
- **Improve the design docs.** Clearer framing is a real contribution.

## What we are unlikely to merge

- Experiments that duplicate an existing taxonomy cell without a distinct
  question.
- Strategies presented without baselines, budget sweeps, or cost.
- Features added to increase scope without answering a question.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Local checks

All of these must pass before opening a pull request:

```bash
ruff check .       # lint
mypy               # strict type check
pytest             # tests
python -m build    # packaging
```

## Commit and PR conventions

- Keep commits small and coherent; one logical change per commit.
- Write imperative, descriptive commit subjects ("Add temporal decay
  evaluator", not "update files").
- Open pull requests against `main` using the PR template.
- Code is type-annotated throughout; public functions and modules carry
  docstrings. Comments explain intent, not mechanics.

## Reproducibility expectations

Randomness derives from a single root seed via
`context_engineering_lab.seeding` (see
[ADR-0003](docs/adr/0003-deterministic-seeding.md)). Experiments run across
multiple seeds and record their configuration so results regenerate exactly. The
full protocol and a checked-in example artifact are documented in
[docs/reproducibility.md](docs/reproducibility.md), and enforced by
`tests/test_reproducibility_example.py`.

## Claims and evidence

Reported claims must be **benchmark-specific** and traceable to a number. State
the strategy, benchmark, and metric (and budget where relevant) — e.g. "on
`high-distractor-selection`, `keyword-overlap` reaches mean `answer_support`
0.21", not "keyword-overlap is weak". Evidence lives in
[RESULTS.md](RESULTS.md), interpretation in [FINDINGS.md](FINDINGS.md), and the
boundaries in [LIMITATIONS.md](LIMITATIONS.md); new results should slot into the
same structure. `oracle*` strategies are ceilings and must never be presented as
deployable.

## Code of conduct

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
