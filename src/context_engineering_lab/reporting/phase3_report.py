"""Phase 3 Markdown reporting.

Turns one or more :class:`~context_engineering_lab.core.results.ExperimentResult`
records from the compression experiments into a plain-text Markdown report:
provenance, an information-retention table and a compression-ratio table by
strategy and budget, mechanical observations, and explicit limitations. Tables
are dependency-free Markdown; there are no charts.

The observations are mechanical summaries of the numbers in the tables. They are
specific to these synthetic benchmarks, seeds, and budgets, are not general
claims about compression or summarization, and ``oracle-compression`` is an upper
bound that reads ground-truth facts and is not deployable.
"""

from __future__ import annotations

from collections.abc import Mapping
from statistics import fmean

from context_engineering_lab.core.results import ExperimentResult, StrategyRunResult

_ORACLE = "oracle-compression"
_RETENTION = "information_retention"
_RATIO = "compression_ratio"


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


def _observations(result: ExperimentResult) -> list[str]:
    oracle = next((r for r in result.results if r.strategy_id == _ORACLE), None)
    others = [r for r in result.results if r.strategy_id != _ORACLE]
    lines: list[str] = []
    if oracle is not None:
        ceiling = _mean_overall(oracle, _RETENTION)
        ratio = _mean_overall(oracle, _RATIO)
        lines.append(
            f"- oracle mean {_RETENTION} = {_fmt(ceiling)} at mean "
            f"{_RATIO} = {_fmt(ratio)} (ceiling, not deployable)."
        )
    scored: list[tuple[str, float]] = []
    for run in others:
        value = _mean_overall(run, _RETENTION)
        if value is not None:
            scored.append((run.strategy_id, value))
    if scored:
        best = max(scored, key=lambda pair: pair[1])
        worst = min(scored, key=lambda pair: pair[1])
        lines.append(
            f"- best non-oracle strategy by mean {_RETENTION}: "
            f"{best[0]} ({best[1]:.2f})."
        )
        lines.append(
            f"- weakest non-oracle strategy by mean {_RETENTION}: "
            f"{worst[0]} ({worst[1]:.2f})."
        )
    return lines


def render_experiment(result: ExperimentResult) -> str:
    """Render a single compression experiment result to a Markdown section.

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
        f"### {_RETENTION} by strategy and budget",
        "",
        *_metric_table(result, _RETENTION),
        "",
        f"### {_RATIO} by strategy and budget",
        "",
        *_metric_table(result, _RATIO),
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
    """Render a full Phase 3 report from named experiment results.

    Args:
        results: Mapping of experiment name to its result, in insertion order.

    Returns:
        A complete Markdown report string.
    """
    sections = [
        "# Phase 3 report: compression under budget pressure",
        "",
        "Controlled, synthetic experiments on the `compression-fact-preservation`",
        "benchmark family, using deterministic compression only (no LLM",
        "summarization, no external calls). Results are early and specific to",
        "these benchmarks, seeds, and budgets. `no-compression` ignores the budget",
        "(its `budget_utilization` may exceed 1); `oracle-compression` reads",
        "ground-truth facts and is not a deployable strategy.",
        "",
    ]
    for result in results.values():
        sections.append(render_experiment(result))
    sections.extend(
        [
            "## limitations",
            "",
            "- Benchmarks are synthetic and deliberately simple.",
            "- Compression is deterministic and extractive; no summarization.",
            "- Metrics are aggregated over a small number of seeds.",
            "- `oracle-compression` results are a ceiling, not achievable.",
            "- Observations describe these benchmarks only; they are not general",
            "  claims about compression or context engineering.",
            "",
        ]
    )
    return "\n".join(sections)
