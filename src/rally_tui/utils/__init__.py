"""Utility functions for rally-tui."""

from rally_tui.utils.html_to_text import extract_images_from_html, html_to_text
from rally_tui.utils.keybindings import (
    ACTION_REGISTRY,
    EMACS_KEYBINDINGS,
    VALID_PROFILES,
    VIM_KEYBINDINGS,
    KeyAction,
    KeyConflict,
    find_conflicts,
    format_key_for_display,
    get_action_categories,
    get_profile_keybindings,
    normalize_key,
    validate_key,
)
from rally_tui.utils.logging import get_logger, set_log_level, setup_logging
from rally_tui.utils.redacting_filter import RedactingFilter

__all__ = [
    "extract_images_from_html",
    "html_to_text",
    "get_logger",
    "set_log_level",
    "setup_logging",
    "RedactingFilter",
    # Keybinding exports
    "ACTION_REGISTRY",
    "EMACS_KEYBINDINGS",
    "VALID_PROFILES",
    "VIM_KEYBINDINGS",
    "KeyAction",
    "KeyConflict",
    "find_conflicts",
    "format_key_for_display",
    "get_action_categories",
    "get_profile_keybindings",
    "normalize_key",
    "validate_key",
]
