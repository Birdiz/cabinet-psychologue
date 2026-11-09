from dataclasses import dataclass
from datetime import datetime
from typing import Any

import recurring_ical_events
from icalendar import Calendar

from cabinet.settings import PRACTICE_TZ


class FeedError(Exception):
    """The feed could not be read. The message never holds the URL or feed content."""


@dataclass(frozen=True, slots=True, order=True)
class Slot:
    start: datetime
    end: datetime


def parse_slots(raw: bytes, *, start: datetime, end: datetime) -> list[Slot]:
    """Return the slots between two instants, keeping only their start and end.

    This is the privacy boundary: nothing else from an event leaves this function.
    """
    try:
        calendar = Calendar.from_ical(raw)
        events = recurring_ical_events.of(calendar).between(start, end)
        slots = {slot for event in events if (slot := _to_slot(event)) is not None}
    except Exception:  # noqa: BLE001
        # Deliberately broad, and chained to nothing: parser errors can quote the
        # offending line, which may hold a patient name.
        raise FeedError("feed could not be parsed") from None
    return sorted(slots)


def _to_slot(event: Any) -> Slot | None:
    if str(event.get("STATUS", "")).upper() == "CANCELLED":
        return None
    start, end = event["DTSTART"].dt, event["DTEND"].dt
    # All-day events are dates, not datetimes: they do not describe a bookable slot.
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        return None
    slot = Slot(_in_practice_tz(start), _in_practice_tz(end))
    return slot if slot.start < slot.end else None


def _in_practice_tz(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=PRACTICE_TZ)
    return value.astimezone(PRACTICE_TZ)
