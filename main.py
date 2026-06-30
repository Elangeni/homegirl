"""Entry point for the Homegirl wall display."""

from homegirl.app import HomegirlApp
from homegirl.settings import Settings


def main() -> None:
    """Start the fullscreen dashboard."""
    app = HomegirlApp(Settings.from_environment())
    app.run()


if __name__ == "__main__":
    main()
