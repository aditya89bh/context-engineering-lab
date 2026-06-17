"""Phase 10 Markdown reporting for robustness under perturbation.

Turns a
:class:`~context_engineering_lab.perturbations.aggregation.RobustnessAggregation`
(or the result artifacts behind it) into a plain-text Markdown report: which
perturbations were applied, per-perturbation degradation tables, a per-strategy
sensitivity summary, an oracle-gap-under-perturbation table, and a set of
mechanical observations. Tables are dependency-free Markdown; there are no charts.

Every statement names the strategy, benchmark, perturbation, and metric it refers
to, as Phase 10 requires. Numbers are specific to the Phase 8 naturalistic
benchmarks, seeds, and budgets behind the artifacts; nothing here is a claim about
real-world systems, and ``oracle`` strategies are ceilings, not deployable ones.
"""

from __future__ import annotations

from collections.abc import Sequence
from statistics import fmean

from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.experiments.phase10 import RobustnessSpec
from context_engineering_lab.perturbations.aggregation import (
    GroupComparison,
    RobustnessAggregation,
    aggregate_robustness,
)

#: How many degradation rows to list per perturbation before truncating.
_MAX_DEGRADATION_ROWS = 12


def _fmt(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "-"


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _provenance(robustness: RobustnessAggregation) -> list[str]:
    return [
        "## provenance",
        "",
        f"- stress groups: {len(robustness.groups())}",
        f"- perturbations: {len(robustness.perturbations())}",
        f"- comparisons: {len(robustness.comparisons)}",
        f"- oracle-gap shifts: {len(robustness.oracle_shifts)}",
        "",
    ]


def _perturbation_section(specs: Sequence[RobustnessSpec]) -> list[str]:
    rows = [
        [spec.group, str(spec.benchmark.id), ", ".join(spec.perturbations)]
        for spec in specs
    ]
    return [
        "## perturbations applied",
        "",
        *_table(("group", "benchmark", "perturbations"), rows),
        "",
    ]


def _degradation_section(robustness: RobustnessAggregation) -> list[str]:
    lines = ["## degradation by perturbation", ""]
    for group in robustness.groups():
        rows = robustness.for_group(group)
        by_perturbation: dict[str, list[GroupComparison]] = {}
        for row in rows:
            by_perturbation.setdefault(row.comparison.perturbation_id, []).append(row)
        for perturbation_id in sorted(by_perturbation):
            comparisons = sorted(
                by_perturbation[perturbation_id],
                key=lambda r: (-r.comparison.degradation, r.comparison.strategy_id),
            )
            benchmark = comparisons[0].comparison.benchmark_id
            lines.append(f"### {group} / {perturbation_id} ({benchmark})")
            lines.append("")
            table_rows = [
                [
                    row.comparison.strategy_id,
                    row.comparison.metric,
                    _fmt(row.comparison.baseline_value),
                    _fmt(row.comparison.perturbed_value),
                    _fmt(row.comparison.degradation),
                    _fmt(row.comparison.robustness),
                ]
                for row in comparisons[:_MAX_DEGRADATION_ROWS]
            ]
            lines.extend(
                _table(
                    (
                        "strategy",
                        "metric",
                        "baseline",
                        "perturbed",
                        "degradation",
                        "robustness",
                    ),
                    table_rows,
                )
            )
            if len(comparisons) > _MAX_DEGRADATION_ROWS:
                extra = len(comparisons) - _MAX_DEGRADATION_ROWS
                lines.append("")
                lines.append(f"_... {extra} more rows omitted._")
            lines.append("")
    return lines


def _sensitivity_section(robustness: RobustnessAggregation) -> list[str]:
    by_strategy: dict[str, list[GroupComparison]] = {}
    for row in robustness.comparisons:
        by_strategy.setdefault(row.comparison.strategy_id, []).append(row)
    rows = []
    for strategy_id in sorted(by_strategy):
        comps = [r.comparison for r in by_strategy[strategy_id]]
        rows.append(
            [
                strategy_id,
                str(len(comps)),
                _fmt(fmean(c.degradation for c in comps)),
                _fmt(max(c.degradation for c in comps)),
                _fmt(min(c.robustness for c in comps)),
            ]
        )
    rows.sort(key=lambda r: (-float(r[2]), r[0]))
    return [
        "## strategy sensitivity",
        "",
        "Mean / worst degradation and worst robustness across all "
        "(benchmark, perturbation, metric) comparisons.",
        "",
        *_table(
            (
                "strategy",
                "comparisons",
                "mean degradation",
                "worst degradation",
                "worst robustness",
            ),
            rows,
        ),
        "",
    ]


def _oracle_gap_section(robustness: RobustnessAggregation) -> list[str]:
    shifts = sorted(
        robustness.oracle_shifts,
        key=lambda s: (-s.gap_increase, s.strategy_id),
    )
    rows = [
        [
            shift.group,
            shift.strategy_id,
            shift.benchmark_id,
            shift.perturbation_id,
            shift.metric,
            _fmt(shift.baseline_gap),
            _fmt(shift.perturbed_gap),
            _fmt(shift.gap_increase),
        ]
        for shift in shifts
    ]
    return [
        "## oracle gap under perturbation",
        "",
        "Oriented distance from the oracle ceiling on each benchmark's primary "
        "metric, baseline vs perturbed. A positive increase means the gap widened.",
        "",
        *_table(
            (
                "group",
                "strategy",
                "benchmark",
                "perturbation",
                "metric",
                "baseline gap",
                "perturbed gap",
                "increase",
            ),
            rows,
        ),
        "",
    ]


def _observations(robustness: RobustnessAggregation) -> list[str]:
    lines = ["## observations", ""]
    for group in robustness.groups():
        comps = [r.comparison for r in robustness.for_group(group)]
        if not comps:
            continue
        worst = max(comps, key=lambda c: c.degradation)
        best = min(comps, key=lambda c: c.degradation)
        lines.append(
            f"- Under `{worst.perturbation_id}` on the `{worst.benchmark_id}` "
            f"benchmark, `{worst.strategy_id}` showed the largest degradation "
            f"({_fmt(worst.degradation)}) in `{worst.metric}`."
        )
        lines.append(
            f"- Under `{best.perturbation_id}` on the `{best.benchmark_id}` "
            f"benchmark, `{best.strategy_id}` was the least affected "
            f"(degradation {_fmt(best.degradation)}) in `{best.metric}`."
        )
    if robustness.oracle_shifts:
        widest = max(robustness.oracle_shifts, key=lambda s: s.gap_increase)
        lines.append(
            f"- The oracle gap widened most for `{widest.strategy_id}` on the "
            f"`{widest.benchmark_id}` benchmark under `{widest.perturbation_id}` "
            f"in `{widest.metric}` (+{_fmt(widest.gap_increase)})."
        )
    lines.append("")
    return lines


def render_report(
    robustness: RobustnessAggregation, specs: Sequence[RobustnessSpec]
) -> str:
    """Render the full Phase 10 robustness report as Markdown text.

    Args:
        robustness: The aggregated robustness rows.
        specs: The stress groups, used for the perturbations-applied table.

    Returns:
        A Markdown document string.
    """
    lines = ["# Phase 10 robustness report", ""]
    lines.extend(_provenance(robustness))
    lines.extend(_perturbation_section(specs))
    lines.extend(_degradation_section(robustness))
    lines.extend(_sensitivity_section(robustness))
    lines.extend(_oracle_gap_section(robustness))
    lines.extend(_observations(robustness))
    return "\n".join(lines).rstrip() + "\n"


def render_from_results(
    results: Sequence[ExperimentResult], specs: Sequence[RobustnessSpec]
) -> str:
    """Aggregate ``results`` against ``specs`` and render the report."""
    return render_report(aggregate_robustness(results, specs), specs)
