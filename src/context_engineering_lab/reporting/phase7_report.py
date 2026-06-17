"""Phase 7 Markdown reporting.

Turns one or more :class:`~context_engineering_lab.core.results.ExperimentResult`
records from the interaction experiments into a plain-text Markdown report:
provenance, a recall table and a harmful-retention table by strategy and budget,
an interaction-metric table contrasting each pipeline with its constituent
baselines, a by-metric summary, mechanical observations, and explicit
limitations. Tables are dependency-free Markdown; there are no charts.

The observations are mechanical summaries of the numbers in the tables, phrased
about specific compositions on these synthetic benchmarks, seeds, and budgets.
They are not general claims about context systems. ``oracle-pipeline`` reads
ground-truth relevance and is an upper bound, not a deployable strategy.
"""

from __future__ import annotations

from collections.abc import Mapping
from statistics import fmean

from context_engineering_lab.core.interaction_metrics import (
    compensation_effect,
    degradation_rate,
    interaction_gain,
)
from context_engineering_lab.core.results import ExperimentResult, StrategyRunResult

_ORACLE = "oracle-pipeline"
_QUALITY = "selection_recall"
_COST = "harmful_retention_rate"

#: For each pipeline: the baseline standing in for its final stage, and all of
#: its constituent baselines. Used to contrast a composition with its parts.
_CONSTITUENTS: dict[str, tuple[str, tuple[str, ...]]] = {
    "temporal->selection": (
        "keyword-overlap",
        ("sliding-window-5", "keyword-overlap"),
    ),
    "attention->selection": (
        "keyword-overlap",
        ("adaptive-allocation", "keyword-overlap"),
    ),
    "retention->attention": (
        "adaptive-allocation",
        ("frequency-retention", "adaptive-allocation"),
    ),
    "temporal->retention": (
        "frequency-retention",
        ("sliding-window-5", "frequency-retention"),
    ),
    "retention->selection": (
        "keyword-overlap",
        ("frequency-retention", "keyword-overlap"),
    ),
}


def _budget_limits(result: ExperimentResult) -> list[int]:
    seen: list[int] = []
    for limit, _unit in result.metadata.budgets:
        if limit not in seen:
            seen.append(limit)
    return seen


def _mean_at_budget(
    run: StrategyRunResult, metric: str, budget_limit: int
) -> float | None:
    values = [
        m.value
        for m in run.metrics
        if m.name == metric and m.budget_limit == budget_limit
    ]
    return fmean(values) if values else None


def _mean_overall(run: StrategyRunResult, metric: str) -> float | None:
    values = [m.value for m in run.metrics if m.name == metric]
    return fmean(values) if values else None


def _fmt(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "-"


def _runs_by_id(result: ExperimentResult) -> dict[str, StrategyRunResult]:
    return {run.strategy_id: run for run in result.results}


def _constituent_means(
    runs: dict[str, StrategyRunResult], ids: tuple[str, ...], metric: str
) -> list[float]:
    means: list[float] = []
    for cid in ids:
        run = runs.get(cid)
        if run is None:
            continue
        value = _mean_overall(run, metric)
        if value is not None:
            means.append(value)
    return means


def _metric_table(result: ExperimentResult, metric: str) -> list[str]:
    limits = _budget_limits(result)
    header = "| strategy | " + " | ".join(f"b={limit}" for limit in limits) + " |"
    divider = "| --- | " + " | ".join("---" for _ in limits) + " |"
    rows = [header, divider]
    for run in result.results:
        cells = [_fmt(_mean_at_budget(run, metric, limit)) for limit in limits]
        rows.append(f"| {run.strategy_id} | " + " | ".join(cells) + " |")
    return rows


def _summary_table(result: ExperimentResult) -> list[str]:
    metric_names = sorted({m.name for run in result.results for m in run.metrics})
    header = "| strategy | " + " | ".join(metric_names) + " |"
    divider = "| --- | " + " | ".join("---" for _ in metric_names) + " |"
    rows = [header, divider]
    for run in result.results:
        cells = [_fmt(_mean_overall(run, name)) for name in metric_names]
        rows.append(f"| {run.strategy_id} | " + " | ".join(cells) + " |")
    return rows


def _interaction_table(result: ExperimentResult) -> list[str]:
    runs = _runs_by_id(result)
    header = (
        "| pipeline | vs (final-stage) | gain(recall) | degradation(recall) "
        "| compensation(recall) | gain(harmful) |"
    )
    divider = "| --- | --- | --- | --- | --- | --- |"
    rows = [header, divider]
    for pipeline, (reference, constituents) in _CONSTITUENTS.items():
        run = runs.get(pipeline)
        ref = runs.get(reference)
        if run is None or ref is None:
            continue
        pipe_recall = _mean_overall(run, _QUALITY)
        ref_recall = _mean_overall(ref, _QUALITY)
        pipe_harm = _mean_overall(run, _COST)
        ref_harm = _mean_overall(ref, _COST)
        gain = (
            interaction_gain(pipe_recall, ref_recall)
            if pipe_recall is not None and ref_recall is not None
            else None
        )
        degr = (
            degradation_rate(pipe_recall, ref_recall)
            if pipe_recall is not None and ref_recall is not None and ref_recall > 0
            else None
        )
        constituent_recalls = _constituent_means(runs, constituents, _QUALITY)
        comp = (
            compensation_effect(pipe_recall, constituent_recalls)
            if pipe_recall is not None and constituent_recalls
            else None
        )
        gain_harm = (
            interaction_gain(pipe_harm, ref_harm)
            if pipe_harm is not None and ref_harm is not None
            else None
        )
        rows.append(
            f"| {pipeline} | {reference} | {_fmt(gain)} | {_fmt(degr)} "
            f"| {_fmt(comp)} | {_fmt(gain_harm)} |"
        )
    return rows


def _observations(result: ExperimentResult) -> list[str]:
    runs = _runs_by_id(result)
    name = result.metadata.experiment_id
    lines: list[str] = []
    oracle = runs.get(_ORACLE)
    if oracle is not None:
        ceiling = _mean_overall(oracle, _QUALITY)
        lines.append(
            f"- oracle mean {_QUALITY} = {_fmt(ceiling)} (ceiling, not deployable)."
        )
    for pipeline, (reference, constituents) in _CONSTITUENTS.items():
        run = runs.get(pipeline)
        ref = runs.get(reference)
        if run is None or ref is None:
            continue
        pipe_harm = _mean_overall(run, _COST)
        ref_harm = _mean_overall(ref, _COST)
        improved = (
            pipe_harm is not None
            and ref_harm is not None
            and pipe_harm + 0.01 < ref_harm
        )
        if improved:
            assert pipe_harm is not None and ref_harm is not None
            lines.append(
                f"- under `{name}`, {pipeline} reduced {_COST} relative to "
                f"{reference} alone ({ref_harm:.2f} -> {pipe_harm:.2f})."
            )
        pipe_recall = _mean_overall(run, _QUALITY)
        ref_recall = _mean_overall(ref, _QUALITY)
        if (
            pipe_recall is not None
            and ref_recall is not None
            and pipe_recall + 0.01 < ref_recall
        ):
            lines.append(
                f"- under `{name}`, {pipeline} reduced {_QUALITY} relative to "
                f"{reference} alone ({ref_recall:.2f} -> {pipe_recall:.2f})."
            )
        constituent_recalls = _constituent_means(runs, constituents, _QUALITY)
        if pipe_recall is not None and constituent_recalls:
            comp = compensation_effect(pipe_recall, constituent_recalls)
            if comp > 0.01:
                lines.append(
                    f"- under `{name}`, {pipeline} exceeded the best of its "
                    f"constituents on {_QUALITY} by {comp:.2f}."
                )
    if not lines:
        lines.append("- no interaction effect exceeded the reporting threshold.")
    return lines


def render_experiment(result: ExperimentResult) -> str:
    """Render a single interaction experiment result to a Markdown section.

    Args:
        result: The experiment result to render.

    Returns:
        A Markdown string for this experiment.
    """
    meta = result.metadata
    budgets = ", ".join(f"{limit}{unit}" for limit, unit in meta.budgets)
    lines = [
        f"## {meta.experiment_id}",
        "",
        f"- benchmark: `{meta.benchmark_id}` (v{meta.benchmark_version})",
        f"- run_id: `{meta.run_id.value}`",
        f"- strategies: {', '.join(meta.strategy_ids)}",
        f"- seeds: {', '.join(str(s) for s in meta.seeds)}",
        f"- budgets: {budgets}",
        "",
        f"### {_QUALITY} by strategy and budget (higher is better)",
        "",
        *_metric_table(result, _QUALITY),
        "",
        f"### {_COST} by strategy and budget (lower is better)",
        "",
        *_metric_table(result, _COST),
        "",
        "### interaction metrics (pipeline vs its constituent baselines)",
        "",
        *_interaction_table(result),
        "",
        "### mean over seeds and budgets, by metric",
        "",
        *_summary_table(result),
        "",
        "### observations (this benchmark only)",
        "",
        *_observations(result),
        "",
    ]
    return "\n".join(lines)


def render_report(results: Mapping[str, ExperimentResult]) -> str:
    """Render a full Phase 7 report from named experiment results.

    Args:
        results: Mapping of experiment name to its result, in insertion order.

    Returns:
        A complete Markdown report string.
    """
    sections = [
        "# Phase 7 report: interactions between primitives",
        "",
        "Controlled, synthetic experiments on the `interaction-context-pipeline`",
        "benchmark family. Phase 7 studies how the Phase 2-6 primitives interact",
        "when chained into linear pipelines; it reuses those primitives unchanged",
        "and introduces no new algorithm. Each pipeline is shown against its",
        "constituent baselines run alone. Results are early and specific to these",
        "benchmarks, seeds, and budgets, and are about specific compositions, not",
        "context systems in general. `oracle-pipeline` reads ground-truth relevance",
        "and is not a deployable strategy.",
        "",
    ]
    for result in results.values():
        sections.append(render_experiment(result))
    sections.extend(
        [
            "## limitations",
            "",
            "- Benchmarks are synthetic and deliberately simple.",
            "- Pipelines are linear chains, not workflow graphs or schedulers.",
            "- Compositions reuse existing primitives; no new algorithm is studied.",
            "- Metrics are aggregated over a small number of seeds.",
            "- Interaction metrics contrast a pipeline with chosen baselines; they",
            "  depend on which primitive instance stands in for each stage.",
            "- `oracle-pipeline` results are a ceiling, not an achievable target.",
            "- Observations describe these benchmarks only; they are not general",
            "  claims about context systems.",
            "",
        ]
    )
    return "\n".join(sections)
