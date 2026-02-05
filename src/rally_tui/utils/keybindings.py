"""Keybinding utilities and action registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


class KeyAction(NamedTuple):
    """Represents a configurable keyboard action."""

    id: str
    description: str
    handler: str  # Method name in app/widget
    category: str
    show_in_footer: bool = True


# All configurable actions with metadata
ACTION_REGISTRY: dict[str, KeyAction] = {
    # Navigation actions (handled by TicketList widget)
    "navigation.down": KeyAction(
        "navigation.down", "Move down", "cursor_down", "Navigation", show_in_footer=False
    ),
    "navigation.up": KeyAction(
        "navigation.up", "Move up", "cursor_up", "Navigation", show_in_footer=False
    ),
    "navigation.top": KeyAction(
        "navigation.top", "Jump to top", "scroll_home", "Navigation", show_in_footer=False
    ),
    "navigation.bottom": KeyAction(
        "navigation.bottom", "Jump to bottom", "scroll_end", "Navigation", show_in_footer=False
    ),
    # Panel actions
    "panel.switch": KeyAction(
        "panel.switch", "Switch Panel", "switch_panel", "Panel", show_in_footer=False
    ),
    # Selection actions
    "selection.toggle": KeyAction(
        "selection.toggle", "Select", "toggle_select", "Selection", show_in_footer=False
    ),
    "selection.all": KeyAction(
        "selection.all", "Select All", "select_all", "Selection", show_in_footer=False
    ),
    # Work item actions
    "action.workitem": KeyAction("action.workitem", "Workitem", "quick_ticket", "Actions"),
    "action.state": KeyAction("action.state", "State", "set_state", "Actions"),
    "action.points": KeyAction("action.points", "Points", "set_points", "Actions"),
    "action.notes": KeyAction("action.notes", "Notes", "toggle_notes", "Actions"),
    "action.discuss": KeyAction("action.discuss", "Discuss", "open_discussions", "Actions"),
    "action.attachments": KeyAction(
        "action.attachments", "Attachments", "open_attachments", "Actions"
    ),
    "action.assign_owner": KeyAction("action.assign_owner", "Assign", "assign_owner", "Actions"),
    "action.copy_url": KeyAction(
        "action.copy_url", "Copy URL", "copy_ticket_url", "Actions", show_in_footer=False
    ),
    # Filter actions
    "action.search": KeyAction("action.search", "Search", "start_search", "Filters"),
    "action.sprint": KeyAction("action.sprint", "Sprint", "iteration_filter", "Filters"),
    "action.my_items": KeyAction("action.my_items", "My Items", "toggle_user_filter", "Filters"),
    "action.sort": KeyAction("action.sort", "Sort", "cycle_sort", "Filters"),
    "action.team": KeyAction("action.team", "Team", "team_breakdown", "Filters"),
    # View actions
    "action.wide_view": KeyAction("action.wide_view", "Wide", "toggle_wide_view", "View"),
    # Bulk actions
    "action.bulk": KeyAction("action.bulk", "Bulk", "bulk_actions", "Bulk"),
    # Cache actions
    "action.refresh": KeyAction("action.refresh", "Refresh", "refresh_cache", "Cache"),
    # App actions
    "action.settings": KeyAction("action.settings", "Settings", "open_settings", "App"),
    "action.keybindings": KeyAction("action.keybindings", "Keys", "open_keybindings", "App"),
    "action.theme": KeyAction("action.theme", "Theme", "toggle_theme", "App", show_in_footer=False),
    "action.quit": KeyAction("action.quit", "Quit", "quit", "App"),
}

# Vim-style keybindings (default)
VIM_KEYBINDINGS: dict[str, str] = {
    # Navigation
    "navigation.down": "j",
    "navigation.up": "k",
    "navigation.top": "g",
    "navigation.bottom": "G",
    # Panel
    "panel.switch": "tab",
    # Selection
    "selection.toggle": "space",
    "selection.all": "ctrl+a",
    # Work item actions
    "action.workitem": "w",
    "action.state": "s",
    "action.points": "p",
    "action.notes": "n",
    "action.discuss": "d",
    "action.attachments": "shift+a",
    "action.assign_owner": "a",
    "action.copy_url": "y",
    # Filters
    "action.search": "slash",
    "action.sprint": "i",
    "action.my_items": "u",
    "action.sort": "o",
    "action.team": "b",
    # View
    "action.wide_view": "v",
    # Bulk
    "action.bulk": "m",
    # Cache
    "action.refresh": "r",
    # App
    "action.settings": "f2",
    "action.keybindings": "f3",
    "action.theme": "t",
    "action.quit": "q",
}

# Emacs-style keybindings
EMACS_KEYBINDINGS: dict[str, str] = {
    # Navigation
    "navigation.down": "ctrl+n",
    "navigation.up": "ctrl+p",
    "navigation.top": "alt+shift+comma",
    "navigation.bottom": "alt+shift+period",
    # Panel
    "panel.switch": "tab",
    # Selection
    "selection.toggle": "space",
    "selection.all": "ctrl+a",
    # Work item actions
    "action.workitem": "ctrl+shift+n",
    "action.state": "ctrl+shift+s",
    "action.points": "ctrl+shift+p",
    "action.notes": "ctrl+shift+o",
    "action.discuss": "ctrl+d",
    "action.attachments": "ctrl+shift+t",
    "action.assign_owner": "ctrl+shift+a",
    "action.copy_url": "alt+w",
    # Filters
    "action.search": "ctrl+s",
    "action.sprint": "ctrl+i",
    "action.my_items": "ctrl+u",
    "action.sort": "ctrl+o",
    "action.team": "ctrl+b",
    # View
    "action.wide_view": "ctrl+v",
    # Bulk
    "action.bulk": "ctrl+m",
    # Cache
    "action.refresh": "ctrl+r",
    # App
    "action.settings": "f2",
    "action.keybindings": "f3",
    "action.theme": "ctrl+t",
    "action.quit": "ctrl+q",
}

# Valid profile names
VALID_PROFILES = ("vim", "emacs", "custom")


def get_profile_keybindings(profile: str) -> dict[str, str]:
    """Get keybindings for a profile.

    Args:
        profile: Profile name ('vim', 'emacs', or 'custom')

    Returns:
        Dictionary of action_id -> key mappings
    """
    if profile == "emacs":
        return dict(EMACS_KEYBINDINGS)
    return dict(VIM_KEYBINDINGS)


@dataclass
class KeyConflict:
    """Represents a keybinding conflict."""

    key: str
    action1: str
    action2: str


def find_conflicts(keybindings: dict[str, str]) -> list[KeyConflict]:
    """Find duplicate key assignments in keybindings.

    Args:
        keybindings: Dictionary of action_id -> key mappings

    Returns:
        List of KeyConflict for any duplicate keys
    """
    key_to_action: dict[str, str] = {}
    conflicts: list[KeyConflict] = []

    for action_id, key in keybindings.items():
        if key in key_to_action:
            conflicts.append(KeyConflict(key, key_to_action[key], action_id))
        else:
            key_to_action[key] = action_id

    return conflicts


def normalize_key(key: str) -> str:
    """Normalize a key string to consistent format.

    Args:
        key: Key string like "ctrl+s", "Ctrl+S", "ctrl+S"

    Returns:
        Normalized key string like "ctrl+s"
    """
    return key.lower().strip()


def format_key_for_display(key: str) -> str:
    """Format a key string for display.

    Args:
        key: Key string like "ctrl+s", "shift+g"

    Returns:
        Display string like "Ctrl+S", "G" (Shift+letter shows uppercase)
    """
    parts = key.split("+")
    formatted = []

    for part in parts:
        part = part.strip().lower()
        if part == "ctrl":
            formatted.append("Ctrl")
        elif part == "alt":
            formatted.append("Alt")
        elif part == "meta":
            formatted.append("Meta")
        elif part == "shift":
            # For shift+letter, we'll show just the uppercase letter
            continue
        elif part == "space":
            formatted.append("Space")
        elif part == "tab":
            formatted.append("Tab")
        elif part == "slash":
            formatted.append("/")
        elif len(part) == 1:
            # Single letter - uppercase if shift was in the combo
            if "shift" in key.lower():
                formatted.append(part.upper())
            else:
                formatted.append(part)
        else:
            # Function keys, etc.
            formatted.append(part.upper())

    return "+".join(formatted) if len(formatted) > 1 else formatted[0] if formatted else key


def validate_key(key: str) -> bool:
    """Validate a key string.

    Args:
        key: Key string to validate

    Returns:
        True if key is valid, False otherwise
    """
    if not key or not isinstance(key, str):
        return False

    normalized = normalize_key(key)
    parts = normalized.split("+")

    valid_modifiers = {"ctrl", "alt", "meta", "shift"}
    valid_special_keys = {
        "space",
        "tab",
        "enter",
        "escape",
        "backspace",
        "delete",
        "up",
        "down",
        "left",
        "right",
        "home",
        "end",
        "pageup",
        "pagedown",
        "f1",
        "f2",
        "f3",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8",
        "f9",
        "f10",
        "f11",
        "f12",
        "slash",
        "backslash",
        "comma",
        "period",
        "semicolon",
        "quote",
        "bracketleft",
        "bracketright",
        "minus",
        "equal",
    }

    modifiers = []
    key_part = None

    for part in parts:
        if part in valid_modifiers:
            modifiers.append(part)
        elif key_part is None:
            key_part = part
        else:
            # Multiple non-modifier keys
            return False

    if key_part is None:
        # Only modifiers, no actual key
        return False

    # Key must be single char or valid special key
    if len(key_part) == 1 or key_part in valid_special_keys:
        return True

    return False


def get_action_categories() -> dict[str, list[str]]:
    """Get actions grouped by category.

    Returns:
        Dictionary of category -> list of action_ids
    """
    categories: dict[str, list[str]] = {}

    for action_id, action in ACTION_REGISTRY.items():
        if action.category not in categories:
            categories[action.category] = []
        categories[action.category].append(action_id)

    return categories
