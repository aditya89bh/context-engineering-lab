"""Compression metric functions.

Pure implementations of the compression metrics defined formally in
``docs/metrics.md``. They operate on integer lengths and on sets of *fact tokens*
(ground-truth markers a compression benchmark embeds in item content), and make
no research claims on their own.

Like the selection metrics, each function raises ``ValueError`` for the cases its
formal definition leaves undefined, so callers must decide how to handle those
rather than silently receiving a misleading value.
"""

from __future__ import annotations

from collections.abc import Set as AbstractSet


def compression_ratio(original_length: int, compressed_length: int) -> float:
    """Compressed size as a fraction of the original: ``L_c / L_o``.

    Lower is more aggressive compression; ``1.0`` means no reduction.

    Args:
        original_length: Length of the original content (``L_o``), in tokens.
        compressed_length: Length of the compressed content (``L_c``), in tokens.

    Returns:
        The ratio ``L_c / L_o`` (``>= 0``; may exceed 1 only if a compressor
        somehow grew the content, which deployed compressors never do).

    Raises:
        ValueError: If ``original_length <= 0`` (the ratio is undefined) or
            ``compressed_length < 0``.
    """
    if original_length <= 0:
        raise ValueError("compression_ratio is undefined for non-positive original")
    if compressed_length < 0:
        raise ValueError("compressed_length cannot be negative")
    return compressed_length / original_length


def information_retention(
    target_facts: AbstractSet[str],
    retained_facts: AbstractSet[str],
) -> float:
    """Fraction of target facts surviving compression: ``|T ∩ K| / |T|``.

    Args:
        target_facts: Ground-truth target fact tokens in the original (``T``).
        retained_facts: Fact tokens present after compression (``K``).

    Returns:
        Retention in ``[0, 1]``.

    Raises:
        ValueError: If ``target_facts`` is empty (retention is undefined).
    """
    if not target_facts:
        raise ValueError("information_retention is undefined with no target facts")
    return len(target_facts & retained_facts) / len(target_facts)


def answer_support_after_compression(
    required_facts: AbstractSet[str],
    retained_facts: AbstractSet[str],
) -> float:
    """Whether every required fact survived: ``1`` if ``R ⊆ K`` else ``0``.

    Args:
        required_facts: The minimal fact tokens needed to answer (``R``).
        retained_facts: Fact tokens present after compression (``K``).

    Returns:
        ``1.0`` if all required facts were retained, else ``0.0``.

    Raises:
        ValueError: If ``required_facts`` is empty (support is undefined).
    """
    if not required_facts:
        raise ValueError("answer_support_after_compression needs required facts")
    return 1.0 if required_facts <= retained_facts else 0.0


def distractor_retention(
    distractor_facts: AbstractSet[str],
    retained_facts: AbstractSet[str],
) -> float:
    """Fraction of distractor facts surviving compression: ``|D ∩ K| / |D|``.

    Lower is better: a good compressor discards distractors.

    Args:
        distractor_facts: Ground-truth distractor fact tokens (``D``).
        retained_facts: Fact tokens present after compression (``K``).

    Returns:
        Distractor retention in ``[0, 1]``.

    Raises:
        ValueError: If ``distractor_facts`` is empty (the rate is undefined).
    """
    if not distractor_facts:
        raise ValueError("distractor_retention is undefined with no distractors")
    return len(distractor_facts & retained_facts) / len(distractor_facts)


def budget_utilization(used_cost: int, budget_limit: int) -> float:
    """Fraction of the budget consumed: ``used / limit``.

    May exceed ``1.0`` for a strategy that does not honor the budget (e.g. a
    no-compression baseline).

    Args:
        used_cost: Total cost consumed by the produced context.
        budget_limit: The budget limit.

    Returns:
        The utilization ratio.

    Raises:
        ValueError: If ``budget_limit <= 0``.
    """
    if budget_limit <= 0:
        raise ValueError("budget_utilization is undefined for non-positive budget")
    return used_cost / budget_limit
