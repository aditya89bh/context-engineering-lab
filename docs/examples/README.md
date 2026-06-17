# Example artifacts

A tiny, checked-in example of what the harness produces, so the output format and
the determinism guarantee can be inspected without running a full phase.

## `easy-selection-experiment.json`

One `ExperimentResult` for the `easy-selection` benchmark at the default seed and
its smallest budget (1 item), comparing three strategies:

| Strategy | `selection_recall` | Reading |
| --- | --- | --- |
| `first-n` | 0.167 | content-blind baseline: picks the first item, usually wrong |
| `keyword-overlap` | 1.000 | query-aware selection finds the relevant item |
| `oracle` | 1.000 | the achievable ceiling |

The contrast — a content-blind baseline well below a query-aware strategy, which
in turn matches the oracle ceiling — is exactly the kind of evidence the lab
produces at scale.

## Portability note

Every field is deterministic except the two environment *observations*,
`metadata.python_version` and `metadata.platform`, which describe the machine that
generated the file. In this checked-in copy both are set to the literal
`"example"` so the reference is portable across machines. The `run_id` is a digest
of the *configuration* (not the machine), so it is stable.

## Regenerating

```python
import json
from context_engineering_lab import Experiment, ExperimentRunner
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.catalog import (
    build_strategy_registry,
    build_benchmark_registry,
)
from context_engineering_lab.seeding import DEFAULT_SEED

strategies = build_strategy_registry()
benchmark = build_benchmark_registry().get("easy-selection")
experiment = Experiment(
    experiment_id=ExperimentId("example-easy-selection"),
    benchmark=benchmark,
    strategies=(
        strategies.get("first-n"),
        strategies.get("keyword-overlap"),
        strategies.get("oracle"),
    ),
    seeds=(DEFAULT_SEED,),
    budgets=(benchmark.budget_sweep[0],),
)
data = ExperimentRunner().run(experiment).to_dict()
data["metadata"]["python_version"] = "example"  # normalize machine observations
data["metadata"]["platform"] = "example"
print(json.dumps(data, indent=2, sort_keys=True))
```

`tests/test_reproducibility_example.py` runs exactly this and asserts the result
matches the checked-in file byte-for-byte (after normalizing the two observation
fields), which is the executable form of the
[reproducibility guarantee](../reproducibility.md).
