"""Tests for the ConfigScreen."""

from pathlib import Path

import pytest
from textual.widgets import Button, Input, Select

from rally_tui.app import RallyTUI
from rally_tui.screens import ConfigScreen
from rally_tui.screens.config_screen import AVAILABLE_THEMES, LOG_LEVELS, ConfigData
from rally_tui.user_settings import UserSettings


@pytest.fixture
def mock_settings(tmp_path: Path, monkeypatch) -> UserSettings:
    """Create mock UserSettings with test values."""
    monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
    settings = UserSettings()
    settings.theme_name = "textual-dark"
    settings.log_level = "INFO"
    settings.parent_options = ["F111", "F222", "F333"]
    return settings


class TestConfigScreenBasic:
    """Basic tests for ConfigScreen."""

    async def test_config_screen_displays_title(self, mock_settings: UserSettings) -> None:
        """ConfigScreen should display Settings title."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            title = app.screen.query_one("#config-title")
            assert "Settings" in str(title.render())

    async def test_config_screen_displays_config_path(self, mock_settings: UserSettings) -> None:
        """ConfigScreen should display the config file path."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            path_label = app.screen.query_one("#config-path")
            assert "config.json" in str(path_label.render())

    async def test_config_screen_has_theme_selector(self, mock_settings: UserSettings) -> None:
        """ConfigScreen should have a theme selector."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            theme_select = app.screen.query_one("#theme-select", Select)
            assert theme_select is not None
            assert theme_select.value == "textual-dark"

    async def test_config_screen_has_log_level_selector(self, mock_settings: UserSettings) -> None:
        """ConfigScreen should have a log level selector."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            log_select = app.screen.query_one("#log-level-select", Select)
            assert log_select is not None
            assert log_select.value == "INFO"

    async def test_config_screen_has_parent_inputs(self, mock_settings: UserSettings) -> None:
        """ConfigScreen should have 3 parent option input fields."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            parent1 = app.screen.query_one("#parent-1", Input)
            parent2 = app.screen.query_one("#parent-2", Input)
            parent3 = app.screen.query_one("#parent-3", Input)

            assert parent1.value == "F111"
            assert parent2.value == "F222"
            assert parent3.value == "F333"

    async def test_config_screen_has_save_button(self, mock_settings: UserSettings) -> None:
        """ConfigScreen should have a Save button."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            save_btn = app.screen.query_one("#btn-save", Button)
            assert save_btn is not None

    async def test_config_screen_has_cancel_button(self, mock_settings: UserSettings) -> None:
        """ConfigScreen should have a Cancel button."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            cancel_btn = app.screen.query_one("#btn-cancel", Button)
            assert cancel_btn is not None


class TestConfigScreenNavigation:
    """Tests for ConfigScreen navigation."""

    async def test_escape_cancels_without_saving(self, mock_settings: UserSettings) -> None:
        """Pressing Escape should close without saving."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            # Verify we're on ConfigScreen
            assert app.screen.__class__.__name__ == "ConfigScreen"

            # Press escape
            await pilot.press("escape")
            await pilot.pause()

            # Should be back to main screen
            assert app.screen.__class__.__name__ != "ConfigScreen"

    async def test_f2_key_opens_settings(self, mock_settings: UserSettings) -> None:
        """Pressing F2 should open settings screen."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            # Press F2 to open settings
            await pilot.press("f2")
            await pilot.pause()

            # Should be on ConfigScreen
            assert app.screen.__class__.__name__ == "ConfigScreen"


class TestConfigScreenSaving:
    """Tests for ConfigScreen save functionality."""

    async def test_save_button_saves_settings(self, mock_settings: UserSettings) -> None:
        """Clicking Save button should save settings."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            # Click save button
            save_btn = app.screen.query_one("#btn-save", Button)
            save_btn.press()
            await pilot.pause()

            # Should be back to main screen
            assert app.screen.__class__.__name__ != "ConfigScreen"

    async def test_ctrl_s_saves_settings(self, mock_settings: UserSettings) -> None:
        """Pressing Ctrl+S should save settings."""
        app = RallyTUI(show_splash=False, user_settings=mock_settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(mock_settings))
            await pilot.pause()

            # Press Ctrl+S
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Should be back to main screen
            assert app.screen.__class__.__name__ != "ConfigScreen"

    async def test_save_persists_theme_change(self, tmp_path: Path, monkeypatch) -> None:
        """Saving should persist theme changes."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        settings = UserSettings()

        app = RallyTUI(show_splash=False, user_settings=settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(settings))
            await pilot.pause()

            # Change theme (simulate selecting a different theme)
            theme_select = app.screen.query_one("#theme-select", Select)
            theme_select.value = "nord"
            await pilot.pause()

            # Save
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Verify theme was saved
            assert settings.theme_name == "nord"

    async def test_save_persists_log_level_change(self, tmp_path: Path, monkeypatch) -> None:
        """Saving should persist log level changes."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        settings = UserSettings()

        app = RallyTUI(show_splash=False, user_settings=settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(settings))
            await pilot.pause()

            # Change log level
            log_select = app.screen.query_one("#log-level-select", Select)
            log_select.value = "DEBUG"
            await pilot.pause()

            # Save
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Verify log level was saved
            assert settings.log_level == "DEBUG"

    async def test_save_persists_parent_options(self, tmp_path: Path, monkeypatch) -> None:
        """Saving should persist parent options changes."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        settings = UserSettings()

        app = RallyTUI(show_splash=False, user_settings=settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(settings))
            await pilot.pause()

            # Change parent options
            parent1 = app.screen.query_one("#parent-1", Input)
            parent2 = app.screen.query_one("#parent-2", Input)
            parent3 = app.screen.query_one("#parent-3", Input)

            parent1.value = "F99999"
            parent2.value = "F88888"
            parent3.value = "F77777"
            await pilot.pause()

            # Save
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Verify parent options were saved
            assert settings.parent_options == ["F99999", "F88888", "F77777"]

    async def test_empty_parent_options_filtered(self, tmp_path: Path, monkeypatch) -> None:
        """Empty parent option fields should be filtered out."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        settings = UserSettings()
        settings.parent_options = ["F111", "F222", "F333"]

        app = RallyTUI(show_splash=False, user_settings=settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(settings))
            await pilot.pause()

            # Clear second and third parent options
            parent2 = app.screen.query_one("#parent-2", Input)
            parent3 = app.screen.query_one("#parent-3", Input)
            parent2.value = ""
            parent3.value = ""
            await pilot.pause()

            # Save
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Only non-empty values should be saved
            assert settings.parent_options == ["F111"]

    async def test_parent_options_uppercased(self, tmp_path: Path, monkeypatch) -> None:
        """Parent options should be uppercased on save."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        settings = UserSettings()

        app = RallyTUI(show_splash=False, user_settings=settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(settings))
            await pilot.pause()

            # Enter lowercase
            parent1 = app.screen.query_one("#parent-1", Input)
            parent1.value = "f12345"
            await pilot.pause()

            # Save
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Should be uppercased
            assert "F12345" in settings.parent_options


class TestConfigScreenProperty:
    """Tests for ConfigScreen properties."""

    def test_settings_property(self, mock_settings: UserSettings) -> None:
        """ConfigScreen should expose settings property."""
        screen = ConfigScreen(mock_settings)
        assert screen.settings == mock_settings


class TestConfigData:
    """Tests for ConfigData dataclass."""

    def test_config_data_creation(self) -> None:
        """ConfigData should hold theme, log_level, and parent_options."""
        data = ConfigData(
            theme_name="nord",
            log_level="DEBUG",
            parent_options=["F111", "F222"],
        )
        assert data.theme_name == "nord"
        assert data.log_level == "DEBUG"
        assert data.parent_options == ["F111", "F222"]


class TestConfigScreenConstants:
    """Tests for ConfigScreen constants."""

    def test_available_themes_not_empty(self) -> None:
        """AVAILABLE_THEMES should have options."""
        assert len(AVAILABLE_THEMES) > 0

    def test_available_themes_has_textual_dark(self) -> None:
        """AVAILABLE_THEMES should include textual-dark."""
        theme_values = [t[0] for t in AVAILABLE_THEMES]
        assert "textual-dark" in theme_values

    def test_log_levels_not_empty(self) -> None:
        """LOG_LEVELS should have options."""
        assert len(LOG_LEVELS) > 0

    def test_log_levels_has_info(self) -> None:
        """LOG_LEVELS should include INFO."""
        level_values = [level[0] for level in LOG_LEVELS]
        assert "INFO" in level_values


class TestConfigScreenEmptyParentOptions:
    """Tests for ConfigScreen with empty parent options."""

    async def test_handles_empty_parent_options(self, tmp_path: Path, monkeypatch) -> None:
        """ConfigScreen should handle settings with empty parent_options."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        settings = UserSettings()
        settings.parent_options = []

        app = RallyTUI(show_splash=False, user_settings=settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(settings))
            await pilot.pause()

            # Should have empty input fields
            parent1 = app.screen.query_one("#parent-1", Input)
            parent2 = app.screen.query_one("#parent-2", Input)
            parent3 = app.screen.query_one("#parent-3", Input)

            assert parent1.value == ""
            assert parent2.value == ""
            assert parent3.value == ""

    async def test_handles_partial_parent_options(self, tmp_path: Path, monkeypatch) -> None:
        """ConfigScreen should handle settings with fewer than 3 parent_options."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        settings = UserSettings()
        settings.parent_options = ["F111"]

        app = RallyTUI(show_splash=False, user_settings=settings)
        async with app.run_test() as pilot:
            await app.push_screen(ConfigScreen(settings))
            await pilot.pause()

            parent1 = app.screen.query_one("#parent-1", Input)
            parent2 = app.screen.query_one("#parent-2", Input)
            parent3 = app.screen.query_one("#parent-3", Input)

            assert parent1.value == "F111"
            assert parent2.value == ""
            assert parent3.value == ""
