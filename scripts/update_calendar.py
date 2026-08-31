#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import UTC, date, datetime
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE_URL = "https://celcat.u-bordeaux.fr/calendar"
RESOURCE_TYPES = [103, 104, 100, 101, 102, 105, 106]
DEFAULT_GROUP = "4TVL904S M2 Algorithms, Models and Verification"

VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Europe/Paris
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE"""


def _build_opener():
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0"),
        ("X-Requested-With", "XMLHttpRequest"),
        ("Referer", f"{BASE_URL}/"),
    ]
    opener.open(Request(f"{BASE_URL}/"), timeout=30).read()
    return opener


def _post_json(opener, path: str, data: dict[str, Any]) -> Any:
    body = urlencode(data, doseq=True).encode("utf-8")
    request = Request(
        f"{BASE_URL}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
    )
    with opener.open(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_events(group: str, start: str, end: str) -> list[dict[str, Any]]:
    opener = _build_opener()
    for resource_type in RESOURCE_TYPES:
        payload = _post_json(
            opener,
            "/Home/GetCalendarData",
            {
                "start": start,
                "end": end,
                "resType": str(resource_type),
                "calView": "month",
                "federationIds[]": group,
                "colourScheme": "3",
            },
        )
        if payload:
            return payload
    raise RuntimeError(
        "No events found. Check the group name and date range."
    )


def _escape_ics(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold_ics(line: str) -> str:
    folded: list[str] = []
    current = ""
    for char in line:
        if len((current + char).encode("utf-8")) > 73:
            folded.append(current)
            current = " " + char
        else:
            current += char
    folded.append(current)
    return "\r\n".join(folded)


def _to_ics_datetime(value: str) -> str:
    return datetime.fromisoformat(value[:19]).strftime("%Y%m%dT%H%M%S")


def _description_lines(raw_description: str) -> list[str]:
    text = re.sub(r"<br\s*/?>", "\n", raw_description or "", flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return [html.unescape(line).strip() for line in text.split("\n") if line.strip()]


def build_ics(events: list[dict[str, Any]], group: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//celcat_calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_ics(group)}",
        "X-WR-TIMEZONE:Europe/Paris",
        VTIMEZONE,
    ]

    for index, event in enumerate(events):
        start = event.get("start")
        if not start:
            continue

        end = event.get("end") or start
        modules = event.get("modules") or []
        sites = event.get("sites") or []
        category = (event.get("eventCategory") or "").strip()
        description_lines = _description_lines(event.get("description") or "")

        summary = (modules[0] if modules else (description_lines[0] if description_lines else "Course")).strip()
        if category:
            summary = f"{summary} - {category}"

        location = ", ".join(site.strip() for site in sites if site)
        uid = str(event.get("id") or f"{index}-{start}")

        lines.extend(
            [
                "BEGIN:VEVENT",
                _fold_ics(f"UID:{_escape_ics(uid)}@celcat.u-bordeaux.fr"),
                f"DTSTAMP:{stamp}",
                f"DTSTART;TZID=Europe/Paris:{_to_ics_datetime(start)}",
                f"DTEND;TZID=Europe/Paris:{_to_ics_datetime(end)}",
                _fold_ics(f"SUMMARY:{_escape_ics(summary)}"),
            ]
        )
        if location:
            lines.append(_fold_ics(f"LOCATION:{_escape_ics(location)}"))
        if description_lines:
            lines.append(_fold_ics(f"DESCRIPTION:{_escape_ics(chr(10).join(description_lines))}"))
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def default_dates() -> tuple[str, str]:
    year = date.today().year
    return f"{year}-09-01", f"{year + 1}-07-31"


def parse_args() -> argparse.Namespace:
    default_start, default_end = default_dates()
    parser = argparse.ArgumentParser(
        description="Fetch CELCAT data and generate a subscribable ICS file."
    )
    parser.add_argument("--group", default=DEFAULT_GROUP)
    parser.add_argument("--start", default=default_start)
    parser.add_argument("--end", default=default_end)
    parser.add_argument("--output", default="calendar.ics")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events = fetch_events(args.group, args.start, args.end)
    content = build_ics(events, args.group)
    output = Path(args.output)
    output.write_text(content, encoding="utf-8", newline="")
    print(f"Wrote {output} with {len(events)} events")


if __name__ == "__main__":
    main()
