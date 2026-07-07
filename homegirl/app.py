"""Main pygame application loop for Homegirl."""

from __future__ import annotations

import threading
from datetime import date, datetime

import pygame

from homegirl.animation import AmbientBackground
from homegirl.audio import AudioPlayer
from homegirl.clock import format_date, format_time, now_local
from homegirl.greeting import Daypart, get_daypart, get_greeting
from homegirl.speech import SpeechSynthesizer
from homegirl.models.schedule import ScheduleData
from homegirl.models.weather import WeatherData
from homegirl.national_day import NationalDayClient
from homegirl.navigation import Screen, WakeController
from homegirl.reflection import REFLECTION_PROMPTS
from homegirl.schedule_insight import (
    get_free_time_gap,
    get_free_time_hint,
    get_schedule_headline,
    get_schedule_summary,
    group_events_by_day,
    timed_events_today,
)
from homegirl.services.calendar import CalendarService
from homegirl.services.weather import WeatherService
from homegirl.settings import Settings
from homegirl.suggestion import SuggestionState
from homegirl.theme import Theme, get_theme
from homegirl.transition import ScreenTransition
from homegirl.ui import (
    AmbientUI,
    AmbientViewModel,
    AppUI,
    AppViewModel,
    CalendarUI,
    CalendarViewModel,
    CelebrationUI,
    DayDetailUI,
    DayDetailViewModel,
    FullCalendarUI,
    FullCalendarViewModel,
    ReflectionUI,
    ReflectionViewModel,
    SuggestionUI,
    WeatherUI,
    WeatherViewModel,
)
from homegirl.weather_insight import get_advice, get_headline


APP_IDLE_TIMEOUT_SECONDS = 30.0
SCREEN_TRANSITION_SECONDS = 0.45

# The celebration screen has no completion-detection engine behind it yet; this
# is placeholder copy shown when a developer presses "C" to preview the screen.
CELEBRATION_DEMO_HEADLINE = "Finished the sewing project."
CELEBRATION_DEMO_SUBTEXT = "Nice one."

DAYPART_CHIME_FILES: dict[Daypart, str] = {
    Daypart.MORNING: "daypart_morning.wav",
    Daypart.AFTERNOON: "daypart_afternoon.wav",
    Daypart.EVENING: "daypart_evening.wav",
    Daypart.NIGHT: "daypart_night.wav",
}


class HomegirlApp:
    """Fullscreen ambient smart-display application."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._national_day = NationalDayClient(
            (settings.national_day_api_url, settings.national_day_fallback_api_url),
            settings.national_day_timeout_seconds,
        )
        self._weather = WeatherService(
            settings.weather_api_key,
            settings.weather_timeout_seconds,
        )
        self._calendar = CalendarService(
            settings.google_client_id,
            settings.google_client_secret,
            settings.google_calendar_token_path,
            settings.google_calendar_id,
            settings.google_calendar_timeout_seconds,
        )
        self._selected_day: date | None = None

    def run(self) -> None:
        """Run until the user quits or presses Escape."""
        pygame.init()
        try:
            flags = pygame.FULLSCREEN if self._settings.fullscreen else pygame.RESIZABLE
            display = pygame.display.Info()
            display_size = (max(1, display.current_w), max(1, display.current_h))
            window_size = display_size if self._settings.fullscreen else (1280, 720)
            screen = pygame.display.set_mode(window_size, flags)
            pygame.display.set_caption(self._settings.app_title)
            pygame.mouse.set_visible(False)

            clock = pygame.time.Clock()
            audio = AudioPlayer(self._settings.speaker_device_match)
            previous_daypart = get_daypart(now_local())
            threading.Thread(
                target=self._play_startup_greeting,
                args=(audio,),
                daemon=True,
            ).start()
            background = AmbientBackground(self._settings.animation_quality_scale)
            ambient_ui = AmbientUI()
            suggestion_ui = SuggestionUI()
            suggestion_state = SuggestionState()
            app_ui = AppUI()
            weather_ui = WeatherUI()
            calendar_ui = CalendarUI()
            full_calendar_ui = FullCalendarUI()
            day_detail_ui = DayDetailUI()
            celebration_ui = CelebrationUI()
            reflection_ui = ReflectionUI()
            wake_controller = WakeController(APP_IDLE_TIMEOUT_SECONDS)
            screen_transition = ScreenTransition(Screen.AMBIENT, SCREEN_TRANSITION_SECONDS)
            running = True

            while running:
                delta_seconds = clock.tick(self._settings.frames_per_second) / 1000.0
                running, had_activity, tap_pos = self._handle_events(window_size, wake_controller)
                self._handle_tap(
                    tap_pos,
                    wake_controller,
                    suggestion_state,
                    suggestion_ui,
                    app_ui,
                    weather_ui,
                    calendar_ui,
                    full_calendar_ui,
                    reflection_ui,
                )
                active_screen = wake_controller.update(delta_seconds, had_activity)
                screen_transition.update(active_screen, delta_seconds)

                moment = now_local()
                daypart = get_daypart(moment)
                if daypart != previous_daypart:
                    audio.play(self._settings.sounds_dir / DAYPART_CHIME_FILES[daypart])
                    previous_daypart = daypart
                theme = get_theme(daypart)
                weather = self._weather.get_weather(moment)
                schedule = self._calendar.get_schedule(moment)

                background.update(delta_seconds)
                ui_bundle = (
                    ambient_ui,
                    suggestion_ui,
                    suggestion_state,
                    app_ui,
                    weather_ui,
                    calendar_ui,
                    full_calendar_ui,
                    day_detail_ui,
                    celebration_ui,
                    reflection_ui,
                )
                if screen_transition.is_active:
                    source_surface = pygame.Surface(screen.get_size())
                    target_surface = pygame.Surface(screen.get_size())
                    self._draw_screen(
                        source_surface,
                        screen_transition.source_screen,
                        moment,
                        theme,
                        weather,
                        schedule,
                        background,
                        *ui_bundle,
                    )
                    self._draw_screen(
                        target_surface,
                        screen_transition.target_screen,
                        moment,
                        theme,
                        weather,
                        schedule,
                        background,
                        *ui_bundle,
                    )
                    screen.blit(source_surface, (0, 0))
                    target_surface.set_alpha(screen_transition.target_alpha)
                    screen.blit(target_surface, (0, 0))
                else:
                    self._draw_screen(
                        screen,
                        active_screen,
                        moment,
                        theme,
                        weather,
                        schedule,
                        background,
                        *ui_bundle,
                    )
                pygame.display.flip()
        finally:
            pygame.quit()

    def _play_startup_greeting(self, audio: AudioPlayer) -> None:
        """Speak a one-time greeting on a background thread.

        Runs off the main thread since the ElevenLabs call can take a
        moment; the render loop shouldn't wait on it.
        """
        speech = SpeechSynthesizer(self._settings.elevenlabs_api_key, self._settings.elevenlabs_voice_id)
        if not speech.is_available:
            return
        greeting_text = f"{get_greeting(now_local())}, {self._settings.user_name}."
        if speech.synthesize_to_file(greeting_text, self._settings.greeting_cache_path):
            audio.play(self._settings.greeting_cache_path)

    def _draw_screen(
        self,
        surface: pygame.Surface,
        active_screen: Screen,
        moment: datetime,
        theme: Theme,
        weather: WeatherData,
        schedule: ScheduleData,
        background: AmbientBackground,
        ambient_ui: AmbientUI,
        suggestion_ui: SuggestionUI,
        suggestion_state: SuggestionState,
        app_ui: AppUI,
        weather_ui: WeatherUI,
        calendar_ui: CalendarUI,
        full_calendar_ui: FullCalendarUI,
        day_detail_ui: DayDetailUI,
        celebration_ui: CelebrationUI,
        reflection_ui: ReflectionUI,
    ) -> None:
        """Draw one top-level screen onto a surface."""
        if active_screen == Screen.AMBIENT:
            background.draw(surface, theme)

            national_day_state = self._national_day.get_state(moment.date())
            ambient_ui.draw(
                surface,
                AmbientViewModel(
                    greeting=get_greeting(moment),
                    user_name=self._settings.user_name,
                    time_text=format_time(moment),
                    date_text=format_date(moment),
                    national_day=national_day_state.name,
                    weather=weather,
                ),
                theme,
            )

            suggestion = suggestion_state.active
            if suggestion is not None:
                suggestion_ui.draw(surface, suggestion)
            return

        if active_screen == Screen.WEATHER:
            daypart = get_daypart(moment)
            weather_ui.draw(
                surface,
                WeatherViewModel(
                    time_text=format_time(moment),
                    weather=weather,
                    headline=get_headline(weather),
                    advice=get_advice(weather, daypart),
                ),
                background,
            )
            return

        if active_screen == Screen.CALENDAR:
            calendar_ui.draw(
                surface,
                CalendarViewModel(
                    time_text=format_time(moment),
                    headline=get_schedule_headline(schedule, moment),
                    free_hint=get_free_time_hint(schedule, moment),
                    events=timed_events_today(schedule),
                    free_gap=get_free_time_gap(schedule, moment),
                ),
                background,
            )
            return

        if active_screen == Screen.FULL_CALENDAR:
            month_schedule = self._calendar.get_month_schedule(moment)
            full_calendar_ui.draw(
                surface,
                FullCalendarViewModel(
                    time_text=format_time(moment),
                    today=moment.date(),
                    events_by_day=group_events_by_day(month_schedule),
                ),
                background,
            )
            return

        if active_screen == Screen.DAY_DETAIL:
            selected_day = self._selected_day or moment.date()
            month_schedule = self._calendar.get_month_schedule(moment)
            day_events = tuple(
                event for event in sorted(month_schedule.events, key=lambda e: e.start)
                if event.start.date() == selected_day
            )
            day_detail_ui.draw(
                surface,
                DayDetailViewModel(
                    month_label=selected_day.strftime("%B %Y"),
                    weekday_label=selected_day.strftime("%A"),
                    date_label=selected_day.strftime("%B %-d"),
                    events=day_events,
                ),
                background,
            )
            return

        if active_screen == Screen.CELEBRATION:
            celebration_ui.draw(
                surface,
                CELEBRATION_DEMO_HEADLINE,
                CELEBRATION_DEMO_SUBTEXT,
                format_date(moment),
                background,
            )
            return

        if active_screen == Screen.REFLECTION:
            reflection_ui.draw(
                surface,
                ReflectionViewModel(time_text=_reflection_time_text(moment), prompts=REFLECTION_PROMPTS),
                background,
            )
            return

        app_ui.draw(
            surface,
            AppViewModel(
                time_text=format_time(moment),
                date_text=format_date(moment),
                today_text=get_schedule_headline(schedule, moment) or "Unavailable",
                weather_text=_home_weather_text(weather),
                calendar_text=(
                    get_free_time_hint(schedule, moment)
                    or get_schedule_summary(schedule, moment)
                    or "Unavailable"
                ),
            ),
            background,
        )

    def _handle_tap(
        self,
        tap_pos: tuple[int, int] | None,
        wake_controller: WakeController,
        suggestion_state: SuggestionState,
        suggestion_ui: SuggestionUI,
        app_ui: AppUI,
        weather_ui: WeatherUI,
        calendar_ui: CalendarUI,
        full_calendar_ui: FullCalendarUI,
        reflection_ui: ReflectionUI,
    ) -> None:
        """Navigate between screens based on where the current screen was tapped."""
        if tap_pos is None:
            return

        current_screen = wake_controller.screen

        if current_screen == Screen.AMBIENT:
            suggestion = suggestion_state.active
            if suggestion is not None:
                if suggestion_ui.confirm_rect and suggestion_ui.confirm_rect.collidepoint(tap_pos):
                    suggestion_state.confirm()
                    return
                if suggestion_ui.dismiss_rect and suggestion_ui.dismiss_rect.collidepoint(tap_pos):
                    suggestion_state.dismiss()
                    return
                if suggestion_ui.close_rect and suggestion_ui.close_rect.collidepoint(tap_pos):
                    suggestion_state.dismiss()
                    return
            wake_controller.show_app()
            return

        if current_screen == Screen.APP:
            if app_ui.weather_rect and app_ui.weather_rect.collidepoint(tap_pos):
                wake_controller.show_weather()
            elif app_ui.today_rect and app_ui.today_rect.collidepoint(tap_pos):
                wake_controller.show_calendar()
            elif app_ui.calendar_rect and app_ui.calendar_rect.collidepoint(tap_pos):
                wake_controller.show_calendar()
            return

        if current_screen == Screen.WEATHER:
            if weather_ui.dismiss_rect and weather_ui.dismiss_rect.collidepoint(tap_pos):
                wake_controller.dismiss()
            return

        if current_screen == Screen.CALENDAR:
            if calendar_ui.dismiss_rect and calendar_ui.dismiss_rect.collidepoint(tap_pos):
                wake_controller.dismiss()
            elif calendar_ui.full_calendar_rect and calendar_ui.full_calendar_rect.collidepoint(tap_pos):
                wake_controller.show_full_calendar()
            return

        if current_screen == Screen.FULL_CALENDAR:
            for day, rect in full_calendar_ui.day_rects.items():
                if rect.collidepoint(tap_pos):
                    self._selected_day = day
                    wake_controller.show_day_detail()
                    return
            wake_controller.dismiss()
            return

        if current_screen == Screen.DAY_DETAIL:
            wake_controller.dismiss()
            return

        if current_screen == Screen.CELEBRATION:
            wake_controller.dismiss()
            return

        if current_screen == Screen.REFLECTION:
            if reflection_ui.dismiss_rect and reflection_ui.dismiss_rect.collidepoint(tap_pos):
                wake_controller.dismiss()
            return

    def _handle_events(
        self,
        window_size: tuple[int, int],
        wake_controller: WakeController,
    ) -> tuple[bool, bool, tuple[int, int] | None]:
        """Process quit events and report user activity and tap position.

        "C" and "R" are developer shortcuts that jump straight to the
        celebration and weekly-reflection screens — there's no real
        completion-detection or scheduling engine to trigger them yet.
        """
        had_activity = False
        tap_pos: tuple[int, int] | None = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, had_activity, tap_pos
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False, had_activity, tap_pos
            if event.type == pygame.MOUSEBUTTONDOWN:
                had_activity = True
                tap_pos = event.pos
            elif event.type == pygame.FINGERDOWN:
                had_activity = True
                tap_pos = (round(event.x * window_size[0]), round(event.y * window_size[1]))
            elif event.type == pygame.KEYDOWN:
                had_activity = True
                if event.key == pygame.K_c:
                    wake_controller.show_celebration()
                elif event.key == pygame.K_r:
                    wake_controller.show_reflection()
                elif wake_controller.screen == Screen.AMBIENT:
                    wake_controller.show_app()
        return True, had_activity, tap_pos


def _home_weather_text(weather: WeatherData) -> str:
    if not weather.is_available:
        return "Unavailable"
    temp = f"{round(weather.current_temp)}°F"
    condition = weather.condition.title() if weather.condition else "Weather"
    return f"{condition} · {temp}"


def _reflection_time_text(moment: datetime) -> str:
    time_text = moment.strftime("%I:%M %p").lstrip("0")
    return f"{time_text} · {moment.strftime('%A')}"
