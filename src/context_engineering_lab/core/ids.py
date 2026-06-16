"""Typed identifier wrappers.

Identifiers are thin, immutable wrappers around a non-empty string. Using
distinct types (rather than bare ``str``) prevents a whole class of bugs where,
say, a :class:`BenchmarkId` is passed where a :class:`StrategyId` is expected;
mypy rejects the mix-up and the wrappers compare unequal at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Identifier:
    """Base class for string-valued identifiers.

    Not meant to be used directly; subclass it to create a distinct identifier
    type. The wrapped value must be a non-empty, non-whitespace string.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError(
                f"{type(self).__name__} value must be a non-empty string"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ItemId(Identifier):
    """Identifies a single information item."""


@dataclass(frozen=True, slots=True)
class StrategyId(Identifier):
    """Identifies a context strategy."""


@dataclass(frozen=True, slots=True)
class BenchmarkId(Identifier):
    """Identifies a benchmark."""


@dataclass(frozen=True, slots=True)
class ExperimentId(Identifier):
    """Identifies an experiment configuration."""


@dataclass(frozen=True, slots=True)
class RunId(Identifier):
    """Identifies a single run, derived deterministically from its config.

    See :mod:`context_engineering_lab.core.metadata` for how run ids are
    computed so that the same configuration always yields the same id.
    """
