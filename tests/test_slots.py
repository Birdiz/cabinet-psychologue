from dataclasses import fields
from datetime import datetime

import pytest
from feeds import PATIENT_EVENT, calendar, event, raw_event

from cabinet.settings import PRACTICE_TZ
from cabinet.slots import FeedError, Slot, parse_slots

WINDOW_START = datetime(2026, 11, 9, 0, 0, tzinfo=PRACTICE_TZ)
WINDOW_END = datetime(2026, 11, 20, 0, 0, tzinfo=PRACTICE_TZ)


def parse(raw: bytes) -> list[Slot]:
    return parse_slots(raw, start=WINDOW_START, end=WINDOW_END)


def paris(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=PRACTICE_TZ)


def test_only_start_and_end_survive_a_patient_event() -> None:
    slots = parse(calendar(PATIENT_EVENT))

    assert slots == [Slot(paris(10, 14), paris(10, 14, 45))]
    assert {field.name for field in fields(Slot)} == {"start", "end"}
    assert "Dupont" not in repr(slots)


def test_recurrence_is_expanded_and_exceptions_removed() -> None:
    raw = calendar(
        event(
            "20261110T090000",
            "20261110T094500",
            "RRULE:FREQ=DAILY;COUNT=3",
            "EXDATE;TZID=Europe/Paris:20261111T090000",
        )
    )

    assert [slot.start for slot in parse(raw)] == [paris(10, 9), paris(12, 9)]


def test_recurring_slot_keeps_local_hour_across_clock_change() -> None:
    raw = calendar(
        event("20261020T100000", "20261020T104500", "RRULE:FREQ=WEEKLY;COUNT=2")
    )

    slots = parse_slots(
        raw,
        start=datetime(2026, 10, 19, tzinfo=PRACTICE_TZ),
        end=datetime(2026, 10, 30, tzinfo=PRACTICE_TZ),
    )

    assert [(slot.start.day, slot.start.hour) for slot in slots] == [(20, 10), (27, 10)]
    assert slots[0].start.utcoffset() != slots[1].start.utcoffset()


def test_all_day_event_is_ignored() -> None:
    raw = calendar(
        raw_event("DTSTART;VALUE=DATE:20261110", "DTEND;VALUE=DATE:20261111")
    )

    assert parse(raw) == []


def test_cancelled_event_is_ignored() -> None:
    assert (
        parse(calendar(event("20261110T090000", "20261110T094500", "STATUS:CANCELLED")))
        == []
    )


def test_utc_times_are_converted_to_practice_time() -> None:
    raw = calendar(raw_event("DTSTART:20261110T130000Z", "DTEND:20261110T134500Z"))

    assert parse(raw)[0].start.hour == 14


def test_duration_is_turned_into_an_end() -> None:
    raw = calendar(
        raw_event("DTSTART;TZID=Europe/Paris:20261110T090000", "DURATION:PT45M")
    )

    assert parse(raw) == [Slot(paris(10, 9), paris(10, 9, 45))]


def test_events_outside_the_window_are_dropped() -> None:
    assert parse(calendar(event("20261201T090000", "20261201T094500"))) == []


@pytest.mark.parametrize(
    "raw",
    [
        b"<html>Mme Dupont</html>",
        b"BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:Dupont\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n",
    ],
)
def test_unreadable_feed_fails_without_quoting_it(raw: bytes) -> None:
    with pytest.raises(FeedError) as caught:
        parse(raw)

    assert "Dupont" not in str(caught.value)
    assert caught.value.__cause__ is None
