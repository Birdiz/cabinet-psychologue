import asyncio
from datetime import timedelta

from conftest import FakeClock
from feeds import calendar, event

from cabinet.agenda import Agenda
from cabinet.slots import FeedError

FEED = calendar(event("20261110T140000", "20261110T144500"))


def make_agenda(clock: FakeClock, *results: bytes | FeedError) -> Agenda:
    remaining = list(results)

    async def fetch() -> bytes:
        result = remaining.pop(0)
        if isinstance(result, FeedError):
            raise result
        return result

    return Agenda(fetch, stale_after=timedelta(hours=1), clock=clock)


def starts(agenda: Agenda) -> list[int] | None:
    slots = agenda.upcoming()
    return None if slots is None else [slot.start.hour for slot in slots]


def test_nothing_is_shown_before_the_first_success(clock: FakeClock) -> None:
    agenda = make_agenda(clock, FeedError("down"))

    asyncio.run(agenda.refresh())

    assert agenda.upcoming() is None
    assert not agenda.is_fresh


def test_failed_refresh_keeps_the_last_slots(clock: FakeClock) -> None:
    agenda = make_agenda(clock, FEED, FeedError("down"))

    asyncio.run(agenda.refresh())
    clock.now += timedelta(minutes=30)
    asyncio.run(agenda.refresh())

    assert starts(agenda) == [14]


def test_slots_are_hidden_once_stale(clock: FakeClock) -> None:
    agenda = make_agenda(clock, FEED)

    asyncio.run(agenda.refresh())
    clock.now += timedelta(hours=1, seconds=1)

    assert agenda.upcoming() is None
    assert not agenda.is_fresh


def test_slot_disappears_once_started(clock: FakeClock) -> None:
    agenda = make_agenda(clock, FEED, FEED)

    asyncio.run(agenda.refresh())
    clock.now += timedelta(days=1, hours=4, minutes=30)
    asyncio.run(agenda.refresh())

    assert starts(agenda) == []


def test_slots_past_seven_days_are_hidden(clock: FakeClock) -> None:
    agenda = make_agenda(clock, calendar(event("20261116T100100", "20261116T104500")))

    asyncio.run(agenda.refresh())

    assert starts(agenda) == []
