"""Google Calendar integration with OAuth refresh and in-memory caching."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from pathlib import Path
import threading
from typing import Any

from homegirl.models.schedule import ScheduleData, ScheduleEvent

SCOPES = ("https://www.googleapis.com/auth/calendar.readonly",)
SCHEDULE_CACHE_SECONDS = 5 * 60
MAX_EVENTS = 10

logger = logging.getLogger(__name__)


class CalendarService:
    """Fetch and cache today's Google Calendar events without blocking rendering."""

    def __init__(
        self,
        client_id: str | None,
        client_secret: str | None,
        token_path: Path,
        calendar_id: str,
        timeout_seconds: float,
        refresh_interval_seconds: int = SCHEDULE_CACHE_SECONDS,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_path = token_path
        self._calendar_id = calendar_id
        self._timeout_seconds = timeout_seconds
        self._refresh_interval = timedelta(seconds=refresh_interval_seconds)
        self._schedule = ScheduleData(error="Schedule unavailable")
        self._is_fetching = False
        self._reported_missing_credentials = False
        self._lock = threading.Lock()

    def get_schedule(self, now: datetime) -> ScheduleData:
        """Return cached schedule and start a background refresh when needed."""
        if not self._credentials_configured():
            if not self._reported_missing_credentials:
                logger.info(
                    "Google Calendar OAuth credentials are missing; run "
                    "authorize_google_calendar.py to enable the schedule tile."
                )
                self._reported_missing_credentials = True
            return self._schedule

        with self._lock:
            schedule = self._schedule
            should_refresh = self._should_refresh(schedule, now) and not self._is_fetching
            if should_refresh:
                self._is_fetching = True

        if should_refresh:
            worker = threading.Thread(
                target=self._refresh_schedule,
                args=(now,),
                name="calendar-fetch",
                daemon=True,
            )
            worker.start()

        return schedule

    def _credentials_configured(self) -> bool:
        return bool(self._client_id and self._client_secret and self._token_path.exists())

    def _should_refresh(self, schedule: ScheduleData, now: datetime) -> bool:
        if schedule.last_updated is None:
            return True
        if schedule.last_updated.date() != now.date():
            return True
        return now - schedule.last_updated >= self._refresh_interval

    def _refresh_schedule(self, now: datetime) -> None:
        try:
            schedule = self._fetch_schedule(now)
        except Exception as exc:  # noqa: BLE001 - any auth/API failure just means "unavailable"
            logger.warning("Google Calendar request failed: %s", exc)
            self._keep_cache_or_error("Schedule unavailable")
            return

        with self._lock:
            self._schedule = schedule
            self._is_fetching = False
        logger.info("Schedule updated successfully.")

    def _fetch_schedule(self, now: datetime) -> ScheduleData:
        import httplib2
        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.discovery import build

        credentials = self._load_credentials()
        http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=self._timeout_seconds))
        service = build("calendar", "v3", http=http, cache_discovery=False)

        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        response = (
            service.events()
            .list(
                calendarId=self._calendar_id,
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=MAX_EVENTS,
            )
            .execute(num_retries=0)
        )

        events = tuple(
            event
            for item in response.get("items", ())
            if (event := self._parse_event(item)) is not None
        )
        return ScheduleData(events=events, last_updated=now)

    def _load_credentials(self):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        credentials = Credentials.from_authorized_user_file(str(self._token_path), SCOPES)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._token_path.write_text(credentials.to_json())
        return credentials

    def _parse_event(self, item: dict[str, Any]) -> ScheduleEvent | None:
        title = item.get("summary") or "Untitled event"
        start_info = item.get("start", {})
        end_info = item.get("end", {})

        if "dateTime" in start_info:
            start = datetime.fromisoformat(start_info["dateTime"])
            end = datetime.fromisoformat(end_info["dateTime"]) if "dateTime" in end_info else None
            return ScheduleEvent(title=title, start=start, end=end, all_day=False)

        if "date" in start_info:
            start = datetime.fromisoformat(start_info["date"])
            return ScheduleEvent(title=title, start=start, end=None, all_day=True)

        return None

    def _keep_cache_or_error(self, error: str) -> None:
        with self._lock:
            if self._schedule.is_available:
                logger.info("Using stale cached schedule from %s.", self._schedule.last_updated)
                self._is_fetching = False
                return

            self._schedule = ScheduleData(error=error)
            self._is_fetching = False
