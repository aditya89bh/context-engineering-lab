"""Command-line interface.

A deliberately small CLI exposing three commands:

* ``context-lab list`` — show the registered strategies and benchmarks.
* ``context-lab run-smoke`` — run the harness smoke experiment and write a JSON
  result artifact.
* ``context-lab run-phase2`` — run the Phase 2 selection experiments and write
  per-experiment JSON artifacts plus a Markdown summary.
* ``context-lab run-phase3`` — run the Phase 3 compression experiments and write
  per-experiment JSON artifacts plus a Markdown summary.
* ``context-lab run-phase4`` — run the Phase 4 temporal experiments and write
  per-experiment JSON artifacts plus a Markdown summary.
* ``context-lab run-phase5`` — run the Phase 5 retention experiments and write
  per-experiment JSON artifacts plus a Markdown summary.
* ``context-lab run-phase6`` — run the Phase 6 attention experiments and write
  per-experiment JSON artifacts plus a Markdown summary.
* ``context-lab run-phase7`` — run the Phase 7 interaction experiments and write
  per-experiment JSON artifacts plus a Markdown summary.
* ``context-lab run-phase8`` — run the Phase 8 naturalistic experiments and write
  per-experiment JSON artifacts plus a Markdown summary.
* ``context-lab run-phase9`` — re-run the Phase 2-8 suites and write their JSON
  artifacts plus a cross-benchmark synthesis report.

It is a skeleton: it proves the lab can be driven from the command line and
produce reproducible artifacts, nothing more.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from pathlib import Path

from context_engineering_lab import __version__
from context_engineering_lab.catalog import (
    build_benchmark_registry,
    build_strategy_registry,
)
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.results import ExperimentResult
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.experiments.phase2 import phase2_experiments
from context_engineering_lab.experiments.phase3 import phase3_experiments
from context_engineering_lab.experiments.phase4 import phase4_experiments
from context_engineering_lab.experiments.phase5 import phase5_experiments
from context_engineering_lab.experiments.phase6 import phase6_experiments
from context_engineering_lab.experiments.phase7 import phase7_experiments
from context_engineering_lab.experiments.phase8 import phase8_experiments
from context_engineering_lab.experiments.phase9 import all_phase_experiments
from context_engineering_lab.reporting.persistence import write_result
from context_engineering_lab.reporting.phase2_report import (
    render_report as render_phase2_report,
)
from context_engineering_lab.reporting.phase3_report import (
    render_report as render_phase3_report,
)
from context_engineering_lab.reporting.phase4_report import (
    render_report as render_phase4_report,
)
from context_engineering_lab.reporting.phase5_report import (
    render_report as render_phase5_report,
)
from context_engineering_lab.reporting.phase6_report import (
    render_report as render_phase6_report,
)
from context_engineering_lab.reporting.phase7_report import (
    render_report as render_phase7_report,
)
from context_engineering_lab.reporting.phase8_report import (
    render_report as render_phase8_report,
)
from context_engineering_lab.reporting.phase9_report import (
    render_from_results as render_phase9_report,
)
from context_engineering_lab.seeding import DEFAULT_SEED

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT = "artifacts/smoke-result.json"
_DEFAULT_PHASE2_OUTPUT = "artifacts/phase2"
_DEFAULT_PHASE3_OUTPUT = "artifacts/phase3"
_DEFAULT_PHASE4_OUTPUT = "artifacts/phase4"
_DEFAULT_PHASE5_OUTPUT = "artifacts/phase5"
_DEFAULT_PHASE6_OUTPUT = "artifacts/phase6"
_DEFAULT_PHASE7_OUTPUT = "artifacts/phase7"
_DEFAULT_PHASE8_OUTPUT = "artifacts/phase8"
_DEFAULT_PHASE9_OUTPUT = "artifacts/phase9"


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s %(name)s %(message)s",
    )


def _run_list() -> int:
    strategies = build_strategy_registry()
    benchmarks = build_benchmark_registry()
    print("strategies:")
    for name in strategies.names():
        print(f"  {name}")
    print("benchmarks:")
    for name in benchmarks.names():
        benchmark = benchmarks.get(name)
        print(f"  {name} (v{benchmark.version})")
    return 0


def _run_smoke(output: str, seeds: tuple[int, ...]) -> int:
    strategies = build_strategy_registry()
    benchmarks = build_benchmark_registry()
    experiment = Experiment(
        experiment_id=ExperimentId("harness-smoke"),
        benchmark=benchmarks.get("harness-smoke"),
        strategies=(strategies.get("recency"),),
        seeds=seeds,
    )
    result = ExperimentRunner().run(experiment)
    path = write_result(result, output)
    print(f"wrote {path} (run_id={result.metadata.run_id.value})")
    return 0


def _run_suite(
    output_dir: str,
    experiments: dict[str, Experiment],
    render: Callable[[dict[str, ExperimentResult]], str],
) -> int:
    runner = ExperimentRunner()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    results: dict[str, ExperimentResult] = {}
    for name, experiment in experiments.items():
        result = runner.run(experiment)
        results[name] = result
        path = write_result(result, destination / f"{name}.json")
        print(f"wrote {path} (run_id={result.metadata.run_id.value})")
    summary_path = destination / "summary.md"
    summary_path.write_text(render(results), encoding="utf-8")
    print(f"wrote {summary_path}")
    return 0


def _run_phase9(output_dir: str) -> int:
    runner = ExperimentRunner()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    results: list[ExperimentResult] = []
    for name, experiment in all_phase_experiments().items():
        result = runner.run(experiment)
        results.append(result)
        path = write_result(result, destination / f"{name}.json")
        print(f"wrote {path} (run_id={result.metadata.run_id.value})")
    summary_path = destination / "synthesis.md"
    summary_path.write_text(render_phase9_report(results), encoding="utf-8")
    print(f"wrote {summary_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="context-lab",
        description="Run context-engineering experiments.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="emit INFO-level structured logs",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list registered strategies and benchmarks")
    run = subparsers.add_parser("run-smoke", help="run the harness smoke experiment")
    run.add_argument(
        "--output",
        default=_DEFAULT_OUTPUT,
        help=f"path for the JSON result artifact (default: {_DEFAULT_OUTPUT})",
    )
    run.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[DEFAULT_SEED],
        help="one or more integer seeds to run over",
    )
    phase2 = subparsers.add_parser(
        "run-phase2", help="run the Phase 2 selection experiment suite"
    )
    phase2.add_argument(
        "--output",
        default=_DEFAULT_PHASE2_OUTPUT,
        help=(
            "directory for JSON artifacts and the Markdown summary "
            f"(default: {_DEFAULT_PHASE2_OUTPUT})"
        ),
    )
    phase3 = subparsers.add_parser(
        "run-phase3", help="run the Phase 3 compression experiment suite"
    )
    phase3.add_argument(
        "--output",
        default=_DEFAULT_PHASE3_OUTPUT,
        help=(
            "directory for JSON artifacts and the Markdown summary "
            f"(default: {_DEFAULT_PHASE3_OUTPUT})"
        ),
    )
    phase4 = subparsers.add_parser(
        "run-phase4", help="run the Phase 4 temporal experiment suite"
    )
    phase4.add_argument(
        "--output",
        default=_DEFAULT_PHASE4_OUTPUT,
        help=(
            "directory for JSON artifacts and the Markdown summary "
            f"(default: {_DEFAULT_PHASE4_OUTPUT})"
        ),
    )
    phase5 = subparsers.add_parser(
        "run-phase5", help="run the Phase 5 retention experiment suite"
    )
    phase5.add_argument(
        "--output",
        default=_DEFAULT_PHASE5_OUTPUT,
        help=(
            "directory for JSON artifacts and the Markdown summary "
            f"(default: {_DEFAULT_PHASE5_OUTPUT})"
        ),
    )
    phase6 = subparsers.add_parser(
        "run-phase6", help="run the Phase 6 attention experiment suite"
    )
    phase6.add_argument(
        "--output",
        default=_DEFAULT_PHASE6_OUTPUT,
        help=(
            "directory for JSON artifacts and the Markdown summary "
            f"(default: {_DEFAULT_PHASE6_OUTPUT})"
        ),
    )
    phase7 = subparsers.add_parser(
        "run-phase7", help="run the Phase 7 interaction experiment suite"
    )
    phase7.add_argument(
        "--output",
        default=_DEFAULT_PHASE7_OUTPUT,
        help=(
            "directory for JSON artifacts and the Markdown summary "
            f"(default: {_DEFAULT_PHASE7_OUTPUT})"
        ),
    )
    phase8 = subparsers.add_parser(
        "run-phase8", help="run the Phase 8 naturalistic experiment suite"
    )
    phase8.add_argument(
        "--output",
        default=_DEFAULT_PHASE8_OUTPUT,
        help=(
            "directory for JSON artifacts and the Markdown summary "
            f"(default: {_DEFAULT_PHASE8_OUTPUT})"
        ),
    )
    phase9 = subparsers.add_parser(
        "run-phase9",
        help="run the Phase 2-8 suites and write a cross-benchmark synthesis",
    )
    phase9.add_argument(
        "--output",
        default=_DEFAULT_PHASE9_OUTPUT,
        help=(
            "directory for JSON artifacts and the synthesis report "
            f"(default: {_DEFAULT_PHASE9_OUTPUT})"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``context-lab`` command.

    Args:
        argv: Optional argument vector; defaults to ``sys.argv`` when ``None``.

    Returns:
        A process exit code.
    """
    args = build_parser().parse_args(argv)
    _configure_logging(bool(args.verbose))
    if args.command == "list":
        return _run_list()
    if args.command == "run-smoke":
        return _run_smoke(str(args.output), tuple(int(s) for s in args.seeds))
    if args.command == "run-phase2":
        return _run_suite(
            str(args.output), phase2_experiments(), render_phase2_report
        )
    if args.command == "run-phase3":
        return _run_suite(
            str(args.output), phase3_experiments(), render_phase3_report
        )
    if args.command == "run-phase4":
        return _run_suite(
            str(args.output), phase4_experiments(), render_phase4_report
        )
    if args.command == "run-phase5":
        return _run_suite(
            str(args.output), phase5_experiments(), render_phase5_report
        )
    if args.command == "run-phase6":
        return _run_suite(
            str(args.output), phase6_experiments(), render_phase6_report
        )
    if args.command == "run-phase7":
        return _run_suite(
            str(args.output), phase7_experiments(), render_phase7_report
        )
    if args.command == "run-phase8":
        return _run_suite(
            str(args.output), phase8_experiments(), render_phase8_report
        )
    if args.command == "run-phase9":
        return _run_phase9(str(args.output))
    return 2  # pragma: no cover - argparse enforces a valid command


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
