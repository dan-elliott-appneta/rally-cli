"""Tests for UserSettings."""

import json
from pathlib import Path

import pytest

from rally_tui.user_settings import UserSettings


class TestUserSettingsDefaults:
    """Tests for UserSettings default behavior."""

    def test_default_theme_is_dark(self, tmp_path: Path, monkeypatch) -> None:
        """Default theme should be 'dark'."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.theme == "dark"

    def test_settings_created_without_file(self, tmp_path: Path, monkeypatch) -> None:
        """Settings should work when no config file exists."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.theme == "dark"


class TestUserSettingsPersistence:
    """Tests for settings persistence."""

    def test_theme_persists_to_file(self, tmp_path: Path, monkeypatch) -> None:
        """Theme setting should be saved to config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.theme = "light"

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["theme"] == "light"

    def test_theme_loads_from_file(self, tmp_path: Path, monkeypatch) -> None:
        """Theme should be loaded from existing config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write config file
        with config_file.open("w") as f:
            json.dump({"theme": "light"}, f)

        settings = UserSettings()
        assert settings.theme == "light"

    def test_creates_config_directory(self, tmp_path: Path, monkeypatch) -> None:
        """Config directory should be created if it doesn't exist."""
        config_dir = tmp_path / "subdir" / "rally-tui"
        config_file = config_dir / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", config_dir)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.theme = "light"

        assert config_dir.exists()
        assert config_file.exists()


class TestUserSettingsTheme:
    """Tests for theme property."""

    def test_set_theme_dark(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to set theme to dark."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.theme = "dark"
        assert settings.theme == "dark"

    def test_set_theme_light(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to set theme to light."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.theme = "light"
        assert settings.theme == "light"

    def test_invalid_theme_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid theme value should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="Theme must be 'dark' or 'light'"):
            settings.theme = "invalid"


class TestUserSettingsGeneric:
    """Tests for generic get/set methods."""

    def test_get_returns_default(self, tmp_path: Path, monkeypatch) -> None:
        """get() should return default for missing keys."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.get("nonexistent") is None
        assert settings.get("nonexistent", "default") == "default"

    def test_set_persists_value(self, tmp_path: Path, monkeypatch) -> None:
        """set() should persist value to file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.set("custom_key", "custom_value")

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["custom_key"] == "custom_value"

    def test_get_retrieves_set_value(self, tmp_path: Path, monkeypatch) -> None:
        """get() should retrieve previously set values."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.set("key", "value")
        assert settings.get("key") == "value"


class TestUserSettingsThemeName:
    """Tests for theme_name property (full Textual theme names)."""

    def test_default_theme_name(self, tmp_path: Path, monkeypatch) -> None:
        """Default theme_name should be textual-dark."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.theme_name == "textual-dark"

    def test_set_theme_name_catppuccin(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to set theme_name to catppuccin-mocha."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.theme_name = "catppuccin-mocha"
        assert settings.theme_name == "catppuccin-mocha"

    def test_theme_name_persists_to_file(self, tmp_path: Path, monkeypatch) -> None:
        """theme_name should persist to config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.theme_name = "nord"

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["theme_name"] == "nord"

    def test_theme_name_loads_from_file(self, tmp_path: Path, monkeypatch) -> None:
        """theme_name should load from config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write config file
        with config_file.open("w") as f:
            json.dump({"theme_name": "dracula"}, f)

        settings = UserSettings()
        assert settings.theme_name == "dracula"


class TestUserSettingsErrorHandling:
    """Tests for error handling."""

    def test_handles_corrupted_json(self, tmp_path: Path, monkeypatch) -> None:
        """Should handle corrupted JSON file gracefully."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write invalid JSON
        with config_file.open("w") as f:
            f.write("not valid json {{{")

        # Should not raise, should use defaults
        settings = UserSettings()
        assert settings.theme == "dark"


class TestUserSettingsLogLevel:
    """Tests for log_level property."""

    def test_default_log_level(self, tmp_path: Path, monkeypatch) -> None:
        """Default log_level should be INFO."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.log_level == "INFO"

    def test_set_log_level_debug(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to set log_level to DEBUG."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.log_level = "DEBUG"
        assert settings.log_level == "DEBUG"

    def test_set_log_level_lowercase(self, tmp_path: Path, monkeypatch) -> None:
        """log_level should accept lowercase and normalize to uppercase."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.log_level = "warning"
        assert settings.log_level == "WARNING"

    def test_log_level_persists_to_file(self, tmp_path: Path, monkeypatch) -> None:
        """log_level should persist to config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.log_level = "ERROR"

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["log_level"] == "ERROR"

    def test_log_level_loads_from_file(self, tmp_path: Path, monkeypatch) -> None:
        """log_level should load from config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write config file
        with config_file.open("w") as f:
            json.dump({"log_level": "CRITICAL"}, f)

        settings = UserSettings()
        assert settings.log_level == "CRITICAL"

    def test_invalid_log_level_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid log_level should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="Log level must be one of"):
            settings.log_level = "INVALID"

    def test_invalid_stored_log_level_returns_default(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Invalid stored log_level should return default INFO."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write invalid log level to file
        with config_file.open("w") as f:
            json.dump({"log_level": "INVALID"}, f)

        settings = UserSettings()
        assert settings.log_level == "INFO"


class TestUserSettingsParentOptions:
    """Tests for parent_options property."""

    def test_default_parent_options(self, tmp_path: Path, monkeypatch) -> None:
        """Default parent_options should be F59625, F59627, F59628."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.parent_options == ["F59625", "F59627", "F59628"]

    def test_set_parent_options(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to set custom parent options."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.parent_options = ["F111", "F222", "F333"]
        assert settings.parent_options == ["F111", "F222", "F333"]

    def test_parent_options_persists_to_file(self, tmp_path: Path, monkeypatch) -> None:
        """parent_options should persist to config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.parent_options = ["F100", "F200"]

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["parent_options"] == ["F100", "F200"]

    def test_parent_options_loads_from_file(self, tmp_path: Path, monkeypatch) -> None:
        """parent_options should load from config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write config file
        with config_file.open("w") as f:
            json.dump({"parent_options": ["F777", "F888"]}, f)

        settings = UserSettings()
        assert settings.parent_options == ["F777", "F888"]

    def test_invalid_parent_options_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid parent_options should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="Parent options must be a list of strings"):
            settings.parent_options = "not a list"  # type: ignore[assignment]

    def test_invalid_parent_options_non_strings_raises(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """parent_options with non-strings should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="Parent options must be a list of strings"):
            settings.parent_options = [1, 2, 3]  # type: ignore[list-item]

    def test_parent_options_returns_copy(self, tmp_path: Path, monkeypatch) -> None:
        """parent_options should return a copy to prevent mutation."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        # Set some options first
        settings.parent_options = ["F111", "F222"]

        options = settings.parent_options
        options.append("F999")

        # Original should not be modified
        assert settings.parent_options == ["F111", "F222"]
