# Homegirl MVP

Homegirl is a Raspberry Pi-powered ambient wall display. This MVP is a clean pygame-ce shell that opens directly into a fullscreen smart-display screen with a static ambient wallpaper, greeting, clock, date, and today's National Day when the API is available.

Tap the ambient screen to wake Homegirl into the app screen with a smooth crossfade. The first app screen shows a top time bar and a 2-by-2 grid: weather, today's schedule (from Google Calendar), a Mail tile ("Coming soon"), and a placeholder `d` tile; after 30 seconds without activity, it crossfades back to the ambient screen.

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
- `OPENWEATHER_API_KEY`: OpenWeather API key. If missing, weather is omitted.
- `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`: OAuth client credentials used to read your Google Calendar. See "Google Calendar setup" below.
- `GOOGLE_CALENDAR_ID`: which calendar to read. Defaults to `primary` (your main calendar).
- `GOOGLE_CALENDAR_TOKEN_FILE`: filename for the stored OAuth refresh token. Defaults to `google_calendar_token.json` in the project root.
- `HOMEGIRL_SPEAKER_DEVICE_MATCH`: case-insensitive substring used to pick the audio output device (e.g. `USB` to prefer a USB speaker over HDMI audio outputs). Defaults to `USB`; set empty to use the system default device.
- `HOMEGIRL_VOICE_MODEL_FILE`: path (relative to the project root) to the Piper `.onnx` voice model used for the startup greeting. Defaults to `voices/en_US-lessac-medium.onnx`. See "Sound" below.

The National Day client tries `https://api.nationaldaysapi.com/v1/date` first, then a quiet fallback endpoint if needed. It fetches in a background thread, caches the result in memory, and refreshes only once per local calendar day. If the requests fail or the responses cannot be parsed, the line is hidden.

Weather uses OpenWeather Current Weather API with hardcoded San Francisco coordinates for now (`37.7749`, `-122.4194`) and imperial units. Weather refreshes at most every 30 minutes, uses cached data between refreshes, and falls back to stale cached data if a refresh fails. If no API key or usable cache exists, weather UI stays quiet.

### Google Calendar setup

The Schedule tile reads today's events from your private Google Calendar. Google doesn't allow a plain API key to read private calendar data — it requires OAuth 2.0 user consent. A one-time setup is needed:

1. In [Google Cloud Console](https://console.cloud.google.com/), enable the "Google Calendar API" on a project, then create an OAuth client ID of type **Desktop app**.
2. Put the resulting client ID and secret in `.env` as `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`.
3. Run `python authorize_google_calendar.py` from a machine with a browser. It opens a Google consent screen and, once approved, writes a refresh token to `google_calendar_token.json`.
4. If you authorized from a different machine than the display device, copy `google_calendar_token.json` to the device (same folder as `main.py`).

`google_calendar_token.json` is gitignored — it's a credential, not source code. Once in place, the Schedule tile refreshes automatically (every 5 minutes, and immediately on a new day); without it, the tile just reads "Unavailable".

The schedule summary text is currently generated with simple rule-based phrasing (see `homegirl/schedule_insight.py`); an on-device LLM is planned to make the phrasing more natural later.

## Ambient Background

The background is loaded from static PNG artwork in `assets/backgrounds/`. The text floats directly on top of the wallpaper without cards, panels, borders, or containers. The app switches wallpapers based on local time:

- Morning: 05:00-11:59
- Afternoon: 12:00-16:59
- Evening: 17:00-20:59
- Night: 21:00-04:59

## Sound

Homegirl plays two kinds of sound through the speaker:

- A short chime whenever the daypart changes (morning/afternoon/evening/night), generated procedurally — see `tools/generate_chimes.py`, output lives in `assets/sounds/`.
- A spoken greeting once at app startup ("Good afternoon, Elangeni."), synthesized on-device with [Piper](https://github.com/OHF-Voice/piper1-gpl). Runs on a background thread so model loading/synthesis doesn't delay the first frame; if the voice model isn't installed, the greeting is silently skipped.

Audio output picks a device matching `HOMEGIRL_SPEAKER_DEVICE_MATCH` (see above) so it plays through a USB speaker rather than defaulting to HDMI audio.

### Piper setup

```bash
pip install piper-tts
python3 -m piper.download_voices en_US-lessac-medium --download-dir voices
```

That downloads `voices/en_US-lessac-medium.onnx` and its `.onnx.json` config — the path `Settings.voice_model_path` expects by default. Both files are gitignored (they're large binary models, not source).

## Architecture

- `homegirl/app.py`: pygame lifecycle and main loop
- `homegirl/animation.py`: static ambient wallpaper rendering
- `homegirl/clock.py`: local time/date formatting
- `homegirl/greeting.py`: greeting and daypart logic
- `homegirl/models/weather.py`: typed weather snapshot
- `homegirl/models/schedule.py`: typed schedule snapshot
- `homegirl/navigation.py`: wake and idle screen state
- `homegirl/national_day.py`: non-blocking API fetch and daily cache
- `homegirl/services/weather.py`: OpenWeather fetching, parsing, caching, and errors
- `homegirl/services/calendar.py`: Google Calendar OAuth, fetching, caching, and errors
- `homegirl/schedule_insight.py`: rule-based schedule summary text
- `homegirl/theme.py`: time-of-day palettes and animation colors
- `homegirl/audio.py`: sound effect playback through a chosen output device
- `homegirl/speech.py`: Piper text-to-speech synthesis
- `homegirl/ui.py`: ambient and app screen rendering
- `homegirl/settings.py`: runtime configuration
- `homegirl/transition.py`: screen transition timing and easing
