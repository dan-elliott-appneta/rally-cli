"""User settings persisted to ~/.config/rally-tui/config.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class UserSettings:
    """User settings stored in JSON config file.

    Settings are persisted to ~/.config/rally-tui/config.json
    and loaded automatically on startup.
    """

    CONFIG_DIR = Path.home() / ".config" / "rally-tui"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    # Defaults
    DEFAULT_THEME = "dark"
    DEFAULT_THEME_NAME = "textual-dark"

    def __init__(self) -> None:
        """Initialize user settings, loading from file if exists."""
        self._settings: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load settings from config file."""
        if self.CONFIG_FILE.exists():
            try:
                with self.CONFIG_FILE.open("r") as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, OSError):
                # If file is corrupted, start fresh
                self._settings = {}

    def _save(self) -> None:
        """Save settings to config file."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with self.CONFIG_FILE.open("w") as f:
            json.dump(self._settings, f, indent=2)

    @property
    def theme(self) -> str:
        """Get the current theme ('dark' or 'light')."""
        return self._settings.get("theme", self.DEFAULT_THEME)

    @theme.setter
    def theme(self, value: str) -> None:
        """Set and persist the theme."""
        if value not in ("dark", "light"):
            raise ValueError("Theme must be 'dark' or 'light'")
        self._settings["theme"] = value
        self._save()

    @property
    def theme_name(self) -> str:
        """Get the current theme name (e.g., 'catppuccin-mocha')."""
        return self._settings.get("theme_name", self.DEFAULT_THEME_NAME)

    @theme_name.setter
    def theme_name(self, value: str) -> None:
        """Set and persist the theme name."""
        self._settings["theme_name"] = value
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set and persist a setting value."""
        self._settings[key] = value
        self._save()
