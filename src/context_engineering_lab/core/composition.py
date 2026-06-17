"""Composing existing strategies into pipelines.

Phase 7 studies how the primitives built in earlier phases *interact*. It adds no
new primitive algorithm; it only chains existing strategies so the output of one
becomes the candidate set of the next. Because every primitive (selection,
temporal weighting, retention, attention allocation, compression) already
implements the :class:`~context_engineering_lab.core.strategy.Strategy`
interface, a composition is itself just a ``Strategy`` and runs through the
existing experiment runner unchanged.

The interface is deliberately small — this is a linear pipeline, not a workflow
engine or DAG:

* :class:`PipelineStep` — one stage wrapping an existing strategy.
* :class:`StepRecord` — how many items entered and left a stage.
* :class:`CompositionResult` — the final context plus the per-stage records.
* :class:`StrategyComposition` — an ordered chain of steps that is itself a
  ``Strategy``.

Pipeline semantics: every non-final step is given a *widened* budget (a multiple
of the final budget) so it prunes or transforms the candidate set without
prematurely enforcing the final limit; the final step is given the real budget
and produces the returned context. Widening is what lets an early stage hand the
next stage more than the final budget's worth of choices.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from context_engineering_lab.core.budget import Budget
from context_engineering_lab.core.context import Context
from context_engineering_lab.core.ids import StrategyId
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.strategy import Strategy
from context_engineering_lab.core.task import Task

#: Default multiple of the final budget handed to each non-final stage.
DEFAULT_WIDEN = 2


@dataclass(frozen=True, slots=True)
class PipelineStep:
    """One stage of a pipeline, wrapping an existing strategy.

    Args:
        strategy: The strategy this stage runs.
    """

    strategy: Strategy

    @property
    def id(self) -> StrategyId:
        """Stable identifier, taken from the wrapped strategy."""
        return self.strategy.id

    def run(
        self, candidates: Sequence[Item], task: Task, budget: Budget
    ) -> Context:
        """Run the wrapped strategy for this stage."""
        return self.strategy.select(candidates, task, budget)


@dataclass(frozen=True, slots=True)
class StepRecord:
    """Item accounting for a single pipeline stage.

    Args:
        step_id: Id of the stage's strategy.
        input_count: Items the stage received.
        output_count: Items the stage produced.
    """

    step_id: str
    input_count: int
    output_count: int


@dataclass(frozen=True, slots=True)
class CompositionResult:
    """The output of a pipeline: the final context and per-stage records."""

    context: Context
    steps: tuple[StepRecord, ...]


class StrategyComposition:
    """An ordered chain of strategies that is itself a strategy.

    Args:
        steps: The strategies to run in order (at least one).
        composition_id: Optional explicit id; defaults to the step ids joined
            with ``->``.
        widen: Multiple of the final budget handed to each non-final stage.

    Raises:
        ValueError: If ``steps`` is empty or ``widen < 1``.
    """

    def __init__(
        self,
        steps: Sequence[Strategy],
        composition_id: str | None = None,
        widen: int = DEFAULT_WIDEN,
    ) -> None:
        if not steps:
            raise ValueError("a composition needs at least one step")
        if widen < 1:
            raise ValueError("widen must be >= 1")
        self._steps = tuple(PipelineStep(strategy) for strategy in steps)
        self._widen = widen
        if composition_id is None:
            composition_id = "->".join(str(step.id) for step in self._steps)
        self._id = StrategyId(composition_id)

    @property
    def id(self) -> StrategyId:
        """Stable identifier for the composition."""
        return self._id

    @property
    def steps(self) -> tuple[PipelineStep, ...]:
        """The pipeline stages, in order."""
        return self._steps

    def run(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> CompositionResult:
        """Run the pipeline, returning the final context and stage records.

        Args:
            candidates: The initial candidate items.
            task: The task passed to every stage.
            budget: The final budget; non-final stages receive a widened copy.

        Returns:
            The final context and the per-stage item accounting.
        """
        running: Sequence[Item] = tuple(candidates)
        records: list[StepRecord] = []
        last = len(self._steps) - 1
        widened = Budget(max(1, budget.limit * self._widen), budget.unit)
        for index, step in enumerate(self._steps):
            stage_budget = budget if index == last else widened
            input_count = len(running)
            context = step.run(running, task, stage_budget)
            running = context.items
            records.append(
                StepRecord(
                    step_id=str(step.id),
                    input_count=input_count,
                    output_count=len(running),
                )
            )
        final = Context(items=tuple(running), budget=budget)
        return CompositionResult(context=final, steps=tuple(records))

    def select(
        self,
        candidates: Sequence[Item],
        task: Task,
        budget: Budget,
    ) -> Context:
        """Run the pipeline and return only its final context."""
        return self.run(candidates, task, budget).context
