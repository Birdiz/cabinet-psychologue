import logging
from collections.abc import Callable
from datetime import timedelta

import httpx
import pytest
from conftest import FakeClock
from fastapi.testclient import TestClient
from feeds import PATIENT_EVENT, calendar, event

from cabinet.feed import to_https
from cabinet.main import create_app
from cabinet.settings import ConfigError, Settings

FEED_URL = "webcal://calendars.test/published/secret-token"
Handler = Callable[[httpx.Request], httpx.Response]


def serving(body: bytes, status: int = 200) -> Handler:
    return lambda request: httpx.Response(status, content=body)


def client_for(handler: Handler, clock: FakeClock) -> TestClient:
    settings = Settings(feed_url=FEED_URL, poll_interval=timedelta(hours=1))
    return TestClient(
        create_app(settings, transport=httpx.MockTransport(handler), clock=clock)
    )


def test_page_lists_slots_without_any_patient_data(clock: FakeClock) -> None:
    with client_for(serving(calendar(PATIENT_EVENT)), clock) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Mardi 10 novembre" in response.text
    assert "14h00 – 14h45" in response.text
    assert "Dupont" not in response.text
    assert "dupont" not in response.text


def test_days_without_a_slot_read_closed(clock: FakeClock) -> None:
    with client_for(serving(calendar(PATIENT_EVENT)), clock) as client:
        text = client.get("/").text

    assert "Mercredi 11 novembre" in text
    assert "Dimanche 15 novembre" in text
    assert text.count("Fermé") == 5


def test_partly_covered_days_appear_only_with_a_slot(clock: FakeClock) -> None:
    with client_for(serving(calendar(PATIENT_EVENT)), clock) as client:
        without_slot = client.get("/").text

    assert "Lundi 9 novembre" not in without_slot
    assert "Lundi 16 novembre" not in without_slot

    last_day = event("20261116T090000", "20261116T094500")
    with client_for(serving(calendar(last_day)), clock) as client:
        with_slot = client.get("/").text

    assert "Lundi 16 novembre" in with_slot
    assert "9h00 – 9h45" in with_slot


def test_page_says_so_when_there_is_no_slot(clock: FakeClock) -> None:
    with client_for(serving(calendar()), clock) as client:
        assert "Aucun créneau libre" in client.get("/").text


def test_feed_down_at_boot_still_serves_the_page(clock: FakeClock) -> None:
    with client_for(serving(b"", status=500), clock) as client:
        page = client.get("/")
        health = client.get("/healthz")

    assert page.status_code == 200
    assert "ne peuvent pas être affichés" in page.text
    assert health.status_code == 503


def test_stale_slots_are_replaced_by_a_notice_and_health_fails(
    clock: FakeClock,
) -> None:
    with client_for(serving(calendar(PATIENT_EVENT)), clock) as client:
        assert client.get("/healthz").status_code == 200
        clock.now += timedelta(hours=2)
        page = client.get("/")
        health = client.get("/healthz")

    assert "14h00" not in page.text
    assert health.status_code == 503
    assert health.json() == {"status": "stale"}


def test_webcal_is_fetched_over_https(clock: FakeClock) -> None:
    seen: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, content=calendar())

    with client_for(handler, clock):
        pass

    assert seen[0].scheme == "https"


@pytest.mark.parametrize("failure", ["status", "connection", "garbage"])
def test_failures_never_log_the_feed_url(
    failure: str, clock: FakeClock, caplog: pytest.LogCaptureFixture
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if failure == "connection":
            raise httpx.ConnectError(f"cannot reach {request.url}")
        if failure == "status":
            return httpx.Response(404)
        return httpx.Response(200, content=b"<html>Mme Dupont</html>")

    with caplog.at_level(logging.INFO), client_for(handler, clock):
        pass

    assert "feed" in caplog.text
    assert "secret-token" not in caplog.text
    assert "Dupont" not in caplog.text


def test_successful_fetch_does_not_log_the_feed_url(
    clock: FakeClock, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO), client_for(serving(calendar()), clock):
        pass

    assert "secret-token" not in caplog.text


def test_page_sends_security_and_cache_headers(clock: FakeClock) -> None:
    with client_for(serving(calendar()), clock) as client:
        headers = client.get("/").headers

    assert "default-src 'none'" in headers["content-security-policy"]
    assert "font-src 'self'" in headers["content-security-policy"]
    assert headers["cache-control"] == "no-cache"


def test_legal_page_names_the_publisher_and_the_host(clock: FakeClock) -> None:
    with client_for(serving(calendar()), clock) as client:
        response = client.get("/mentions-legales")

    assert response.status_code == 200
    assert "Hannah Schreiber" in response.text
    assert "Railway Corporation" in response.text


@pytest.mark.parametrize(
    "path",
    [
        "site.css",
        "favicon.svg",
        "assets/ginkgo-a.svg",
        "assets/ginkgo-a-mark.svg",
        "fonts/Sacramento-Regular.woff2",
        "fonts/Nunito-Variable.woff2",
    ],
)
def test_static_files_are_served(path: str, clock: FakeClock) -> None:
    with client_for(serving(calendar()), clock) as client:
        assert client.get(f"/static/{path}").status_code == 200


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_api_documentation_is_not_exposed(path: str, clock: FakeClock) -> None:
    with client_for(serving(calendar()), clock) as client:
        assert client.get(path).status_code == 404


def test_missing_feed_url_is_a_config_error() -> None:
    with pytest.raises(ConfigError):
        Settings.from_env({})


def test_settings_repr_hides_the_feed_url() -> None:
    assert "secret-token" not in repr(Settings(feed_url=FEED_URL))


def test_feed_url_is_read_from_the_environment() -> None:
    settings = Settings.from_env({"FEED_URL": f"  {FEED_URL}\n"})

    assert settings.feed_url == FEED_URL


def test_blank_feed_url_is_a_config_error() -> None:
    with pytest.raises(ConfigError):
        Settings.from_env({"FEED_URL": "   "})


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("webcal://calendars.test/a", "https://calendars.test/a"),
        ("https://calendars.test/a", "https://calendars.test/a"),
    ],
)
def test_feed_links_end_up_on_https(url: str, expected: str) -> None:
    assert to_https(url) == expected
