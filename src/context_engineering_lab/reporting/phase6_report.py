"""Phase 6 Markdown reporting.

Turns one or more :class:`~context_engineering_lab.core.results.ExperimentResult`
records from the attention experiments into a plain-text Markdown report:
provenance, a signal-capture table and a wasted-attention table by allocator and
budget, a by-metric summary, mechanical observations, and explicit limitations.
Tables are dependency-free Markdown; there are no charts.

The observations are mechanical summaries of the numbers in the tables. They are
specific to these synthetic benchmarks, seeds, and budgets, are not general
claims about attention mechanisms, and ``oracle-allocation`` is an upper bound
that reads ground-truth signal counts and is not deployable.
"""

from __future__ import annotations

from collections.abc import Mapping
from statistics import fmean

from context_engineering_lab.core.results import ExperimentResult, StrategyRunResult

_ORACLE = "oracle-allocation"
_CAPTURE = "signal_capture_rate"
_WASTED = "wasted_attention_rate"


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
    header = "| allocator | " + " | ".join(f"b={limit}" for limit in limits) + " |"
    divider = "| --- | " + " | ".join("---" for _ in limits) + " |"
    rows = [header, divider]
    for run in result.results:
        cells = [_fmt(_mean_at_budget(run, metric, limit)) for limit in limits]
        rows.append(f"| {run.strategy_id} | " + " | ".join(cells) + " |")
    return rows


def _summary_table(result: ExperimentResult) -> list[str]:
    metric_names = sorted({m.name for run in result.results for m in run.metrics})
    header = "| allocator | " + " | ".join(metric_names) + " |"
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
        ceiling = _mean_overall(oracle, _CAPTURE)
        lines.append(
            f"- oracle mean {_CAPTURE} = {_fmt(ceiling)} (ceiling, not deployable)."
        )
    captured: list[tuple[str, float]] = []
    for run in others:
        value = _mean_overall(run, _CAPTURE)
        if value is not None:
            captured.append((run.strategy_id, value))
    if captured:
        best = max(captured, key=lambda pair: pair[1])
        worst = min(captured, key=lambda pair: pair[1])
        lines.append(
            f"- best non-oracle allocator by mean {_CAPTURE}: "
            f"{best[0]} ({best[1]:.2f})."
        )
        lines.append(
            f"- weakest non-oracle allocator by mean {_CAPTURE}: "
            f"{worst[0]} ({worst[1]:.2f})."
        )
    wasted: list[tuple[str, float]] = []
    for run in others:
        value = _mean_overall(run, _WASTED)
        if value is not None:
            wasted.append((run.strategy_id, value))
    if wasted:
        worst_waste = max(wasted, key=lambda pair: pair[1])
        lines.append(
            f"- highest mean {_WASTED} among non-oracle allocators: "
            f"{worst_waste[0]} ({worst_waste[1]:.2f})."
        )
    return lines


def render_experiment(result: ExperimentResult) -> str:
    """Render a single attention experiment result to a Markdown section.

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
        f"- allocators: {', '.join(meta.strategy_ids)}",
        f"- seeds: {', '.join(str(s) for s in meta.seeds)}",
        f"- budgets: {budgets}",
        "",
        f"### {_CAPTURE} by allocator and budget (higher is better)",
        "",
        *_metric_table(result, _CAPTURE),
        "",
        f"### {_WASTED} by allocator and budget (lower is better)",
        "",
        *_metric_table(result, _WASTED),
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
    """Render a full Phase 6 report from named experiment results.

    Args:
        results: Mapping of experiment name to its result, in insertion order.

    Returns:
        A complete Markdown report string.
    """
    sections = [
        "# Phase 6 report: attention allocation across sources",
        "",
        "Controlled, synthetic experiments on the `attention-source-allocation`",
        "benchmark family. Phase 6 studies allocation as a *policy* — how a budget",
        "should be split across competing sources before selection — not a",
        "scheduler or agent. Allocation is distinct from selection: the inner",
        "selection that fills each source's share is identical for every allocator,",
        "so differences come only from the split. Results are early and specific to",
        "these benchmarks, seeds, and budgets. `oracle-allocation` reads",
        "ground-truth signal counts and is not a deployable allocator.",
        "",
    ]
    for result in results.values():
        sections.append(render_experiment(result))
    sections.extend(
        [
            "## limitations",
            "",
            "- Benchmarks are synthetic and deliberately simple.",
            "- Allocation is studied as a one-shot budget split, not a scheduler.",
            "- Metrics are aggregated over a small number of seeds.",
            "- `oracle-allocation` results are a ceiling, not an achievable target.",
            "- Observations describe these benchmarks only; they are not general",
            "  claims about attention mechanisms.",
            "",
        ]
    )
    return "\n".join(sections)
