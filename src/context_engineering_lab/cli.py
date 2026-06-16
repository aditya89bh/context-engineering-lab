"""Command-line interface.

A deliberately small CLI exposing two commands:

* ``context-lab list`` — show the registered strategies and benchmarks.
* ``context-lab run-smoke`` — run the harness smoke experiment and write a JSON
  result artifact.

It is a skeleton: it proves the lab can be driven from the command line and
produce a reproducible artifact, nothing more.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from context_engineering_lab import __version__
from context_engineering_lab.catalog import (
    build_benchmark_registry,
    build_strategy_registry,
)
from context_engineering_lab.core.experiment import Experiment
from context_engineering_lab.core.ids import ExperimentId
from context_engineering_lab.core.runner import ExperimentRunner
from context_engineering_lab.reporting.persistence import write_result
from context_engineering_lab.seeding import DEFAULT_SEED

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT = "artifacts/smoke-result.json"


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
    return 2  # pragma: no cover - argparse enforces a valid command


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
