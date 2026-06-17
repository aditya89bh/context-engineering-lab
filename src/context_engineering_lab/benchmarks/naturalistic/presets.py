"""Named presets of the naturalistic benchmark families.

Six presets across five families, each declaring an id, version, construct,
parameters, budget sweep, and expected failure modes. Kept small on purpose —
one or two presets per family is enough to probe the scenario.
"""

from __future__ import annotations

from context_engineering_lab.benchmarks.naturalistic.email import (
    EmailThreadBenchmark,
)
from context_engineering_lab.benchmarks.naturalistic.meeting import (
    MeetingNotesBenchmark,
)
from context_engineering_lab.benchmarks.naturalistic.memory_log import (
    MemoryLogBenchmark,
)
from context_engineering_lab.benchmarks.naturalistic.records import (
    NaturalisticBenchmark,
    NaturalisticConfig,
)
from context_engineering_lab.benchmarks.naturalistic.revision import (
    DocumentRevisionBenchmark,
)
from context_engineering_lab.benchmarks.naturalistic.support import (
    SupportTicketBenchmark,
)


def email_old_signal() -> EmailThreadBenchmark:
    """The answer is an old message under a pile of recent chatter."""
    return EmailThreadBenchmark(
        NaturalisticConfig(
            benchmark_id="email-old-signal",
            version="1.0",
            construct="recover an older relevant email under recent distractors",
            expected_failure_modes=(
                "recency and recent windows chase the latest chatter",
                "a recency window drops the older relevant message",
            ),
        ),
        num_distractors=7,
        num_conflicting=2,
        num_harmful=1,
    )


def email_conflict_heavy() -> EmailThreadBenchmark:
    """Several on-topic-but-outdated messages conflict with the answer."""
    return EmailThreadBenchmark(
        NaturalisticConfig(
            benchmark_id="email-conflict-heavy",
            version="1.0",
            construct="separate the answer from many on-topic conflicting messages",
            expected_failure_modes=(
                "keyword overlap keeps conflicting messages that share the terms",
                "the conflicting messages read as unimportant, not off-topic",
            ),
        ),
        num_distractors=4,
        num_conflicting=5,
        num_harmful=1,
    )


def meeting_action_items() -> MeetingNotesBenchmark:
    """The current decision and its action item are buried in notes."""
    return MeetingNotesBenchmark(
        NaturalisticConfig(
            benchmark_id="meeting-action-items",
            version="1.0",
            construct="find the current decision and action among superseded notes",
            expected_failure_modes=(
                "keyword overlap keeps the superseded decision",
                "updates and asides crowd a tight budget",
            ),
        ),
        num_updates=5,
        num_superseded=2,
        num_irrelevant=4,
    )


def support_stale_fix() -> SupportTicketBenchmark:
    """The working fix competes with a stale fix and a harmful one."""
    return SupportTicketBenchmark(
        NaturalisticConfig(
            benchmark_id="support-stale-fix",
            version="1.0",
            construct="pick the working fix over stale, harmful, and noisy incidents",
            expected_failure_modes=(
                "repeated symptoms recur often and crowd the budget",
                "the harmful fix is on-topic and competes with the working one",
            ),
        ),
        num_similar=3,
        symptoms_per_incident=2,
    )


def revision_current_truth() -> DocumentRevisionBenchmark:
    """The current revision's facts compete with old and conflicting ones."""
    return DocumentRevisionBenchmark(
        NaturalisticConfig(
            benchmark_id="revision-current-truth",
            version="1.0",
            construct="track the current document facts, not superseded revisions",
            expected_failure_modes=(
                "keyword overlap keeps deprecated and conflicting old facts",
                "the old conflicting fact is on-topic and reads plausibly",
            ),
        ),
        num_current=2,
        num_old=3,
        num_conflicting=2,
    )


def memory_log_noisy() -> MemoryLogBenchmark:
    """A memory log dense with stale, harmful, and neutral entries."""
    return MemoryLogBenchmark(
        NaturalisticConfig(
            benchmark_id="memory-log-noisy",
            version="1.0",
            construct="keep useful memories while dropping stale and harmful ones",
            expected_failure_modes=(
                "recency keeps recent harmful memories",
                "neutral entries crowd the budget",
            ),
        ),
        num_useful=3,
        num_stale=4,
        num_harmful=3,
        num_neutral=8,
    )


def all_naturalistic_presets() -> tuple[NaturalisticBenchmark, ...]:
    """Return all six naturalistic presets in a stable order."""
    return (
        email_old_signal(),
        email_conflict_heavy(),
        meeting_action_items(),
        support_stale_fix(),
        revision_current_truth(),
        memory_log_noisy(),
    )
