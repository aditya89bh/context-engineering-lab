"""Tests for the compression metric functions."""

from __future__ import annotations

import pytest

from context_engineering_lab.core.compression_metrics import (
    answer_support_after_compression,
    budget_utilization,
    compression_ratio,
    distractor_retention,
    information_retention,
)


def test_compression_ratio() -> None:
    assert compression_ratio(10, 5) == 0.5
    assert compression_ratio(10, 10) == 1.0
    assert compression_ratio(10, 0) == 0.0


def test_compression_ratio_undefined() -> None:
    with pytest.raises(ValueError):
        compression_ratio(0, 0)
    with pytest.raises(ValueError):
        compression_ratio(10, -1)


def test_information_retention() -> None:
    assert information_retention({"RF0", "TF0"}, {"RF0"}) == 0.5
    assert information_retention({"RF0"}, {"RF0", "DF1"}) == 1.0
    assert information_retention({"RF0"}, set()) == 0.0


def test_information_retention_undefined() -> None:
    with pytest.raises(ValueError):
        information_retention(set(), {"RF0"})


def test_answer_support_after_compression() -> None:
    required = {"RF0", "RF1"}
    assert answer_support_after_compression(required, {"RF0", "RF1", "TF0"}) == 1.0
    assert answer_support_after_compression(required, {"RF0"}) == 0.0


def test_answer_support_undefined() -> None:
    with pytest.raises(ValueError):
        answer_support_after_compression(set(), {"RF0"})


def test_distractor_retention() -> None:
    assert distractor_retention({"DF0", "DF1"}, {"DF0"}) == 0.5
    assert distractor_retention({"DF0"}, {"RF0"}) == 0.0


def test_distractor_retention_undefined() -> None:
    with pytest.raises(ValueError):
        distractor_retention(set(), {"DF0"})


def test_budget_utilization() -> None:
    assert budget_utilization(4, 8) == 0.5
    assert budget_utilization(12, 8) == 1.5  # over-budget baseline


def test_budget_utilization_undefined() -> None:
    with pytest.raises(ValueError):
        budget_utilization(4, 0)
