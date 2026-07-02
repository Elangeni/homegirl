"""Main pygame application loop for Homegirl."""

from __future__ import annotations

from datetime import datetime

import pygame

from homegirl.animation import AmbientBackground
from homegirl.clock import format_date, format_time, now_local
from homegirl.greeting import get_daypart, get_greeting
from homegirl.models.weather import WeatherData
from homegirl.national_day import NationalDayClient
from homegirl.navigation import Screen, WakeController
from homegirl.settings import Settings
from homegirl.services.weather import WeatherService
from homegirl.theme import Theme, get_theme
from homegirl.transition import ScreenTransition
from homegirl.ui import (
    AmbientUI,
    AmbientViewModel,
    AppUI,
    AppViewModel,
    WeatherUI,
    WeatherViewModel,
)
from homegirl.weather_insight import get_advice, get_headline


APP_IDLE_TIMEOUT_SECONDS = 30.0
APP_LABELS = ("a", "b", "c", "d")
SCREEN_TRANSITION_SECONDS = 0.45


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
            background = AmbientBackground(self._settings.animation_quality_scale)
            ambient_ui = AmbientUI()
            app_ui = AppUI()
            weather_ui = WeatherUI()
            wake_controller = WakeController(APP_IDLE_TIMEOUT_SECONDS)
            screen_transition = ScreenTransition(Screen.AMBIENT, SCREEN_TRANSITION_SECONDS)
            running = True

            while running:
                delta_seconds = clock.tick(self._settings.frames_per_second) / 1000.0
                running, had_activity, tap_pos = self._handle_events(window_size)
                self._handle_tap(tap_pos, wake_controller, app_ui, weather_ui)
                active_screen = wake_controller.update(delta_seconds, had_activity)
                screen_transition.update(active_screen, delta_seconds)

                moment = now_local()
                daypart = get_daypart(moment)
                theme = get_theme(daypart)
                weather = self._weather.get_weather(moment)

                background.update(delta_seconds)
                if screen_transition.is_active:
                    source_surface = pygame.Surface(screen.get_size())
                    target_surface = pygame.Surface(screen.get_size())
                    self._draw_screen(
                        source_surface,
                        screen_transition.source_screen,
                        moment,
                        theme,
                        weather,
                        background,
                        ambient_ui,
                        app_ui,
                        weather_ui,
                    )
                    self._draw_screen(
                        target_surface,
                        screen_transition.target_screen,
                        moment,
                        theme,
                        weather,
                        background,
                        ambient_ui,
                        app_ui,
                        weather_ui,
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
                        background,
                        ambient_ui,
                        app_ui,
                        weather_ui,
                    )
                pygame.display.flip()
        finally:
            pygame.quit()

    def _draw_screen(
        self,
        surface: pygame.Surface,
        active_screen: Screen,
        moment: datetime,
        theme: Theme,
        weather: WeatherData,
        background: AmbientBackground,
        ambient_ui: AmbientUI,
        app_ui: AppUI,
        weather_ui: WeatherUI,
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
            )
            return

        app_ui.draw(
            surface,
            AppViewModel(time_text=format_time(moment), labels=APP_LABELS, weather=weather),
        )

    def _handle_tap(
        self,
        tap_pos: tuple[int, int] | None,
        wake_controller: WakeController,
        app_ui: AppUI,
        weather_ui: WeatherUI,
    ) -> None:
        """Navigate between the app grid and weather screens on tap."""
        if tap_pos is None:
            return

        current_screen = wake_controller.screen
        if current_screen == Screen.APP and app_ui.weather_tile_rect is not None:
            if app_ui.weather_tile_rect.collidepoint(tap_pos):
                wake_controller.show_weather()
        elif current_screen == Screen.WEATHER and weather_ui.dismiss_rect is not None:
            if weather_ui.dismiss_rect.collidepoint(tap_pos):
                wake_controller.show_app()

    def _handle_events(
        self,
        window_size: tuple[int, int],
    ) -> tuple[bool, bool, tuple[int, int] | None]:
        """Process quit events and report user activity and tap position."""
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
        return True, had_activity, tap_pos
