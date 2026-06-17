"""Cross-benchmark synthesis (Phase 9).

Phase 9 adds no new strategy, benchmark, or metric. It reads the result artifacts
produced by the Phase 2-8 experiment suites and synthesises them: aggregation,
strategy profiles, dominance, oracle gaps, failure modes, and stability. Every
conclusion is mechanical and benchmark-specific; nothing here calls an external
service or uses an LLM. See ``docs/synthesis.md``.
"""

from __future__ import annotations
