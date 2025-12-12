"""User settings persisted to ~/.config/rally-tui/config.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rally_tui.utils.keybindings import (
    VALID_PROFILES,
    VIM_KEYBINDINGS,
    get_profile_keybindings,
    validate_key,
)


class UserSettings:
    """User settings stored in JSON config file.

    Settings are persisted to ~/.config/rally-tui/config.json
    and loaded automatically on startup.
    """

    CONFIG_DIR = Path.home() / ".config" / "rally-tui"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    LOG_FILE = CONFIG_DIR / "rally-tui.log"

    # Defaults
    DEFAULT_THEME = "dark"
    DEFAULT_THEME_NAME = "textual-dark"
    DEFAULT_LOG_LEVEL = "INFO"
    VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    # Default parent Feature IDs for quick selection
    DEFAULT_PARENT_OPTIONS: list[str] = ["F59625", "F59627", "F59628"]
    # Default keybinding profile
    DEFAULT_KEYBINDING_PROFILE = "vim"

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

    @property
    def log_level(self) -> str:
        """Get the current log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        level = self._settings.get("log_level", self.DEFAULT_LOG_LEVEL)
        # Ensure it's a valid level
        if level.upper() not in self.VALID_LOG_LEVELS:
            return self.DEFAULT_LOG_LEVEL
        return level.upper()

    @log_level.setter
    def log_level(self, value: str) -> None:
        """Set and persist the log level."""
        value = value.upper()
        if value not in self.VALID_LOG_LEVELS:
            raise ValueError(f"Log level must be one of: {', '.join(self.VALID_LOG_LEVELS)}")
        self._settings["log_level"] = value
        self._save()

    @property
    def parent_options(self) -> list[str]:
        """Get the list of quick-select parent Feature IDs.

        Returns a copy to prevent mutation of internal state.
        """
        return list(self._settings.get("parent_options", self.DEFAULT_PARENT_OPTIONS))

    @parent_options.setter
    def parent_options(self, value: list[str]) -> None:
        """Set and persist the parent options list."""
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ValueError("Parent options must be a list of strings")
        self._settings["parent_options"] = value
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set and persist a setting value."""
        self._settings[key] = value
        self._save()

    # Keybinding properties and methods

    @property
    def keybinding_profile(self) -> str:
        """Get the current keybinding profile ('vim', 'emacs', or 'custom')."""
        profile = self._settings.get("keybinding_profile", self.DEFAULT_KEYBINDING_PROFILE)
        if profile not in VALID_PROFILES:
            return self.DEFAULT_KEYBINDING_PROFILE
        return profile

    @keybinding_profile.setter
    def keybinding_profile(self, value: str) -> None:
        """Set and persist the keybinding profile."""
        if value not in VALID_PROFILES:
            raise ValueError(f"Profile must be one of: {', '.join(VALID_PROFILES)}")
        self._settings["keybinding_profile"] = value
        self._save()

    @property
    def keybindings(self) -> dict[str, str]:
        """Get the current keybindings.

        Returns merged keybindings: profile defaults + user overrides.
        Returns a copy to prevent mutation of internal state.
        """
        # Start with profile defaults
        profile = self.keybinding_profile
        result = get_profile_keybindings(profile)

        # Apply any user overrides
        custom = self._settings.get("keybindings", {})
        if isinstance(custom, dict):
            for action_id, key in custom.items():
                if isinstance(key, str) and action_id in result:
                    result[action_id] = key

        return result

    @keybindings.setter
    def keybindings(self, value: dict[str, str]) -> None:
        """Set and persist custom keybindings.

        Args:
            value: Dictionary of action_id -> key mappings.
        """
        if not isinstance(value, dict):
            raise ValueError("Keybindings must be a dictionary")
        for action_id, key in value.items():
            if not isinstance(action_id, str) or not isinstance(key, str):
                raise ValueError("Keybinding keys and values must be strings")
            if not validate_key(key):
                raise ValueError(f"Invalid key: {key}")

        self._settings["keybindings"] = value
        # When setting custom keybindings, switch to custom profile
        if value:
            self._settings["keybinding_profile"] = "custom"
        self._save()

    def get_keybinding(self, action_id: str) -> str:
        """Get the key for a specific action.

        Args:
            action_id: The action identifier (e.g., 'navigation.down')

        Returns:
            The key string (e.g., 'j' or 'ctrl+n')

        Raises:
            KeyError: If action_id is not found
        """
        bindings = self.keybindings
        if action_id not in bindings:
            raise KeyError(f"Unknown action: {action_id}")
        return bindings[action_id]

    def set_keybinding(self, action_id: str, key: str) -> None:
        """Set a single keybinding.

        Args:
            action_id: The action identifier
            key: The new key string

        Raises:
            ValueError: If key is invalid
            KeyError: If action_id is not known
        """
        if not validate_key(key):
            raise ValueError(f"Invalid key: {key}")

        # Verify action exists in defaults
        if action_id not in VIM_KEYBINDINGS:
            raise KeyError(f"Unknown action: {action_id}")

        # Get current custom bindings or empty dict
        custom = dict(self._settings.get("keybindings", {}))
        custom[action_id] = key
        self._settings["keybindings"] = custom
        self._settings["keybinding_profile"] = "custom"
        self._save()

    def reset_keybindings(self, profile: str = "vim") -> None:
        """Reset keybindings to a profile's defaults.

        Args:
            profile: Profile to reset to ('vim' or 'emacs')

        Raises:
            ValueError: If profile is invalid
        """
        if profile not in ("vim", "emacs"):
            raise ValueError(f"Profile must be 'vim' or 'emacs', got: {profile}")

        # Clear custom bindings
        self._settings.pop("keybindings", None)
        self._settings["keybinding_profile"] = profile
        self._save()
