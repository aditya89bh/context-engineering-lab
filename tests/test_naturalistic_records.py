"""Tests for the naturalistic record helpers."""

from __future__ import annotations

from context_engineering_lab.benchmarks.naturalistic.records import (
    CONFLICTING_KEY,
    CURRENT_KEY,
    HARMFUL_KEY,
    REQUIRED_KEY,
    SUPERSEDED_KEY,
    MeetingNoteRecord,
    MemoryRecord,
    MessageLikeRecord,
    RevisionRecord,
    TicketRecord,
    naturalistic_signal,
    query_fragment,
)
from context_engineering_lab.core.attention import SOURCE_QUALITY_KEY
from context_engineering_lab.core.item import Item
from context_engineering_lab.core.retention import FREQUENCY_KEY
from context_engineering_lab.core.temporal import SALIENCE_KEY
from context_engineering_lab.strategies.oracle import ORACLE_RELEVANCE_KEY


def test_message_record_converts_to_item() -> None:
    record = MessageLikeRecord(
        record_id="m1",
        kind="relevant",
        timestamp=5.0,
        salience=0.9,
        frequency=6,
        relevant=True,
        current=True,
        required=True,
        sender="amy",
        subject="budget",
        body="the answer",
    )
    item = record.to_item()
    assert isinstance(item, Item)
    assert str(item.id) == "m1"
    assert "amy" in item.content and "the answer" in item.content
    assert item.timestamp == 5.0
    assert item.length == 1
    assert item.metadata[ORACLE_RELEVANCE_KEY] is True
    assert item.metadata[CURRENT_KEY] is True
    assert item.metadata[REQUIRED_KEY] is True
    assert item.metadata[SALIENCE_KEY] == 0.9
    assert item.metadata[FREQUENCY_KEY] == 6


def test_records_set_their_ground_truth_flags() -> None:
    note = MeetingNoteRecord(
        record_id="n1",
        kind="superseded",
        timestamp=1.0,
        salience=0.4,
        frequency=2,
        superseded=True,
        conflicting=True,
        label="decision",
        body="reversed",
    )
    meta = note.to_item().metadata
    assert meta[SUPERSEDED_KEY] is True
    assert meta[CONFLICTING_KEY] is True
    assert meta[ORACLE_RELEVANCE_KEY] is False


def test_ticket_record_includes_source_quality_when_set() -> None:
    ticket = TicketRecord(
        record_id="t1",
        kind="harmful",
        timestamp=3.0,
        salience=0.1,
        frequency=1,
        harmful=True,
        source="INC-bad",
        source_quality=0.2,
        incident="INC-bad",
        field_name="resolution",
        body="disable checks",
    )
    item = ticket.to_item()
    assert item.source == "INC-bad"
    assert item.metadata[SOURCE_QUALITY_KEY] == 0.2
    assert item.metadata[HARMFUL_KEY] is True


def test_source_quality_absent_when_unset() -> None:
    memory = MemoryRecord(
        record_id="x1",
        kind="distractor",
        timestamp=2.0,
        salience=0.1,
        frequency=0,
        body="neutral",
    )
    assert SOURCE_QUALITY_KEY not in memory.to_item().metadata


def test_revision_record_tags_revision_number() -> None:
    rev = RevisionRecord(
        record_id="r1",
        kind="current",
        timestamp=9.0,
        salience=0.9,
        frequency=5,
        relevant=True,
        current=True,
        revision=3,
        body="retry is five",
    )
    assert "rev3" in rev.to_item().content


def test_naturalistic_signal_is_deterministic_and_in_range() -> None:
    import random

    sal1, freq1 = naturalistic_signal("relevant", random.Random(7))
    sal2, freq2 = naturalistic_signal("relevant", random.Random(7))
    assert (sal1, freq1) == (sal2, freq2)
    assert 0.75 <= sal1 <= 1.0
    assert 4 <= freq1 <= 8


def test_query_fragment_levels() -> None:
    import random

    query = "alpha beta gamma delta"
    assert query_fragment(query, "full", random.Random(1)) == query
    assert query_fragment(query, "none", random.Random(1)) == ""
    partial = query_fragment(query, "partial", random.Random(1))
    assert partial and partial != query
    assert all(term in query.split() for term in partial.split())
