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
  --exclude-module "4TIN914U Logic and languages" \
  --output /home/runner/work/celcat_calendar/celcat_calendar/calendar.ics
```

To exclude several modules, repeat `--exclude-module`.

## Automatic update

A GitHub Actions workflow (`.github/workflows/update-calendar.yml`) runs every 15 minutes, regenerates `calendar.ics` and commits it only when the timetable actually changed.

## Option 1 — Subscribe from Google Calendar (slow: 8 to 24 h delay)

1. Open Google Calendar.
2. Add calendar → **From URL**.
3. Use your raw GitHub file URL, for example:
   `https://raw.githubusercontent.com/LianilVIII/celcat_calendar/main/calendar.ics`

Google only re-downloads subscribed URLs every 8 to 24 hours and this delay cannot be changed, so changes on CELCAT can take up to a day to appear.

## Option 2 — Direct sync with the Google Calendar API (≈15 min delay, recommended)

The workflow can write the events directly into one of your Google calendars, so a change on CELCAT shows up on your phone within about 15 minutes.

1. In the [Google Cloud console](https://console.cloud.google.com/), create a project and enable the **Google Calendar API**.
2. **IAM & Admin → Service accounts** → create a service account, then **Keys → Add key → JSON** and download the key file.
3. In Google Calendar, create a new dedicated calendar (e.g. "CELCAT M2"). Do not use your main calendar: the sync deletes events it created that are no longer on CELCAT.
4. In that calendar's settings → **Share with specific people** → add the service account email (`...@...iam.gserviceaccount.com`) with **Make changes to events**.
5. Copy the **Calendar ID** from **Integrate calendar** (looks like `xxxx@group.calendar.google.com`).
6. In the GitHub repository → **Settings → Secrets and variables → Actions**, add:
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: the whole content of the JSON key file
   - `GOOGLE_CALENDAR_ID`: the calendar ID
7. Run the workflow once from the **Actions** tab (**Run workflow**) to fill the calendar.
8. If you were subscribed to the URL (option 1), remove that subscription to avoid duplicates.

The sync step is skipped automatically while these secrets are not set.
