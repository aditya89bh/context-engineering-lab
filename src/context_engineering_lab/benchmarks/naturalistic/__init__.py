"""Naturalistic context benchmarks (Phase 8).

Deterministic, fully synthetic benchmarks shaped like realistic working
information — email threads, meeting notes, support tickets, document revisions,
and memory logs. Nothing here ingests real or private data, calls an external
service, or uses an LLM; every case is generated from a seed. See
``docs/naturalistic-benchmarks.md``.
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
from context_engineering_lab.benchmarks.naturalistic.presets import (
    all_naturalistic_presets,
)
from context_engineering_lab.benchmarks.naturalistic.revision import (
    DocumentRevisionBenchmark,
)
from context_engineering_lab.benchmarks.naturalistic.support import (
    SupportTicketBenchmark,
)

__all__ = [
    "DocumentRevisionBenchmark",
    "EmailThreadBenchmark",
    "MeetingNotesBenchmark",
    "MemoryLogBenchmark",
    "SupportTicketBenchmark",
    "all_naturalistic_presets",
]
