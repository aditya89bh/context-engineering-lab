"""Phase 8 Markdown reporting for the naturalistic scenarios.

Turns one or more :class:`~context_engineering_lab.core.results.ExperimentResult`
records from the naturalistic experiments into a plain-text Markdown report:
provenance, an answer-support table by strategy and budget, a cost table over
whichever of the conflict / superseded / harmful / stale metrics the family
declares, a by-metric summary, mechanical observations, and explicit limitations.
Tables are dependency-free Markdown; there are no charts.

Each family declares its own metric set, so the report adapts to the metrics
present rather than assuming a fixed list. Observations are mechanical summaries
of the numbers, phrased about specific strategies on a specific synthetic
scenario, seeds, and budgets. They are not claims about real workplace context or
real-world systems. ``oracle`` reads ground-truth relevance and is an upper bound,
not a deployable strategy.
"""

from __future__ import annotations

from collections.abc import Mapping
from statistics import fmean

from context_engineering_lab.core.results import ExperimentResult, StrategyRunResult

_ORACLE = "oracle"
_QUALITY = "answer_support"
_BASELINE = "keyword-overlap"

# Cost metrics (lower is better) the report surfaces when a family declares them.
_COST_METRICS: tuple[str, ...] = (
    "conflict_selection_rate",
    "superseded_fact_retention",
    "harmful_retention_rate",
    "stale_selection_rate",
)


def _budget_limits(result: ExperimentResult) -> list[int]:
    seen: list[int] = []
    for limit, _unit in result.metadata.budgets:
        if limit not in seen:
            seen.append(limit)
    return seen


def _present_metrics(result: ExperimentResult) -> set[str]:
    return {m.name for run in result.results for m in run.metrics}


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


def _metric_table(result: ExperimentResult, metric: str) -> list[str]:
    limits = _budget_limits(result)
    header = "| strategy | " + " | ".join(f"b={limit}" for limit in limits) + " |"
    divider = "| --- | " + " | ".join("---" for _ in limits) + " |"
    rows = [header, divider]
    for run in result.results:
        cells = [_fmt(_mean_at_budget(run, metric, limit)) for limit in limits]
        rows.append(f"| {run.strategy_id} | " + " | ".join(cells) + " |")
    return rows


def _cost_table(result: ExperimentResult, metrics: list[str]) -> list[str]:
    header = "| strategy | " + " | ".join(metrics) + " |"
    divider = "| --- | " + " | ".join("---" for _ in metrics) + " |"
    rows = [header, divider]
    for run in result.results:
        cells = [_fmt(_mean_overall(run, name)) for name in metrics]
        rows.append(f"| {run.strategy_id} | " + " | ".join(cells) + " |")
    return rows


def _summary_table(result: ExperimentResult) -> list[str]:
    metric_names = sorted(_present_metrics(result))
    header = "| strategy | " + " | ".join(metric_names) + " |"
    divider = "| --- | " + " | ".join("---" for _ in metric_names) + " |"
    rows = [header, divider]
    for run in result.results:
        cells = [_fmt(_mean_overall(run, name)) for name in metric_names]
        rows.append(f"| {run.strategy_id} | " + " | ".join(cells) + " |")
    return rows


def _observations(result: ExperimentResult) -> list[str]:
    runs = _runs_by_id(result)
    present = _present_metrics(result)
    name = result.metadata.experiment_id
    lines: list[str] = []

    oracle = runs.get(_ORACLE)
    if oracle is not None:
        ceiling = _mean_overall(oracle, _QUALITY)
        lines.append(
            f"- oracle mean {_QUALITY} = {_fmt(ceiling)} (ceiling, not deployable)."
        )

    baseline = runs.get(_BASELINE)
    cost_metrics = [m for m in _COST_METRICS if m in present]
    if baseline is not None:
        for run in result.results:
            if run.strategy_id in (_ORACLE, _BASELINE):
                continue
            for metric in cost_metrics:
                value = _mean_overall(run, metric)
                ref = _mean_overall(baseline, metric)
                if (
                    value is not None
                    and ref is not None
                    and value + 0.01 < ref
                ):
                    lines.append(
                        f"- on `{name}`, {run.strategy_id} reduced {metric} relative "
                        f"to {_BASELINE} ({ref:.2f} -> {value:.2f})."
                    )

    if not lines:
        lines.append("- no contrast exceeded the reporting threshold.")
    return lines


def render_experiment(result: ExperimentResult) -> str:
    """Render a single naturalistic experiment result to a Markdown section.

    Args:
        result: The experiment result to render.

    Returns:
        A Markdown string for this experiment.
    """
    meta = result.metadata
    budgets = ", ".join(f"{limit}{unit}" for limit, unit in meta.budgets)
    present = _present_metrics(result)
    cost_metrics = [m for m in _COST_METRICS if m in present]
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
    ]
    if cost_metrics:
        lines += [
            "### conflict / superseded / harmful / stale (lower is better)",
            "",
            *_cost_table(result, cost_metrics),
            "",
        ]
    lines += [
        "### mean over seeds and budgets, by metric",
        "",
        *_summary_table(result),
        "",
        "### observations (this scenario only)",
        "",
        *_observations(result),
        "",
    ]
    return "\n".join(lines)


def render_report(results: Mapping[str, ExperimentResult]) -> str:
    """Render a full Phase 8 report from named experiment results.

    Args:
        results: Mapping of experiment name to its result, in insertion order.

    Returns:
        A complete Markdown report string.
    """
    sections = [
        "# Phase 8 report: naturalistic context benchmarks",
        "",
        "Controlled experiments on deterministic, fully synthetic benchmarks shaped",
        "like realistic working information: email threads, meeting notes, support",
        "tickets, document revisions, and memory logs. No real or private data is",
        "ingested and no LLM generates any content; every case is built from a seed.",
        "Phase 8 reuses the Phase 2-7 strategies and compositions unchanged. Results",
        "are specific to these synthetic scenarios, seeds, and budgets; they are not",
        "claims about all workplace context or all real-world systems. `oracle` reads",
        "ground-truth relevance and is a ceiling, not a deployable strategy.",
        "",
    ]
    for result in results.values():
        sections.append(render_experiment(result))
    sections.extend(
        [
            "## limitations",
            "",
            "- Benchmarks are synthetic and deterministic; naturalistic means",
            "  realistic-shaped, not real.",
            "- No real, private, or external data is ingested; no LLM is used.",
            "- Observable signals (salience, frequency, source quality) are stylised",
            "  proxies, not measurements from a real system.",
            "- The strategy lineup is curated and small, not exhaustive.",
            "- Metrics are aggregated over a small number of seeds.",
            "- `oracle` results are a ceiling, not an achievable target.",
            "- Observations describe these scenarios only; they are not general",
            "  claims about real-world context.",
            "",
        ]
    )
    return "\n".join(sections)
