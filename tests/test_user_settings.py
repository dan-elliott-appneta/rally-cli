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

    def test_invalid_stored_log_level_returns_default(self, tmp_path: Path, monkeypatch) -> None:
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

    def test_invalid_parent_options_non_strings_raises(self, tmp_path: Path, monkeypatch) -> None:
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


class TestUserSettingsKeybindingProfile:
    """Tests for keybinding_profile property."""

    def test_default_profile_is_vim(self, tmp_path: Path, monkeypatch) -> None:
        """Default keybinding profile should be 'vim'."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.keybinding_profile == "vim"

    def test_set_profile_emacs(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to set profile to emacs."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.keybinding_profile = "emacs"
        assert settings.keybinding_profile == "emacs"

    def test_set_profile_custom(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to set profile to custom."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.keybinding_profile = "custom"
        assert settings.keybinding_profile == "custom"

    def test_invalid_profile_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid profile should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="Profile must be one of"):
            settings.keybinding_profile = "invalid"

    def test_invalid_stored_profile_returns_default(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid stored profile should return default vim."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write invalid profile to file
        with config_file.open("w") as f:
            json.dump({"keybinding_profile": "invalid"}, f)

        settings = UserSettings()
        assert settings.keybinding_profile == "vim"

    def test_profile_persists_to_file(self, tmp_path: Path, monkeypatch) -> None:
        """Profile should persist to config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.keybinding_profile = "emacs"

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["keybinding_profile"] == "emacs"


class TestUserSettingsKeybindings:
    """Tests for keybindings property."""

    def test_default_keybindings_are_vim(self, tmp_path: Path, monkeypatch) -> None:
        """Default keybindings should be vim profile."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        bindings = settings.keybindings
        assert bindings["navigation.down"] == "j"
        assert bindings["navigation.up"] == "k"
        assert bindings["action.quit"] == "q"

    def test_emacs_keybindings_when_emacs_profile(self, tmp_path: Path, monkeypatch) -> None:
        """Emacs profile should use emacs keybindings."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.keybinding_profile = "emacs"

        bindings = settings.keybindings
        assert bindings["navigation.down"] == "ctrl+n"
        assert bindings["navigation.up"] == "ctrl+p"
        assert bindings["action.quit"] == "ctrl+q"

    def test_custom_bindings_override_defaults(self, tmp_path: Path, monkeypatch) -> None:
        """Custom bindings should override profile defaults."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write custom bindings to file
        with config_file.open("w") as f:
            json.dump({"keybinding_profile": "vim", "keybindings": {"navigation.down": "x"}}, f)

        settings = UserSettings()
        bindings = settings.keybindings
        # Custom override
        assert bindings["navigation.down"] == "x"
        # Other vim defaults still work
        assert bindings["navigation.up"] == "k"

    def test_keybindings_returns_copy(self, tmp_path: Path, monkeypatch) -> None:
        """keybindings should return a copy to prevent mutation."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        bindings = settings.keybindings
        bindings["navigation.down"] = "changed"

        # Original should not be modified
        assert settings.keybindings["navigation.down"] == "j"

    def test_set_keybindings_switches_to_custom(self, tmp_path: Path, monkeypatch) -> None:
        """Setting keybindings should switch to custom profile."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.keybindings = {"navigation.down": "x", "navigation.up": "y"}

        assert settings.keybinding_profile == "custom"

    def test_set_keybindings_validates_keys(self, tmp_path: Path, monkeypatch) -> None:
        """Setting keybindings should validate key values."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="Invalid key"):
            settings.keybindings = {"navigation.down": "invalid_key_name"}


class TestUserSettingsGetKeybinding:
    """Tests for get_keybinding method."""

    def test_get_keybinding_returns_value(self, tmp_path: Path, monkeypatch) -> None:
        """get_keybinding should return the key for an action."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.get_keybinding("navigation.down") == "j"
        assert settings.get_keybinding("action.quit") == "q"

    def test_get_keybinding_unknown_action_raises(self, tmp_path: Path, monkeypatch) -> None:
        """get_keybinding should raise KeyError for unknown actions."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(KeyError, match="Unknown action"):
            settings.get_keybinding("nonexistent.action")


class TestUserSettingsSetKeybinding:
    """Tests for set_keybinding method."""

    def test_set_keybinding_updates_key(self, tmp_path: Path, monkeypatch) -> None:
        """set_keybinding should update the key for an action."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.set_keybinding("navigation.down", "x")

        assert settings.get_keybinding("navigation.down") == "x"
        # Others unchanged
        assert settings.get_keybinding("navigation.up") == "k"

    def test_set_keybinding_switches_to_custom(self, tmp_path: Path, monkeypatch) -> None:
        """set_keybinding should switch to custom profile."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.set_keybinding("navigation.down", "x")

        assert settings.keybinding_profile == "custom"

    def test_set_keybinding_invalid_key_raises(self, tmp_path: Path, monkeypatch) -> None:
        """set_keybinding should reject invalid keys."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="Invalid key"):
            settings.set_keybinding("navigation.down", "invalid_key")

    def test_set_keybinding_unknown_action_raises(self, tmp_path: Path, monkeypatch) -> None:
        """set_keybinding should reject unknown actions."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(KeyError, match="Unknown action"):
            settings.set_keybinding("unknown.action", "x")

    def test_set_keybinding_persists(self, tmp_path: Path, monkeypatch) -> None:
        """set_keybinding changes should persist to file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.set_keybinding("navigation.down", "x")

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["keybindings"]["navigation.down"] == "x"


class TestUserSettingsResetKeybindings:
    """Tests for reset_keybindings method."""

    def test_reset_to_vim(self, tmp_path: Path, monkeypatch) -> None:
        """reset_keybindings('vim') should restore vim defaults."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        # Set custom binding
        settings.set_keybinding("navigation.down", "x")
        assert settings.get_keybinding("navigation.down") == "x"

        # Reset
        settings.reset_keybindings("vim")

        assert settings.keybinding_profile == "vim"
        assert settings.get_keybinding("navigation.down") == "j"

    def test_reset_to_emacs(self, tmp_path: Path, monkeypatch) -> None:
        """reset_keybindings('emacs') should set emacs profile."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.reset_keybindings("emacs")

        assert settings.keybinding_profile == "emacs"
        assert settings.get_keybinding("navigation.down") == "ctrl+n"

    def test_reset_invalid_profile_raises(self, tmp_path: Path, monkeypatch) -> None:
        """reset_keybindings with invalid profile should raise."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="Profile must be"):
            settings.reset_keybindings("invalid")

    def test_reset_clears_custom_bindings(self, tmp_path: Path, monkeypatch) -> None:
        """reset_keybindings should clear custom bindings from file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.set_keybinding("navigation.down", "x")
        settings.reset_keybindings("vim")

        # Check file
        with config_file.open() as f:
            data = json.load(f)
        assert "keybindings" not in data


class TestUserSettingsCacheEnabled:
    """Tests for cache_enabled property."""

    def test_default_cache_enabled(self, tmp_path: Path, monkeypatch) -> None:
        """Default cache_enabled should be True."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.cache_enabled is True

    def test_set_cache_enabled_false(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to disable caching."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.cache_enabled = False
        assert settings.cache_enabled is False

    def test_cache_enabled_persists_to_file(self, tmp_path: Path, monkeypatch) -> None:
        """cache_enabled should persist to config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.cache_enabled = False

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["cache_enabled"] is False

    def test_cache_enabled_loads_from_file(self, tmp_path: Path, monkeypatch) -> None:
        """cache_enabled should load from config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write config file
        with config_file.open("w") as f:
            json.dump({"cache_enabled": False}, f)

        settings = UserSettings()
        assert settings.cache_enabled is False

    def test_invalid_cache_enabled_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid cache_enabled value should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="cache_enabled must be a boolean"):
            settings.cache_enabled = "not a bool"  # type: ignore[assignment]


class TestUserSettingsCacheTTLMinutes:
    """Tests for cache_ttl_minutes property."""

    def test_default_cache_ttl_minutes(self, tmp_path: Path, monkeypatch) -> None:
        """Default cache_ttl_minutes should be 15."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.cache_ttl_minutes == 15

    def test_set_cache_ttl_minutes(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to set cache TTL."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.cache_ttl_minutes = 30
        assert settings.cache_ttl_minutes == 30

    def test_cache_ttl_minutes_persists_to_file(self, tmp_path: Path, monkeypatch) -> None:
        """cache_ttl_minutes should persist to config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.cache_ttl_minutes = 60

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["cache_ttl_minutes"] == 60

    def test_cache_ttl_minutes_loads_from_file(self, tmp_path: Path, monkeypatch) -> None:
        """cache_ttl_minutes should load from config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write config file
        with config_file.open("w") as f:
            json.dump({"cache_ttl_minutes": 45}, f)

        settings = UserSettings()
        assert settings.cache_ttl_minutes == 45

    def test_invalid_cache_ttl_minutes_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid cache_ttl_minutes should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="cache_ttl_minutes must be a positive integer"):
            settings.cache_ttl_minutes = -5

    def test_zero_cache_ttl_minutes_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Zero cache_ttl_minutes should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="cache_ttl_minutes must be a positive integer"):
            settings.cache_ttl_minutes = 0

    def test_invalid_stored_cache_ttl_returns_default(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid stored cache_ttl_minutes should return default."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write invalid TTL to file
        with config_file.open("w") as f:
            json.dump({"cache_ttl_minutes": -10}, f)

        settings = UserSettings()
        assert settings.cache_ttl_minutes == 15


class TestUserSettingsCacheAutoRefresh:
    """Tests for cache_auto_refresh property."""

    def test_default_cache_auto_refresh(self, tmp_path: Path, monkeypatch) -> None:
        """Default cache_auto_refresh should be True."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        assert settings.cache_auto_refresh is True

    def test_set_cache_auto_refresh_false(self, tmp_path: Path, monkeypatch) -> None:
        """Should be able to disable auto-refresh."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        settings.cache_auto_refresh = False
        assert settings.cache_auto_refresh is False

    def test_cache_auto_refresh_persists_to_file(self, tmp_path: Path, monkeypatch) -> None:
        """cache_auto_refresh should persist to config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        settings = UserSettings()
        settings.cache_auto_refresh = False

        # Read file directly
        with config_file.open() as f:
            data = json.load(f)
        assert data["cache_auto_refresh"] is False

    def test_cache_auto_refresh_loads_from_file(self, tmp_path: Path, monkeypatch) -> None:
        """cache_auto_refresh should load from config file."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)

        # Write config file
        with config_file.open("w") as f:
            json.dump({"cache_auto_refresh": False}, f)

        settings = UserSettings()
        assert settings.cache_auto_refresh is False

    def test_invalid_cache_auto_refresh_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Invalid cache_auto_refresh value should raise ValueError."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")

        settings = UserSettings()
        with pytest.raises(ValueError, match="cache_auto_refresh must be a boolean"):
            settings.cache_auto_refresh = "not a bool"  # type: ignore[assignment]
