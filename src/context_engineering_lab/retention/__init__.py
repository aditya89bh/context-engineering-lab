"""Deterministic retention (forgetting) policies.

Phase 5 policies decide which items survive a memory budget without any external
calls or LLM. They span a retain-all reference, single-signal policies (recency,
frequency, salience), a hybrid blend, and an oracle ceiling. See
``docs/retention-benchmarks.md``.
"""

from __future__ import annotations

from context_engineering_lab.core.retention import RetentionPolicy
from context_engineering_lab.retention.frequency import FrequencyRetentionPolicy
from context_engineering_lab.retention.hybrid import HybridRetentionPolicy
from context_engineering_lab.retention.oracle import OracleRetentionPolicy
from context_engineering_lab.retention.recency import RecencyRetentionPolicy
from context_engineering_lab.retention.retain_all import RetainAllPolicy
from context_engineering_lab.retention.salience import SalienceRetentionPolicy


def default_policies() -> tuple[RetentionPolicy, ...]:
    """Return the built-in retention policies in a stable order.

    Spans a retain-all reference, three single-signal policies (recency,
    frequency, salience), a hybrid blend, and the oracle ceiling (which is
    **not deployable**).
    """
    return (
        RetainAllPolicy(),
        RecencyRetentionPolicy(),
        FrequencyRetentionPolicy(),
        SalienceRetentionPolicy(),
        HybridRetentionPolicy(),
        OracleRetentionPolicy(),
    )


__all__ = [
    "FrequencyRetentionPolicy",
    "HybridRetentionPolicy",
    "OracleRetentionPolicy",
    "RecencyRetentionPolicy",
    "RetainAllPolicy",
    "SalienceRetentionPolicy",
    "default_policies",
]
