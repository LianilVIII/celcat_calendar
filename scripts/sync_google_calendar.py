#!/usr/bin/env python3
"""Push CELCAT events directly into a Google Calendar through the Calendar API.

Google Calendar only refreshes calendars subscribed "from URL" every 8-24 hours,
so this script writes the events itself: changes show up as soon as it runs.

Environment variables:
  GOOGLE_SERVICE_ACCOUNT_JSON  content of the service account JSON key
  GOOGLE_CALENDAR_ID           id of the calendar shared with the service account
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TIMEZONE = "Europe/Paris"
MARKER = "celcatSync"


def _event_id(uid: str) -> str:
    # Google event ids only allow base32hex characters (0-9, a-v): hex digits fit.
    return hashlib.sha1(uid.encode("utf-8")).hexdigest()


def _to_body(event: dict[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "summary": event["summary"],
        "location": event["location"],
        "description": event["description"],
        "start": {"dateTime": event["start"], "timeZone": TIMEZONE},
        "end": {"dateTime": event["end"], "timeZone": TIMEZONE},
        "status": "confirmed",
    }
    digest = hashlib.sha1(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
    body["extendedProperties"] = {"private": {MARKER: "1", "celcatHash": digest}}
    return body


def _existing_events(service, calendar_id: str) -> dict[str, dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    page_token = None
    while True:
        response = (
            service.events()
            .list(
                calendarId=calendar_id,
                privateExtendedProperty=f"{MARKER}=1",
                showDeleted=True,
                maxResults=2500,
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("items", []):
            existing[item["id"]] = item
        page_token = response.get("nextPageToken")
        if not page_token:
            return existing


def sync(service, calendar_id: str, events: list[dict[str, str]]) -> None:
    desired = {_event_id(event["uid"]): _to_body(event) for event in events}
    existing = _existing_events(service, calendar_id)
    created = updated = deleted = 0

    for event_id, body in desired.items():
        current = existing.get(event_id)
        if current is None:
            try:
                service.events().insert(calendarId=calendar_id, body={**body, "id": event_id}).execute()
                created += 1
                continue
            except HttpError as error:
                # 409: the id already exists (e.g. deleted outside our listing): update it instead.
                if error.resp.status != 409:
                    raise
        elif (
            current.get("status") == body["status"]
            and current.get("extendedProperties", {}).get("private", {}).get("celcatHash")
            == body["extendedProperties"]["private"]["celcatHash"]
        ):
            continue
        service.events().update(calendarId=calendar_id, eventId=event_id, body=body).execute()
        updated += 1

    for event_id, current in existing.items():
        if event_id not in desired and current.get("status") != "cancelled":
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            deleted += 1

    print(f"Google Calendar sync: {created} created, {updated} updated, {deleted} deleted, {len(desired)} total")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--events", default="events.json", help="JSON file written by update_calendar.py --json-output")
    args = parser.parse_args()

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]), scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
    events = json.loads(Path(args.events).read_text(encoding="utf-8"))
    sync(service, os.environ["GOOGLE_CALENDAR_ID"], events)


if __name__ == "__main__":
    main()
