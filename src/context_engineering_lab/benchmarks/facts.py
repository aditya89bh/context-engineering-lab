"""Fact-token markers for compression benchmarks.

A compression benchmark embeds *facts* directly in item content as recognizable
tokens, so scoring can check which facts survived compression by scanning the
compressed text — no side-channel state required. There are three kinds:

* required target facts, ``RF<n>`` (must survive to answer the task),
* optional target facts, ``TF<n>`` (relevant, but not strictly required),
* distractor facts, ``DF<n>`` (irrelevant; a good compressor discards them).

These markers are *ground truth*. Only an oracle compressor is permitted to read
them; deployable strategies must rely on position or the task query instead.
"""

from __future__ import annotations

import re

REQUIRED_PREFIX = "RF"
OPTIONAL_PREFIX = "TF"
DISTRACTOR_PREFIX = "DF"

_FACT_RE = re.compile(r"(?:RF|TF|DF)\d+")


def is_fact(token: str) -> bool:
    """Whether a token is any fact marker."""
    return _FACT_RE.fullmatch(token) is not None


def is_required_fact(token: str) -> bool:
    """Whether a token is a required target fact (``RF<n>``)."""
    return is_fact(token) and token.startswith(REQUIRED_PREFIX)


def is_target_fact(token: str) -> bool:
    """Whether a token is a target fact (required or optional)."""
    return is_fact(token) and token.startswith((REQUIRED_PREFIX, OPTIONAL_PREFIX))


def is_distractor_fact(token: str) -> bool:
    """Whether a token is a distractor fact (``DF<n>``)."""
    return is_fact(token) and token.startswith(DISTRACTOR_PREFIX)


def fact_tokens(text: str) -> list[str]:
    """Return all fact tokens in ``text``, in order of appearance."""
    return [token for token in text.split() if is_fact(token)]


def required_facts(text: str) -> set[str]:
    """Return the set of required target facts in ``text``."""
    return {token for token in fact_tokens(text) if is_required_fact(token)}


def target_facts(text: str) -> set[str]:
    """Return the set of target facts (required or optional) in ``text``."""
    return {token for token in fact_tokens(text) if is_target_fact(token)}


def distractor_facts(text: str) -> set[str]:
    """Return the set of distractor facts in ``text``."""
    return {token for token in fact_tokens(text) if is_distractor_fact(token)}
