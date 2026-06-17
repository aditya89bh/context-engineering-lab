"""Named presets of the interaction benchmark.

Three presets of the ``interaction-context-pipeline`` generator, each tuned to a
distinct interaction regime: a balanced case where primitives have little to
correct in each other, a memory-pressure case where harmful traps and tight
budgets force a forgetting stage to matter, and a noisy case dense with stale and
distractor items. Three is intentionally enough; more would add combinations
without adding insight.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.interaction import (
    InteractionBenchmark,
    InteractionConfig,
)
from context_engineering_lab.core.budget import Budget, BudgetUnit

_BUDGET_SWEEP: tuple[Budget, ...] = (
    Budget(4, BudgetUnit.ITEMS),
    Budget(8, BudgetUnit.ITEMS),
    Budget(12, BudgetUnit.ITEMS),
    Budget(16, BudgetUnit.ITEMS),
)


def balanced_interaction() -> InteractionBenchmark:
    """Comparable sources, few traps, relevant signal spread over time.

    Construct: when traps and stale items are sparse, a single good primitive is
    often enough and composing adds little. This is the preset where pipelines
    should roughly match their strongest constituent, not beat it.
    """
    return InteractionBenchmark(
        InteractionConfig(
            benchmark_id="balanced-interaction",
            version="1.0",
            construct="composition when traps and stale items are sparse",
            num_cases=24,
            num_sources=3,
            num_relevant=8,
            num_required=2,
            num_stale=3,
            num_harmful=3,
            num_distractor=6,
            source_imbalance="low",
            signal_concentration="spread",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "composing adds little when a single primitive already suffices",
                "a temporal pre-filter can drop spread-out relevant items",
            ),
        )
    )


def memory_pressure() -> InteractionBenchmark:
    """Many harmful traps under tight budgets; forgetting should matter.

    Construct: harmful items look relevant (carry the query terms, are salient and
    recent) and only frequency separates them from the signal. A selection- or
    attention-only pipeline keeps the traps; a retention/frequency stage before it
    should cut ``harmful_retention_rate``.
    """
    return InteractionBenchmark(
        InteractionConfig(
            benchmark_id="memory-pressure",
            version="1.0",
            construct="composition against many harmful traps under tight budgets",
            num_cases=24,
            num_sources=3,
            num_relevant=8,
            num_required=3,
            num_stale=4,
            num_harmful=10,
            num_distractor=6,
            source_imbalance="high",
            signal_concentration="concentrated",
            budget_sweep=(
                Budget(2, BudgetUnit.ITEMS),
                Budget(4, BudgetUnit.ITEMS),
                Budget(6, BudgetUnit.ITEMS),
                Budget(8, BudgetUnit.ITEMS),
            ),
            expected_failure_modes=(
                "keyword selection keeps harmful items that carry the query terms",
                "salience/recency stages keep harmful items (salient and recent)",
                "only a frequency-aware stage separates trap from signal",
            ),
        )
    )


def noisy_context() -> InteractionBenchmark:
    """Dense stale and distractor noise across many sources.

    Construct: most items are stale or off-topic, spread over time and sources. A
    temporal stage should drop the stale tail and a selection or attention stage
    should ignore the off-topic filler; the question is whether chaining them
    compounds the gains or one stage starves the next.
    """
    return InteractionBenchmark(
        InteractionConfig(
            benchmark_id="noisy-context",
            version="1.0",
            construct="composition under dense stale and distractor noise",
            num_cases=24,
            num_sources=4,
            num_relevant=8,
            num_required=2,
            num_stale=12,
            num_harmful=4,
            num_distractor=14,
            source_imbalance="high",
            signal_concentration="spread",
            budget_sweep=_BUDGET_SWEEP,
            expected_failure_modes=(
                "a temporal window drops old-but-relevant items with the stale tail",
                "distractors crowd the budget when no stage filters them",
            ),
        )
    )


def all_interaction_presets() -> tuple[InteractionBenchmark, ...]:
    """Return all three interaction presets."""
    return (
        balanced_interaction(),
        memory_pressure(),
        noisy_context(),
    )
