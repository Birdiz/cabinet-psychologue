import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cabinet.agenda import Agenda, Clock, utc_now
from cabinet.content import PRACTICE
from cabinet.display import format_time, week_days
from cabinet.feed import fetch_feed
from cabinet.settings import Settings

_HERE = Path(__file__).parent
_FEED_TIMEOUT_SECONDS = 10
_CSP = (
    "default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)

templates = Jinja2Templates(directory=_HERE / "templates")


def create_app(
    settings: Settings | None = None,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
    clock: Clock = utc_now,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Read here rather than at import, so a missing secret stops the boot.
        config = settings or Settings.from_env()
        async with httpx.AsyncClient(
            transport=transport, timeout=_FEED_TIMEOUT_SECONDS, follow_redirects=True
        ) as client:
            agenda = Agenda(
                lambda: fetch_feed(client, config.feed_url),
                stale_after=config.stale_after,
                clock=clock,
            )
            await agenda.refresh()
            app.state.agenda = agenda
            polling = asyncio.create_task(agenda.poll_forever(config.poll_interval))
            yield
            polling.cancel()
            with suppress(asyncio.CancelledError):
                await polling

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = _CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> Response:
        agenda: Agenda = request.app.state.agenda
        slots = agenda.upcoming()
        updated_at = agenda.last_update
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "practice": PRACTICE,
                "days": None if slots is None else week_days(slots, clock()),
                "updated_at": format_time(updated_at) if updated_at else None,
            },
            # The page is only useful fresh: browsers must revalidate it.
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/mentions-legales", response_class=HTMLResponse)
    def legal(request: Request) -> Response:
        return templates.TemplateResponse(request, "legal.html", {"practice": PRACTICE})

    @app.api_route("/healthz", methods=["GET", "HEAD"])
    def health(request: Request) -> JSONResponse:
        """503 when the feed has been failing, so a process that is up can still alert."""
        agenda: Agenda = request.app.state.agenda
        if agenda.is_fresh:
            return JSONResponse({"status": "ok"})
        return JSONResponse({"status": "stale"}, status_code=503)

    return app


app = create_app()
