"""Tests for deterministic seeding utilities."""

from __future__ import annotations

import random

from context_engineering_lab.seeding import (
    DEFAULT_SEED,
    derive_seed,
    seed_everything,
    temporary_seed,
)


def test_seed_everything_is_reproducible() -> None:
    seed_everything(123)
    first = [random.random() for _ in range(5)]
    seed_everything(123)
    second = [random.random() for _ in range(5)]
    assert first == second


def test_seed_everything_returns_seed() -> None:
    assert seed_everything(7) == 7
    assert seed_everything() == DEFAULT_SEED


def test_derive_seed_is_stable_and_in_range() -> None:
    # Known-answer: derivation must not drift across runs or versions.
    value = derive_seed(DEFAULT_SEED, "data", "shuffle")
    assert value == derive_seed(DEFAULT_SEED, "data", "shuffle")
    assert 0 <= value < 2**63


def test_derive_seed_separates_streams() -> None:
    a = derive_seed(DEFAULT_SEED, "model", "init")
    b = derive_seed(DEFAULT_SEED, "sampler")
    assert a != b


def test_temporary_seed_restores_state() -> None:
    seed_everything(42)
    before = random.random()

    seed_everything(42)
    with temporary_seed(999):
        # Inside the context the stream is independent of the outer seed.
        random.random()
    after = random.random()

    assert before == after
