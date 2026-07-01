"""Runtime configuration for Homegirl."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application settings kept in one place for later extension."""

    user_name: str = "Elangeni"
    app_title: str = "Homegirl"
    frames_per_second: int = 30
    animation_quality_scale: float = 0.45
    base_dir: Path = Path(__file__).resolve().parent.parent
    national_day_timeout_seconds: float = 4.0
    national_day_api_url: str = "https://api.nationaldaysapi.com/v1/date"
    national_day_fallback_api_url: str = "https://www.checkiday.com/api/3/?d=today"
    openweather_api_key: str | None = None
    openweather_timeout_seconds: float = 4.0
    fullscreen: bool = True

    @property
    def assets_dir(self) -> Path:
        """Return the root folder for background frame assets."""
        return self.base_dir / "assets"

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from environment variables when provided."""
        fullscreen_value = os.getenv("HOMEGIRL_FULLSCREEN", "1").strip().lower()
        return cls(
            user_name=os.getenv("HOMEGIRL_USER_NAME", cls.user_name),
            national_day_api_url=os.getenv(
                "HOMEGIRL_NATIONAL_DAY_API_URL",
                cls.national_day_api_url,
            ),
            national_day_fallback_api_url=os.getenv(
                "HOMEGIRL_NATIONAL_DAY_FALLBACK_API_URL",
                cls.national_day_fallback_api_url,
            ),
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
            fullscreen=fullscreen_value not in {"0", "false", "no", "off"},
        )
