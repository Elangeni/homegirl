# Homegirl MVP

Homegirl is a Raspberry Pi-powered ambient wall display. This MVP is a clean pygame-ce shell that opens directly into a fullscreen smart-display screen with a static ambient wallpaper, greeting, clock, date, and today's National Day when the API is available.

Tap the ambient screen to wake Homegirl into the app screen with a smooth crossfade. The first app screen shows a top time bar and a 2-by-2 grid labeled `a`, `b`, `c`, and `d`; after 30 seconds without activity, it crossfades back to the ambient screen.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
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
- `OPENWEATHER_API_KEY`: OpenWeather One Call API 3.0 key. If missing, weather is omitted.

The National Day client tries `https://api.nationaldaysapi.com/v1/date` first, then a quiet fallback endpoint if needed. It fetches in a background thread, caches the result in memory, and refreshes only once per local calendar day. If the requests fail or the responses cannot be parsed, the line is hidden.

Weather uses OpenWeather One Call API 3.0 with hardcoded San Francisco coordinates for now (`37.7749`, `-122.4194`) and imperial units. Weather refreshes at most every 30 minutes, uses cached data between refreshes, and falls back to stale cached data if a refresh fails. If no API key or usable cache exists, weather UI stays quiet.

## Ambient Background

The background is loaded from static PNG artwork in `assets/backgrounds/`. The text floats directly on top of the wallpaper without cards, panels, borders, or containers. The app switches wallpapers based on local time:

- Morning: 05:00-11:59
- Afternoon: 12:00-16:59
- Evening: 17:00-20:59
- Night: 21:00-04:59

## Architecture

- `homegirl/app.py`: pygame lifecycle and main loop
- `homegirl/animation.py`: static ambient wallpaper rendering
- `homegirl/clock.py`: local time/date formatting
- `homegirl/greeting.py`: greeting and daypart logic
- `homegirl/models/weather.py`: typed weather snapshot
- `homegirl/navigation.py`: wake and idle screen state
- `homegirl/national_day.py`: non-blocking API fetch and daily cache
- `homegirl/services/weather.py`: OpenWeather fetching, parsing, caching, and errors
- `homegirl/theme.py`: time-of-day palettes and animation colors
- `homegirl/ui.py`: ambient and app screen rendering
- `homegirl/settings.py`: runtime configuration
- `homegirl/transition.py`: screen transition timing and easing
