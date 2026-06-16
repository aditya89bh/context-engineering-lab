"""Core abstractions for the lab.

This subpackage holds the substrate-independent primitives every experiment is
built from: items, budgets, contexts, tasks, the strategy and benchmark
interfaces, result models, deterministic metadata, and the experiment runner.

Nothing here makes a research claim; it is the infrastructure that later phases
use to *make* claims reproducibly.
"""

from __future__ import annotations
