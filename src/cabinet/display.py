"""French rendering of dates. Hand-written so the page does not depend on OS locales."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from itertools import groupby

from cabinet.agenda import HORIZON
from cabinet.settings import PRACTICE_TZ
from cabinet.slots import Slot

_WEEKDAYS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche")
_MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


@dataclass(frozen=True, slots=True)
class SlotView:
    label: str
    start_iso: str


@dataclass(frozen=True, slots=True)
class DayView:
    label: str
    iso: str
    slots: tuple[SlotView, ...]


def format_time(value: datetime) -> str:
    local = value.astimezone(PRACTICE_TZ)
    return f"{local.hour}h{local.minute:02d}"


def format_day(value: date) -> str:
    day = "1er" if value.day == 1 else str(value.day)
    return f"{_WEEKDAYS[value.weekday()]} {day} {_MONTHS[value.month - 1]}"


def week_days(slots: list[Slot], now: datetime) -> list[DayView]:
    """One row per day of the horizon, or nothing at all when no slot is free.

    Today and the day the horizon ends on are only partly covered, so "closed" could
    be wrong about them: they appear only when they hold a slot.
    """
    if not slots:
        return []
    by_day = {
        day: tuple(day_slots)
        for day, day_slots in groupby(slots, key=lambda slot: slot.start.date())
    }
    first = now.astimezone(PRACTICE_TZ).date()
    last = (now + HORIZON).astimezone(PRACTICE_TZ).date()
    dates = (first + timedelta(days=n) for n in range((last - first).days + 1))
    return [
        _day_view(day, by_day.get(day, ()))
        for day in dates
        if day in by_day or first < day < last
    ]


def _day_view(day: date, slots: tuple[Slot, ...]) -> DayView:
    return DayView(
        label=format_day(day),
        iso=day.isoformat(),
        slots=tuple(
            SlotView(
                label=f"{format_time(slot.start)} – {format_time(slot.end)}",
                start_iso=slot.start.isoformat(),
            )
            for slot in slots
        ),
    )
