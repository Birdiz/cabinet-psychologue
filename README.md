# cabinet-psychologue

[![CI](https://github.com/Birdiz/cabinet-psychologue/actions/workflows/ci.yml/badge.svg)](https://github.com/Birdiz/cabinet-psychologue/actions/workflows/ci.yml)

Public page listing a practice's free appointment slots, built from a dedicated calendar feed (only the start and end of each event are kept).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs and manages Python 3.13 for you)
- [Docker](https://docs.docker.com/get-docker/) with Compose v2.22+ (only for the container targets)

## Run locally

```sh
cp .env.example .env   # then fill in the values
make install
make dev               # http://localhost:8000
```

## Run in Docker

```sh
make up                # builds the image, reads .env if present
```

`make watch` rebuilds the container on source changes, `make down` stops it.

## Checks

```sh
make check             # lint + strict type check + tests (95 % coverage gate)
```

Run `make` alone to list every target. CI runs the same checks on every push to `main` and every pull request, then builds the production image and loads the page from it.

## Configuration

| Variable   | Required | Purpose                                                              |
| ---------- | -------- | -------------------------------------------------------------------- |
| `FEED_URL` | yes      | Public link of the dedicated free-slots calendar. Treat as a secret. |

The app refuses to boot without it. Practice details live in `src/cabinet/content.py`.

`GET /healthz` returns 200 while the slots are fresh and 503 once the feed has been failing for an hour. Point an external uptime check at it: a process that is up can still be serving nothing useful.

## Design decisions

**The practice manages its availability from a phone calendar.** There is no admin UI, login or database. A dedicated calendar holds only free slots and the site reads its public link. The main calendar is never read and no Apple credential reaches the server.

**Only start and end leave the parser.** `parse_slots` is the privacy boundary: someone may one day type a patient's name into the wrong calendar, so every other field is dropped there, before any storage or logging. The raw feed is never written anywhere, and a test feeds a patient event through the whole page to prove it.

**Errors cannot leak.** The feed URL grants read access, and httpx puts URLs in its messages and INFO logs, while parser errors can quote the offending line. Failures are reduced to a type name and raised without chaining, the httpx loggers are capped at WARNING, and `Settings` hides the URL from its `repr`.

**Stale slots are hidden, not shown.** Slots stay in memory and are refreshed every five minutes. If the feed fails, the last slots remain for one hour, then the page asks visitors to phone instead of showing availability that may be false.

**Next seven days, not calendar week.** A Sunday-evening cancellation for Monday morning must be visible.

**A day without a slot reads "Fermé".** The calendar only holds free slots, so the site cannot tell a full day from a day off. Today and the day the seven-day window ends on are only partly covered, so they are listed only when they hold a slot.

**Nothing about visitors is collected by the app.** No cookies, no analytics, no third-party fonts or scripts, and uvicorn's access log is off. The Content-Security-Policy enforces the no-third-party rule in the browser.

**What was left out.** Online booking, waitlists and notifications all require storing a name or a contact, which would mean handling health-adjacent data on the server.
