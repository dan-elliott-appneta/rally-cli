"""Tests for keybinding utilities."""

from rally_tui.utils.keybindings import (
    ACTION_REGISTRY,
    EMACS_KEYBINDINGS,
    VALID_PROFILES,
    VIM_KEYBINDINGS,
    find_conflicts,
    format_key_for_display,
    get_action_categories,
    get_profile_keybindings,
    normalize_key,
    validate_key,
)


class TestActionRegistry:
    """Tests for ACTION_REGISTRY."""

    def test_registry_not_empty(self) -> None:
        """Registry should have actions."""
        assert len(ACTION_REGISTRY) > 0

    def test_all_actions_have_required_fields(self) -> None:
        """All actions should have id, description, handler, category."""
        for action_id, action in ACTION_REGISTRY.items():
            assert action.id == action_id
            assert action.description
            assert action.handler
            assert action.category

    def test_navigation_actions_exist(self) -> None:
        """Navigation actions should be defined."""
        assert "navigation.down" in ACTION_REGISTRY
        assert "navigation.up" in ACTION_REGISTRY
        assert "navigation.top" in ACTION_REGISTRY
        assert "navigation.bottom" in ACTION_REGISTRY

    def test_action_actions_exist(self) -> None:
        """Main actions should be defined."""
        assert "action.quit" in ACTION_REGISTRY
        assert "action.search" in ACTION_REGISTRY
        assert "action.state" in ACTION_REGISTRY
        assert "action.points" in ACTION_REGISTRY
        assert "action.workitem" in ACTION_REGISTRY

    def test_action_categories(self) -> None:
        """Actions should have valid categories."""
        valid_categories = {
            "Navigation",
            "Panel",
            "Selection",
            "Actions",
            "Filters",
            "View",
            "Bulk",
            "Cache",
            "App",
        }
        for action in ACTION_REGISTRY.values():
            assert action.category in valid_categories


class TestVimKeybindings:
    """Tests for VIM_KEYBINDINGS."""

    def test_all_actions_have_keybinding(self) -> None:
        """All actions in registry should have a vim keybinding."""
        for action_id in ACTION_REGISTRY:
            assert action_id in VIM_KEYBINDINGS, f"Missing vim keybinding for {action_id}"

    def test_vim_navigation_keys(self) -> None:
        """Vim uses j/k for navigation."""
        assert VIM_KEYBINDINGS["navigation.down"] == "j"
        assert VIM_KEYBINDINGS["navigation.up"] == "k"

    def test_vim_quit_key(self) -> None:
        """Vim uses q for quit."""
        assert VIM_KEYBINDINGS["action.quit"] == "q"

    def test_vim_search_key(self) -> None:
        """Vim uses / for search."""
        assert VIM_KEYBINDINGS["action.search"] == "slash"


class TestEmacsKeybindings:
    """Tests for EMACS_KEYBINDINGS."""

    def test_all_actions_have_keybinding(self) -> None:
        """All actions in registry should have an emacs keybinding."""
        for action_id in ACTION_REGISTRY:
            assert action_id in EMACS_KEYBINDINGS, f"Missing emacs keybinding for {action_id}"

    def test_emacs_navigation_keys(self) -> None:
        """Emacs uses ctrl+n/p for navigation."""
        assert EMACS_KEYBINDINGS["navigation.down"] == "ctrl+n"
        assert EMACS_KEYBINDINGS["navigation.up"] == "ctrl+p"

    def test_emacs_quit_key(self) -> None:
        """Emacs uses ctrl+q for quit."""
        assert EMACS_KEYBINDINGS["action.quit"] == "ctrl+q"

    def test_emacs_search_key(self) -> None:
        """Emacs uses ctrl+s for search."""
        assert EMACS_KEYBINDINGS["action.search"] == "ctrl+s"


class TestGetProfileKeybindings:
    """Tests for get_profile_keybindings."""

    def test_get_vim_profile(self) -> None:
        """Should return vim keybindings."""
        bindings = get_profile_keybindings("vim")
        assert bindings == VIM_KEYBINDINGS

    def test_get_emacs_profile(self) -> None:
        """Should return emacs keybindings."""
        bindings = get_profile_keybindings("emacs")
        assert bindings == EMACS_KEYBINDINGS

    def test_get_custom_defaults_to_vim(self) -> None:
        """Custom profile should default to vim."""
        bindings = get_profile_keybindings("custom")
        assert bindings == VIM_KEYBINDINGS

    def test_get_invalid_defaults_to_vim(self) -> None:
        """Invalid profile should default to vim."""
        bindings = get_profile_keybindings("invalid")
        assert bindings == VIM_KEYBINDINGS

    def test_returns_copy(self) -> None:
        """Should return a copy, not the original."""
        bindings = get_profile_keybindings("vim")
        bindings["action.quit"] = "changed"
        assert VIM_KEYBINDINGS["action.quit"] == "q"


class TestFindConflicts:
    """Tests for find_conflicts."""

    def test_no_conflicts_in_vim(self) -> None:
        """Vim keybindings should have no conflicts."""
        conflicts = find_conflicts(VIM_KEYBINDINGS)
        assert len(conflicts) == 0

    def test_no_conflicts_in_emacs(self) -> None:
        """Emacs keybindings should have no conflicts."""
        conflicts = find_conflicts(EMACS_KEYBINDINGS)
        assert len(conflicts) == 0

    def test_detects_conflict(self) -> None:
        """Should detect when two actions have same key."""
        bindings = {
            "action.a": "q",
            "action.b": "w",
            "action.c": "q",  # Conflict with action.a
        }
        conflicts = find_conflicts(bindings)
        assert len(conflicts) == 1
        assert conflicts[0].key == "q"
        assert conflicts[0].action1 == "action.a"
        assert conflicts[0].action2 == "action.c"

    def test_detects_multiple_conflicts(self) -> None:
        """Should detect multiple conflicts."""
        bindings = {
            "action.a": "q",
            "action.b": "q",
            "action.c": "w",
            "action.d": "w",
        }
        conflicts = find_conflicts(bindings)
        assert len(conflicts) == 2


class TestNormalizeKey:
    """Tests for normalize_key."""

    def test_lowercase(self) -> None:
        """Should lowercase the key."""
        assert normalize_key("Q") == "q"
        assert normalize_key("Ctrl+S") == "ctrl+s"

    def test_strips_whitespace(self) -> None:
        """Should strip whitespace."""
        assert normalize_key("  q  ") == "q"
        assert normalize_key(" ctrl+s ") == "ctrl+s"

    def test_already_normalized(self) -> None:
        """Already normalized keys should stay the same."""
        assert normalize_key("q") == "q"
        assert normalize_key("ctrl+s") == "ctrl+s"


class TestFormatKeyForDisplay:
    """Tests for format_key_for_display."""

    def test_simple_key(self) -> None:
        """Simple keys should be lowercase."""
        assert format_key_for_display("q") == "q"
        assert format_key_for_display("j") == "j"

    def test_ctrl_modifier(self) -> None:
        """Ctrl modifier should be capitalized."""
        assert format_key_for_display("ctrl+s") == "Ctrl+s"
        assert format_key_for_display("ctrl+q") == "Ctrl+q"

    def test_shift_shows_uppercase(self) -> None:
        """Shift+letter should show uppercase letter."""
        assert format_key_for_display("shift+g") == "G"

    def test_special_keys(self) -> None:
        """Special keys should format nicely."""
        assert format_key_for_display("space") == "Space"
        assert format_key_for_display("tab") == "Tab"
        assert format_key_for_display("slash") == "/"

    def test_function_keys(self) -> None:
        """Function keys should be uppercase."""
        assert format_key_for_display("f2") == "F2"
        assert format_key_for_display("f12") == "F12"


class TestValidateKey:
    """Tests for validate_key."""

    def test_single_letter(self) -> None:
        """Single letters are valid."""
        assert validate_key("q") is True
        assert validate_key("j") is True
        assert validate_key("G") is True

    def test_with_ctrl(self) -> None:
        """Ctrl combinations are valid."""
        assert validate_key("ctrl+s") is True
        assert validate_key("ctrl+q") is True

    def test_with_alt(self) -> None:
        """Alt combinations are valid."""
        assert validate_key("alt+x") is True

    def test_with_shift(self) -> None:
        """Shift combinations are valid."""
        assert validate_key("shift+g") is True

    def test_function_keys(self) -> None:
        """Function keys are valid."""
        assert validate_key("f2") is True
        assert validate_key("f12") is True

    def test_special_keys(self) -> None:
        """Special keys are valid."""
        assert validate_key("space") is True
        assert validate_key("tab") is True
        assert validate_key("enter") is True
        assert validate_key("escape") is True
        assert validate_key("slash") is True

    def test_empty_invalid(self) -> None:
        """Empty strings are invalid."""
        assert validate_key("") is False
        assert validate_key(None) is False  # type: ignore

    def test_only_modifier_invalid(self) -> None:
        """Only modifiers are invalid."""
        assert validate_key("ctrl") is False
        assert validate_key("ctrl+") is False

    def test_invalid_key(self) -> None:
        """Invalid key names are rejected."""
        assert validate_key("invalid") is False
        assert validate_key("ctrl+invalid") is False


class TestGetActionCategories:
    """Tests for get_action_categories."""

    def test_returns_categories(self) -> None:
        """Should return categories with actions."""
        categories = get_action_categories()
        assert len(categories) > 0

    def test_navigation_category(self) -> None:
        """Navigation category should exist with actions."""
        categories = get_action_categories()
        assert "Navigation" in categories
        assert "navigation.down" in categories["Navigation"]
        assert "navigation.up" in categories["Navigation"]

    def test_actions_category(self) -> None:
        """Actions category should exist."""
        categories = get_action_categories()
        assert "Actions" in categories
        assert len(categories["Actions"]) > 0

    def test_all_actions_categorized(self) -> None:
        """All actions should be in some category."""
        categories = get_action_categories()
        all_categorized = []
        for actions in categories.values():
            all_categorized.extend(actions)

        for action_id in ACTION_REGISTRY:
            assert action_id in all_categorized


class TestValidProfiles:
    """Tests for VALID_PROFILES."""

    def test_contains_vim(self) -> None:
        """Vim should be a valid profile."""
        assert "vim" in VALID_PROFILES

    def test_contains_emacs(self) -> None:
        """Emacs should be a valid profile."""
        assert "emacs" in VALID_PROFILES

    def test_contains_custom(self) -> None:
        """Custom should be a valid profile."""
        assert "custom" in VALID_PROFILES
