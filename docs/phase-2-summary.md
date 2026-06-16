# Phase 2 summary

Phase 2 runs the first real controlled experiments on the harness from Phase 1.
It studies **selection under budget pressure**: what deserves to enter a limited
context window as budgets shrink, distractors increase, and target position
changes. For the benchmark design see
[selection-benchmarks.md](selection-benchmarks.md).

## What Phase 2 added

- Five selection strategies beyond recency: `first-n`, `last-n`, `random`
  (deterministic), `keyword-overlap`, and `oracle` (a ceiling).
- A shared greedy budget-fill helper so each strategy implements only its
  ordering.
- The `selection-signal-retrieval` benchmark generator and three presets:
  `easy-selection`, `position-biased-selection`, `high-distractor-selection`.
- A Phase 2 derived metric, `budget_utilization`, alongside the existing
  `answer_support`, `selection_recall`, and `selection_precision`.
- Four reproducible experiments: `selection-baselines-easy`,
  `selection-position-bias`, `selection-distractor-stress`,
  `selection-budget-sweep`.
- A Markdown reporting module and a `context-lab run-phase2` command.

## Strategies as bounds

The line-up is deliberately structured as bounds, not as a leaderboard of
deployable systems:

- **Lower bounds:** the content-blind baselines (`first-n`, `last-n`, `recency`,
  `random`). They succeed only by position or luck.
- **Crude middle:** `keyword-overlap`, the simplest content-aware selector.
- **Upper bound:** `oracle`, which reads ground-truth relevance and is **not
  deployable**. It measures how much headroom remains, nothing more.

### Note on `random` determinism

`RandomSelection` is deterministic and *content-addressed*: it does not receive
the experiment seed directly. The current `Strategy.select(candidates, task,
budget)` interface carries no seed, run id, or case id, so the strategy derives
its per-call seed from its own base seed combined with the ids of the candidates
it is given. Two calls with the same candidate set therefore always produce the
same selection.

This means the variation in `random` results across Phase 2 seeds comes
*primarily from the benchmark*: different experiment seeds make the generator
emit different candidate sets (different distractor content and target
placement), and the strategy's content-addressed seed changes with them. It is
not the experiment seed flowing into the strategy. The behaviour is fully
reproducible, but the source of its randomness is the generated data, not a seed
handed to the strategy. See the deferred `StrategyContext` note in
[architecture.md](architecture.md).

## Observations (these benchmarks only)

Run `context-lab run-phase2` to regenerate the tables. The headline patterns,
which are specific to these synthetic benchmarks, seeds, and budgets:

- **Salience can beat recency — when content separates targets.** On
  `easy-selection`, `keyword-overlap` reaches the oracle ceiling and clearly
  beats recency at tight budgets. On `high-distractor-selection`, where
  distractors share every signal term, that advantage vanishes and keyword
  overlap falls back to baseline levels. (RQ1)
- **Order-only baselines can be right for the wrong reason.** On
  `position-biased-selection` (target always late), `first-n` fails at small
  budgets while `last-n` and `recency` succeed — by position, not relevance.
  (RQ13)
- **Heavy, look-alike distractors collapse precision and recall** for every
  non-oracle strategy; only the oracle stays reliable. (RQ9)
- **The budget curve rises smoothly here.** On `selection-budget-sweep`,
  non-oracle answer support increases gradually with the item budget with no
  sharp cliff on this benchmark; the oracle is flat at the ceiling. (RQ2)

These begin to address [research questions](research-questions.md) RQ1, RQ2, RQ9,
and the newly added RQ13. They do not close any of them.

## What Phase 2 does not claim

- **No general conclusions.** Every observation is specific to synthetic
  benchmarks, a handful of seeds, and item budgets. None generalizes to real
  corpora or to context engineering at large.
- **The oracle is not achievable.** It is a measurement ceiling, not a target.
- **`keyword-overlap` is not "the salience strategy."** It is the crudest
  possible content signal, included as a reference point.
- **No tuning, no significance testing.** Results are aggregated means over a few
  seeds, reported as-is.

Later phases (compression, temporal decay, forgetting, attention allocation) are
out of scope here; see the [roadmap](roadmap.md).

## Running validation

```bash
pip install -e ".[dev]"
ruff check .       # lint
mypy               # strict type check
pytest             # tests
python -m build    # build sdist + wheel
```
