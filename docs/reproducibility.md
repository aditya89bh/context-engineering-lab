# Reproducibility

Reproducibility is a first-class requirement of this lab, not an afterthought.
Every result in this repository is regenerable bit-for-bit from a single integer
seed, on any machine, with no network access and no external services. This
document explains the guarantees, the mechanisms behind them, and how to verify
them yourself.

## The guarantee

For a fixed code version, running the same experiment definition produces:

- the **same benchmark cases** (items, content, metadata, ground truth),
- the **same strategy outputs** (the selected/compressed/retained context),
- the **same metric values**, and
- the **same run id**.

Two runs of `context-lab run-phase2` on different machines yield byte-identical
metric tables. The only fields that legitimately differ between machines are the
*recorded environment observations* (`python_version`, `platform`), which are
provenance, not inputs — see [Run identity](#run-identity) below.

## How determinism is achieved

### One seed, derived streams

All randomness descends from a single base seed (default `DEFAULT_SEED = 20260101`).
Components never call the global RNG implicitly; instead each derives an
independent, stable sub-stream with `derive_seed`:

```python
from context_engineering_lab import derive_seed

shuffle_seed = derive_seed(base_seed, "selection", "case", "3")
```

`derive_seed` hashes the base seed and labels with BLAKE2b, so the result is
stable across processes, machines, and Python versions — unlike the built-in
`hash`, which is salted per process. Benchmarks seed a local `random.Random`
instance per case rather than mutating global state, so concurrent or reordered
construction cannot change the output.

### No hidden sources of nondeterminism

- **No wall-clock time** enters any case, metric, or id. Temporal benchmarks use
  abstract, integer timestamps generated from the seed.
- **No network, no LLMs, no external APIs.** This is enforced by a guard test
  (`tests/test_no_external_api.py`) that scans the library for forbidden imports.
- **No floating-point reductions over unordered collections.** Aggregations sort
  before they fold, so ordering cannot perturb a sum.
- **Canonical JSON.** Artifacts are serialized with sorted keys and fixed
  separators, so the on-disk bytes are stable.

### Run identity

Each run records `RunMetadata` whose `run_id` is a BLAKE2b digest of the
*canonical configuration* — experiment id, benchmark id and version, strategy ids,
seeds, and budgets — and **not** of wall-clock time or the host. The same
configuration therefore always produces the same `run_id`, which makes reruns
detectable and makes two artifacts trivially comparable. Environment details
(`python_version`, `platform`) are recorded alongside as observations but are
deliberately excluded from the id, which identifies the *configuration*, not the
machine.

## Reproducing the results

```bash
# 1. Install the package and dev tooling into a clean environment.
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Regenerate any phase's artifacts and report.
context-lab run-phase2  --output artifacts/phase2
context-lab run-phase8  --output artifacts/phase8
context-lab run-phase9  --output artifacts/phase9
context-lab run-phase10 --output artifacts/phase10

# 3. Confirm a rerun is identical (no differences expected in the metric tables).
context-lab run-phase2 --output artifacts/phase2-again
diff artifacts/phase2/summary.md artifacts/phase2-again/summary.md && echo "identical"
```

Artifacts land under `artifacts/` (git-ignored): a JSON file per experiment plus a
Markdown report (`summary.md` for phases 2–8, `synthesis.md` for phase 9,
`robustness.md` for phase 10).

## Verifying determinism

The test suite encodes the guarantee directly. Many modules include a
`*_is_reproducible` test that runs a computation twice and asserts equality; the
CLI tests assert that `run-phase*` produces stable artifacts. Run them with:

```bash
pytest -k reproducible
pytest tests/test_no_external_api.py
```

A small, checked-in example artifact (see
[`docs/examples/`](examples/)) lets you confirm that a freshly generated artifact
matches a known-good reference without rerunning a whole phase.

## Pinning for exact byte-equality

Determinism holds across machines for a fixed code version. To pin a result to a
specific revision, record the commit hash alongside the artifact (the
`code_version` field in `RunMetadata` is provided for this). Different code
versions may intentionally change benchmark content or metrics; the `run_id` and
`benchmark_version` make such changes explicit rather than silent.
