"""
Sample main module for testing arc42gen.
"""

from typing import Optional


class Application:
    """Main application class."""

    def __init__(self, name: str = "TestApp"):
        """Initialize application."""
        self.name = name
        self.running = False

    def start(self) -> None:
        """Start the application."""
        self.running = True
        print(f"{self.name} started")

    def stop(self) -> None:
        """Stop the application."""
        self.running = False
        print(f"{self.name} stopped")


class Config:
    """Configuration class."""

    def __init__(self):
        self.debug = False
        self.log_level = "INFO"

    def load(self, path: str) -> None:
        """Load configuration from file."""
        pass


def main() -> None:
    """Main entry point."""
    app = Application()
    app.start()


if __name__ == "__main__":
    main()
