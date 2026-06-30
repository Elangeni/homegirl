"""Main pygame application loop for Homegirl."""

from __future__ import annotations

import pygame

from homegirl.animation import BackgroundManager
from homegirl.clock import format_date, format_time, now_local
from homegirl.greeting import get_daypart, get_greeting
from homegirl.national_day import NationalDayClient
from homegirl.settings import Settings
from homegirl.ui import DashboardUI, DashboardViewModel


class HomegirlApp:
    """Fullscreen ambient dashboard application."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._national_day = NationalDayClient(
            settings.national_day_api_url,
            settings.national_day_timeout_seconds,
        )

    def run(self) -> None:
        """Run until the user quits or presses Escape."""
        pygame.init()
        try:
            flags = pygame.FULLSCREEN if self._settings.fullscreen else pygame.RESIZABLE
            screen = pygame.display.set_mode((0, 0), flags)
            pygame.display.set_caption(self._settings.app_title)
            pygame.mouse.set_visible(False)

            clock = pygame.time.Clock()
            backgrounds = BackgroundManager(
                self._settings.assets_dir,
                self._settings.background_frame_seconds,
            )
            ui = DashboardUI()
            running = True

            while running:
                delta_seconds = clock.tick(self._settings.frames_per_second) / 1000.0
                running = self._handle_events()

                moment = now_local()
                daypart = get_daypart(moment)
                backgrounds.set_daypart(daypart)
                backgrounds.update(delta_seconds)
                backgrounds.draw(screen)

                national_day_state = self._national_day.get_state(moment.date())
                ui.draw(
                    screen,
                    DashboardViewModel(
                        greeting=get_greeting(moment),
                        user_name=self._settings.user_name,
                        time_text=format_time(moment),
                        date_text=format_date(moment),
                        national_day=national_day_state.name,
                    ),
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
