# celcat_calendar

Automatic calendar setup for Google Calendar using Celcat data.

This repository now contains a script that fetches the CELCAT timetable for:

`4TVL904S M2 Algorithms, Models and Verification`

and generates an `calendar.ics` file that can be subscribed to from Google Calendar.

## Generate the calendar file locally

```bash
python3 /home/runner/work/celcat_calendar/celcat_calendar/scripts/update_calendar.py
```

By default it writes:

`/home/runner/work/celcat_calendar/celcat_calendar/calendar.ics`

Optional arguments:

```bash
python3 /home/runner/work/celcat_calendar/celcat_calendar/scripts/update_calendar.py \
  --group "4TVL904S M2 Algorithms, Models and Verification" \
  --start 2026-09-01 \
  --end 2027-07-31 \
  --output /home/runner/work/celcat_calendar/celcat_calendar/calendar.ics
```

## Automatic update

A GitHub Actions workflow (`.github/workflows/update-calendar.yml`) updates `calendar.ics` every day and commits it when changes are detected.

## Subscribe from Google Calendar

1. Open Google Calendar.
2. Add calendar → **From URL**.
3. Use your raw GitHub file URL, for example:
   `https://raw.githubusercontent.com/LianilVIII/celcat_calendar/main/calendar.ics`
