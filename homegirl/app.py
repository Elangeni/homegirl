"""Main pygame application loop for Homegirl."""

from __future__ import annotations

import pygame

from homegirl.animation import AmbientBackground
from homegirl.clock import format_date, format_time, now_local
from homegirl.greeting import get_daypart, get_greeting
from homegirl.national_day import NationalDayClient
from homegirl.navigation import Screen, WakeController
from homegirl.settings import Settings
from homegirl.theme import Theme, get_theme
from homegirl.transition import ScreenTransition
from homegirl.ui import AmbientUI, AmbientViewModel, AppUI, AppViewModel


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
            wake_controller = WakeController(APP_IDLE_TIMEOUT_SECONDS)
            screen_transition = ScreenTransition(Screen.AMBIENT, SCREEN_TRANSITION_SECONDS)
            running = True

            while running:
                delta_seconds = clock.tick(self._settings.frames_per_second) / 1000.0
                running, had_activity = self._handle_events()
                active_screen = wake_controller.update(delta_seconds, had_activity)
                screen_transition.update(active_screen, delta_seconds)

                moment = now_local()
                daypart = get_daypart(moment)
                theme = get_theme(daypart)

                background.update(delta_seconds)
                if screen_transition.is_active:
                    source_surface = pygame.Surface(screen.get_size())
                    target_surface = pygame.Surface(screen.get_size())
                    self._draw_screen(
                        source_surface,
                        screen_transition.source_screen,
                        moment,
                        theme,
                        background,
                        ambient_ui,
                        app_ui,
                    )
                    self._draw_screen(
                        target_surface,
                        screen_transition.target_screen,
                        moment,
                        theme,
                        background,
                        ambient_ui,
                        app_ui,
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
                        background,
                        ambient_ui,
                        app_ui,
                    )
                pygame.display.flip()
        finally:
            pygame.quit()

    def _draw_screen(
        self,
        surface: pygame.Surface,
        active_screen: Screen,
        moment,
        theme: Theme,
        background: AmbientBackground,
        ambient_ui: AmbientUI,
        app_ui: AppUI,
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
                ),
                theme,
            )
            return

        app_ui.draw(
            surface,
            AppViewModel(time_text=format_time(moment), labels=APP_LABELS),
        )

    def _handle_events(self) -> tuple[bool, bool]:
        """Process quit events and report user activity."""
        had_activity = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, had_activity
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False, had_activity
            if event.type in {
                pygame.FINGERDOWN,
                pygame.MOUSEBUTTONDOWN,
                pygame.KEYDOWN,
            }:
                had_activity = True
        return True, had_activity
