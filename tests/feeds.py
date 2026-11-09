"""Hand-written calendar samples. Never commit a real feed here."""


def raw_event(*lines: str) -> str:
    parts = (
        "BEGIN:VEVENT",
        "UID:slot@test",
        "DTSTAMP:20261101T000000Z",
        *lines,
        "END:VEVENT",
    )
    return "\r\n".join(parts)


def event(start: str, end: str, *extra: str) -> str:
    return raw_event(
        f"DTSTART;TZID=Europe/Paris:{start}",
        f"DTEND;TZID=Europe/Paris:{end}",
        *extra,
    )


def calendar(*events: str) -> bytes:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//test//EN",
        *events,
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(lines).encode()


# A mistake the practice could make: a real appointment in the free-slots calendar.
PATIENT_EVENT = event(
    "20261110T140000",
    "20261110T144500",
    "SUMMARY:Mme Dupont",
    "DESCRIPTION:Dupont - suivi",
    "LOCATION:Chez Dupont",
    "ATTENDEE:mailto:dupont@example.invalid",
)
