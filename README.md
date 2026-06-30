# Homegirl MVP

Homegirl is a Raspberry Pi-powered ambient wall display. This MVP is a clean pygame-ce shell that opens directly into a fullscreen dashboard with an animated disk-backed background, greeting, clock, date, and today's National Day when the API is available.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Press `Esc` to quit during local development.

## Configuration

Environment variables:

- `HOMEGIRL_USER_NAME`: name shown in `Hello, ...` text. Defaults to `Elangeni`.
- `HOMEGIRL_FULLSCREEN`: set to `0` for a resizable desktop window. Defaults to fullscreen.
- `HOMEGIRL_NATIONAL_DAY_API_URL`: override the National Day JSON API URL.

The National Day client defaults to Checkiday's public JSON endpoint, prefers holidays whose names start with `National`, fetches in a background thread, caches the result in memory, and refreshes only once per local calendar day. If the request fails or the response cannot be parsed, the line is hidden.

## Assets

Animated backgrounds are loaded from PNG frames on disk:

```text
assets/
  morning/
  afternoon/
  evening/
  night/
```

Each folder contains sequential PNGs such as `frame_000.png`. The app switches folders based on local time:

- Morning: 05:00-11:59
- Afternoon: 12:00-16:59
- Evening: 17:00-20:59
- Night: 21:00-04:59

The included frames are lightweight lava-lamp placeholders so the MVP runs immediately. Replace them with production artwork later without changing code.

## Architecture

- `homegirl/app.py`: pygame lifecycle and main loop
- `homegirl/animation.py`: disk-backed frame animation
- `homegirl/clock.py`: local time/date formatting
- `homegirl/greeting.py`: greeting and daypart logic
- `homegirl/national_day.py`: non-blocking API fetch and daily cache
- `homegirl/ui.py`: dashboard rendering and future widget contract
- `homegirl/settings.py`: runtime configuration

The UI module includes a small `Widget` protocol so later features like weather, calendar, todos, Home Assistant, music controls, and notifications can be added without rewriting the application loop.
