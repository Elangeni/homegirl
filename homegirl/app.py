"""Main pygame application loop for Homegirl."""

from __future__ import annotations

import pygame

from homegirl.animation import AmbientBackground
from homegirl.clock import format_date, format_time, now_local
from homegirl.greeting import get_daypart, get_greeting
from homegirl.national_day import NationalDayClient
from homegirl.settings import Settings
from homegirl.theme import get_theme
from homegirl.ui import AmbientUI, AmbientViewModel


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
            ui = AmbientUI()
            running = True

            while running:
                delta_seconds = clock.tick(self._settings.frames_per_second) / 1000.0
                running = self._handle_events()

                moment = now_local()
                daypart = get_daypart(moment)
                theme = get_theme(daypart)
                background.update(delta_seconds)
                background.draw(screen, theme)

                national_day_state = self._national_day.get_state(moment.date())
                ui.draw(
                    screen,
                    AmbientViewModel(
                        greeting=get_greeting(moment),
                        user_name=self._settings.user_name,
                        time_text=format_time(moment),
                        date_text=format_date(moment),
                        national_day=national_day_state.name,
                    ),
                    theme,
                )
                pygame.display.flip()
        finally:
            pygame.quit()

    def _handle_events(self) -> bool:
        """Process quit events while keeping the render loop responsive."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True
