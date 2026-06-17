"""Phase 9 Markdown reporting for cross-benchmark synthesis.

Turns an :class:`~context_engineering_lab.synthesis.aggregation.Aggregation` (or the
result artifacts behind it) into a plain-text Markdown report: provenance,
per-strategy profiles, a dominance table with the non-dominated frontier, an
oracle-gap table, a failure summary, and a stability summary. Tables are
dependency-free Markdown; there are no charts.

Every number is mechanical and specific to the Phase 2-8 synthetic benchmarks,
seeds, and budgets behind the artifacts. Nothing here is a claim about real-world
systems, and ``oracle`` strategies are ceilings, not deployable approaches.
"""

from __future__ import annotations

from collections.abc import Sequence

from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.synthesis.aggregation import Aggregation, aggregate_results
from context_engineering_lab.synthesis.dominance import (
    dominance_records,
    non_dominated_strategies,
)
from context_engineering_lab.synthesis.failure import FailureMode, analyze_failures
from context_engineering_lab.synthesis.oracle_gap import oracle_summaries
from context_engineering_lab.synthesis.profiles import generate_profiles
from context_engineering_lab.synthesis.stability import (
    ranking_volatilities,
    stability_reports,
)

#: How many failure observations to list in full before summarising the rest.
_MAX_FAILURE_ROWS = 20


def _fmt(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "-"


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _provenance(aggregation: Aggregation) -> list[str]:
    return [
        "## provenance",
        "",
        f"- benchmarks: {len(aggregation.benchmarks())}",
        f"- strategies: {len(aggregation.strategies())}",
        f"- metrics: {len(aggregation.metrics())}",
        f"- cells: {len(aggregation.cells)}",
        "",
    ]


def _profiles_section(aggregation: Aggregation) -> list[str]:
    rows = []
    for profile in generate_profiles(aggregation):
        strongest = profile.strengths[0].benchmark_id if profile.strengths else "-"
        weakest = profile.weaknesses[0].benchmark_id if profile.weaknesses else "-"
        rows.append(
            [
                profile.strategy_id,
                str(len(profile.benchmarks)),
                _fmt(profile.mean_primary),
                _fmt(profile.oracle_distance),
                strongest,
                weakest,
            ]
        )
    return [
        "## strategy profiles",
        "",
        "Mean primary is the mean of each benchmark's primary metric; oracle",
        "distance is the mean primary gap to that benchmark's oracle.",
        "",
        *_table(
            ["strategy", "benchmarks", "mean primary", "oracle dist",
             "strongest", "weakest"],
            rows,
        ),
        "",
    ]


def _dominance_section(aggregation: Aggregation) -> list[str]:
    rows = [
        [
            record.strategy_id,
            str(record.wins),
            str(record.losses),
            str(record.ties),
            str(record.net),
            _fmt(record.win_rate),
        ]
        for record in dominance_records(aggregation)
    ]
    frontier = non_dominated_strategies(aggregation)
    return [
        "## dominance",
        "",
        "Wins, losses, and ties are over shared (benchmark, metric, budget) cells,",
        "with cost metrics oriented so higher is better.",
        "",
        *_table(
            ["strategy", "wins", "losses", "ties", "net", "win rate"], rows
        ),
        "",
        f"Non-dominated frontier: {', '.join(frontier) if frontier else '-'}",
        "",
    ]


def _oracle_gap_section(aggregation: Aggregation) -> list[str]:
    rows = [
        [
            summary.strategy_id,
            _fmt(summary.normalized),
            _fmt(summary.mean_primary_gap),
            _fmt(summary.mean_gap),
            str(summary.cell_count),
        ]
        for summary in oracle_summaries(aggregation)
    ]
    return [
        "## oracle gap",
        "",
        "Normalized is strategy/oracle on the primary metric (1.0 matches the",
        "oracle); gaps are oracle minus strategy.",
        "",
        *_table(
            ["strategy", "normalized", "primary gap", "mean gap", "cells"], rows
        ),
        "",
    ]


def _failure_section(aggregation: Aggregation) -> list[str]:
    observations = analyze_failures(aggregation)
    counts: dict[FailureMode, int] = dict.fromkeys(FailureMode, 0)
    for observation in observations:
        counts[observation.mode] += 1
    summary = ", ".join(
        f"{mode.value}: {counts[mode]}" for mode in FailureMode
    )
    rows = [
        [
            observation.strategy_id,
            observation.benchmark_id,
            observation.mode.value,
            observation.metric,
            _fmt(observation.severity),
        ]
        for observation in observations[:_MAX_FAILURE_ROWS]
    ]
    lines = [
        "## failures",
        "",
        f"Counts by mode: {summary}.",
        "",
        *_table(
            ["strategy", "benchmark", "mode", "metric", "severity"], rows
        ),
        "",
    ]
    if len(observations) > _MAX_FAILURE_ROWS:
        extra = len(observations) - _MAX_FAILURE_ROWS
        lines.append(f"({extra} further observations omitted.)")
        lines.append("")
    return lines


def _stability_section(aggregation: Aggregation) -> list[str]:
    strategy_rows = [
        [
            report.strategy_id,
            _fmt(report.seed_variance),
            _fmt(report.budget_sensitivity),
        ]
        for report in stability_reports(aggregation)
    ]
    volatility_rows = [
        [volatility.benchmark_id, volatility.metric, _fmt(volatility.volatility)]
        for volatility in ranking_volatilities(aggregation)
    ]
    return [
        "## stability",
        "",
        "Seed variance and budget sensitivity are per strategy (lower is",
        "steadier); ranking volatility is per benchmark across budgets.",
        "",
        *_table(
            ["strategy", "seed variance", "budget sensitivity"], strategy_rows
        ),
        "",
        *_table(["benchmark", "metric", "ranking volatility"], volatility_rows),
        "",
    ]


def render_report(aggregation: Aggregation) -> str:
    """Render a full Phase 9 synthesis report from an aggregation.

    Args:
        aggregation: The aggregated cells to synthesise.

    Returns:
        A deterministic Markdown document.
    """
    sections = [
        "# Phase 9 report: cross-benchmark synthesis",
        "",
        "A synthesis of the Phase 2-8 experiment artifacts. It adds no new",
        "strategy, benchmark, or metric; it aggregates existing results and",
        "reports dominance, oracle gaps, failures, and stability. Every number is",
        "specific to these synthetic benchmarks, seeds, and budgets and is not a",
        "claim about real-world systems. `oracle` strategies are ceilings.",
        "",
        *_provenance(aggregation),
        *_profiles_section(aggregation),
        *_dominance_section(aggregation),
        *_oracle_gap_section(aggregation),
        *_failure_section(aggregation),
        *_stability_section(aggregation),
        "## limitations",
        "",
        "- Synthesis only reflects the benchmarks, strategies, seeds, and budgets",
        "  present in the artifacts; gaps in coverage are gaps in the conclusions.",
        "- Primary metrics differ by benchmark, so cross-benchmark numbers mix",
        "  metrics; comparisons are strongest within a benchmark.",
        "- Budgets are compared by numeric limit even though units differ",
        "  (items vs tokens) between benchmarks.",
        "- Dominance is restricted to shared cells; strategies on disjoint",
        "  benchmarks never compare and are all non-dominated.",
        "- `oracle` strategies are upper bounds, not deployable approaches.",
        "- Failure flags are mechanical threshold checks, not root-cause claims.",
        "",
    ]
    return "\n".join(sections)


def render_from_results(results: Sequence[ExperimentResult]) -> str:
    """Aggregate result artifacts and render the Phase 9 report."""
    return render_report(aggregate_results(results))
