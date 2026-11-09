from datetime import datetime

import pytest

from cabinet.settings import PRACTICE_TZ


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    # A Monday morning.
    return FakeClock(datetime(2026, 11, 9, 10, 0, tzinfo=PRACTICE_TZ))
