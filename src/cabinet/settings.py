import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Self
from zoneinfo import ZoneInfo

PRACTICE_TZ = ZoneInfo("Europe/Paris")


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Settings:
    # The feed URL grants read access to the calendar: keep it out of any repr.
    feed_url: str = field(repr=False)
    poll_interval: timedelta = timedelta(minutes=5)
    stale_after: timedelta = timedelta(hours=1)

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> Self:
        feed_url = env.get("FEED_URL", "").strip()
        if not feed_url:
            raise ConfigError("FEED_URL is not set")
        return cls(feed_url=feed_url)
