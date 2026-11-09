import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from cabinet.slots import FeedError, Slot, parse_slots

logger = logging.getLogger(__name__)

HORIZON = timedelta(days=7)

Clock = Callable[[], datetime]
Fetch = Callable[[], Awaitable[bytes]]


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class _Snapshot:
    slots: tuple[Slot, ...]
    fetched_at: datetime


class Agenda:
    """Holds the latest slots in memory and knows whether they can still be trusted."""

    def __init__(
        self, fetch: Fetch, *, stale_after: timedelta, clock: Clock = utc_now
    ) -> None:
        self._fetch = fetch
        self._stale_after = stale_after
        self._clock = clock
        self._snapshot: _Snapshot | None = None

    async def refresh(self) -> None:
        now = self._clock()
        try:
            raw = await self._fetch()
            # Reach past the horizon so slots keep entering it while the feed is down.
            slots = parse_slots(raw, start=now, end=now + HORIZON + self._stale_after)
        except FeedError as exc:
            logger.warning("%s", exc)
            return
        self._snapshot = _Snapshot(tuple(slots), now)

    async def poll_forever(self, interval: timedelta) -> None:
        while True:
            await asyncio.sleep(interval.total_seconds())
            await self.refresh()

    @property
    def is_fresh(self) -> bool:
        return (
            self._snapshot is not None
            and self._clock() - self._snapshot.fetched_at <= self._stale_after
        )

    @property
    def last_update(self) -> datetime | None:
        return self._snapshot.fetched_at if self._snapshot else None

    def upcoming(self) -> list[Slot] | None:
        """Slots starting within the horizon, or None when the data cannot be trusted."""
        if self._snapshot is None or not self.is_fresh:
            return None
        now = self._clock()
        return [
            slot for slot in self._snapshot.slots if now < slot.start <= now + HORIZON
        ]
