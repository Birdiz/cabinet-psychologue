import logging

import httpx

from cabinet.slots import FeedError

# httpx logs every request URL at INFO, and this URL is a secret.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def to_https(url: str) -> str:
    """Apple publishes calendars as webcal://, which is HTTPS under another name."""
    if url.startswith("webcal://"):
        return "https://" + url.removeprefix("webcal://")
    return url


async def fetch_feed(client: httpx.AsyncClient, url: str) -> bytes:
    try:
        response = await client.get(to_https(url))
        response.raise_for_status()
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        # httpx puts the URL in its messages: report the type only, and do not chain.
        raise FeedError(f"feed request failed: {type(exc).__name__}") from None
    return response.content
