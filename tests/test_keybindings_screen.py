"""Tests for KeybindingsScreen."""

from pathlib import Path

import pytest

from rally_tui.screens.keybindings_screen import (
    PROFILE_OPTIONS,
    KeybindingRow,
    KeybindingsScreen,
)
from rally_tui.user_settings import UserSettings
from rally_tui.utils.keybindings import VIM_KEYBINDINGS


@pytest.fixture
def mock_user_settings(tmp_path: Path, monkeypatch) -> UserSettings:
    """Create UserSettings with temp config file."""
    monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
    return UserSettings()


class TestKeybindingRow:
    """Tests for KeybindingRow widget."""

    def test_keybinding_row_has_action_id(self) -> None:
        """Row should store action_id."""
        row = KeybindingRow("navigation.down", "Move down", "j")
        assert row.action_id == "navigation.down"

    def test_keybinding_row_has_action_name(self) -> None:
        """Row should store action_name."""
        row = KeybindingRow("navigation.down", "Move down", "j")
        assert row.action_name == "Move down"

    def test_keybinding_row_has_key(self) -> None:
        """Row should store key."""
        row = KeybindingRow("navigation.down", "Move down", "j")
        assert row.key == "j"

    def test_keybinding_row_conflict_flag(self) -> None:
        """Row should track conflict flag."""
        row = KeybindingRow("navigation.down", "Move down", "j", has_conflict=True)
        assert row.has_conflict is True

    def test_keybinding_row_default_no_conflict(self) -> None:
        """Row should default to no conflict."""
        row = KeybindingRow("navigation.down", "Move down", "j")
        assert row.has_conflict is False


class TestProfileOptions:
    """Tests for profile options."""

    def test_vim_profile_available(self) -> None:
        """Vim profile should be available."""
        profiles = dict((v, k) for k, v in PROFILE_OPTIONS)
        assert "vim" in profiles

    def test_emacs_profile_available(self) -> None:
        """Emacs profile should be available."""
        profiles = dict((v, k) for k, v in PROFILE_OPTIONS)
        assert "emacs" in profiles

    def test_custom_profile_available(self) -> None:
        """Custom profile should be available."""
        profiles = dict((v, k) for k, v in PROFILE_OPTIONS)
        assert "custom" in profiles


class TestKeybindingsScreenInit:
    """Tests for KeybindingsScreen initialization."""

    def test_screen_stores_settings(self, mock_user_settings: UserSettings) -> None:
        """Screen should store settings reference."""
        screen = KeybindingsScreen(mock_user_settings)
        assert screen.settings is mock_user_settings

    def test_screen_loads_temp_bindings(self, mock_user_settings: UserSettings) -> None:
        """Screen should load temp bindings from settings."""
        screen = KeybindingsScreen(mock_user_settings)
        assert screen._temp_bindings == mock_user_settings.keybindings

    def test_screen_starts_not_editing(self, mock_user_settings: UserSettings) -> None:
        """Screen should start with no action being edited."""
        screen = KeybindingsScreen(mock_user_settings)
        assert screen._editing_action is None

    def test_screen_starts_unchanged(self, mock_user_settings: UserSettings) -> None:
        """Screen should start with changed=False."""
        screen = KeybindingsScreen(mock_user_settings)
        assert screen._changed is False


class TestKeybindingsScreenKeyString:
    """Tests for key string building."""

    def test_build_key_string_single_char(self, mock_user_settings: UserSettings) -> None:
        """Should build key string for single character."""
        screen = KeybindingsScreen(mock_user_settings)

        class MockEvent:
            key = "j"

        result = screen._build_key_string(MockEvent())
        assert result == "j"

    def test_build_key_string_function_key(self, mock_user_settings: UserSettings) -> None:
        """Should build key string for function key."""
        screen = KeybindingsScreen(mock_user_settings)

        class MockEvent:
            key = "f3"

        result = screen._build_key_string(MockEvent())
        assert result == "f3"

    def test_build_key_string_special_key(self, mock_user_settings: UserSettings) -> None:
        """Should build key string for special key."""
        screen = KeybindingsScreen(mock_user_settings)

        class MockEvent:
            key = "space"

        result = screen._build_key_string(MockEvent())
        assert result == "space"

    def test_build_key_string_modifier_only_returns_none(
        self, mock_user_settings: UserSettings
    ) -> None:
        """Should return None for modifier-only keys."""
        screen = KeybindingsScreen(mock_user_settings)

        class MockEvent:
            key = "ctrl"

        result = screen._build_key_string(MockEvent())
        assert result is None

    def test_build_key_string_ctrl_combo(self, mock_user_settings: UserSettings) -> None:
        """Should handle ctrl+key combos."""
        screen = KeybindingsScreen(mock_user_settings)

        class MockEvent:
            key = "ctrl+s"

        result = screen._build_key_string(MockEvent())
        assert result == "ctrl+s"

    def test_build_key_string_tab(self, mock_user_settings: UserSettings) -> None:
        """Should handle tab key."""
        screen = KeybindingsScreen(mock_user_settings)

        class MockEvent:
            key = "tab"

        result = screen._build_key_string(MockEvent())
        assert result == "tab"

    def test_build_key_string_escape(self, mock_user_settings: UserSettings) -> None:
        """Should handle escape key."""
        screen = KeybindingsScreen(mock_user_settings)

        class MockEvent:
            key = "escape"

        result = screen._build_key_string(MockEvent())
        assert result == "escape"

    def test_build_key_string_enter(self, mock_user_settings: UserSettings) -> None:
        """Should handle enter key."""
        screen = KeybindingsScreen(mock_user_settings)

        class MockEvent:
            key = "enter"

        result = screen._build_key_string(MockEvent())
        assert result == "enter"


class TestKeybindingsScreenTempBindings:
    """Tests for temporary bindings management."""

    def test_modify_temp_bindings(self, mock_user_settings: UserSettings) -> None:
        """Should be able to modify temp bindings."""
        screen = KeybindingsScreen(mock_user_settings)
        screen._temp_bindings["navigation.down"] = "x"
        assert screen._temp_bindings["navigation.down"] == "x"
        # Original settings unchanged
        assert mock_user_settings.get_keybinding("navigation.down") == "j"

    def test_reset_restores_vim_defaults(self, mock_user_settings: UserSettings) -> None:
        """Reset should restore vim defaults."""
        screen = KeybindingsScreen(mock_user_settings)
        screen._temp_bindings["navigation.down"] = "x"
        screen._temp_bindings = dict(VIM_KEYBINDINGS)
        assert screen._temp_bindings["navigation.down"] == "j"


class TestKeybindingsScreenEditing:
    """Tests for editing mode."""

    def test_start_editing_sets_action(self, mock_user_settings: UserSettings) -> None:
        """Start editing should set the editing action."""
        screen = KeybindingsScreen(mock_user_settings)
        screen._editing_action = "navigation.down"
        assert screen._editing_action == "navigation.down"

    def test_stop_editing_clears_action(self, mock_user_settings: UserSettings) -> None:
        """Stop editing should clear the editing action."""
        screen = KeybindingsScreen(mock_user_settings)
        screen._editing_action = "navigation.down"
        screen._editing_action = None
        assert screen._editing_action is None
