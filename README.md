# Homegirl MVP

Homegirl is a Raspberry Pi-powered ambient wall display. This MVP is a clean pygame-ce shell that opens directly into a fullscreen smart-display screen with a generated lava-lamp ambient background, greeting, clock, date, and today's National Day when the API is available.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

On the Raspberry Pi display:

```bash
DISPLAY=:0 python main.py
```

or:

```bash
./run.sh
```

Press `Esc` to quit during local development.

## Configuration

Environment variables:

- `HOMEGIRL_USER_NAME`: name shown in `Hello, ...` text. Defaults to `Elangeni`.
- `HOMEGIRL_FULLSCREEN`: set to `0` for a resizable desktop window. Defaults to fullscreen.
- `HOMEGIRL_NATIONAL_DAY_API_URL`: override the National Day JSON API URL.
- `HOMEGIRL_NATIONAL_DAY_FALLBACK_API_URL`: override the fallback JSON API URL.

The National Day client tries `https://api.nationaldaysapi.com/v1/date` first, then a quiet fallback endpoint if needed. It fetches in a background thread, caches the result in memory, and refreshes only once per local calendar day. If the requests fail or the responses cannot be parsed, the line is hidden.

## Ambient Background

The background is generated in code with large translucent moving blobs and smooth gradients. The text floats directly on top of the wallpaper without cards, panels, borders, or containers. The app switches palettes based on local time:

- Morning: 05:00-11:59
- Afternoon: 12:00-16:59
- Evening: 17:00-20:59
- Night: 21:00-04:59

## Architecture

- `homegirl/app.py`: pygame lifecycle and main loop
- `homegirl/animation.py`: generated ambient blob animation
- `homegirl/clock.py`: local time/date formatting
- `homegirl/greeting.py`: greeting and daypart logic
- `homegirl/national_day.py`: non-blocking API fetch and daily cache
- `homegirl/theme.py`: time-of-day palettes and animation colors
- `homegirl/ui.py`: ambient floating text rendering
- `homegirl/settings.py`: runtime configuration
