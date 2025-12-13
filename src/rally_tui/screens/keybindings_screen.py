"""Keybindings configuration screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Select, Static

from rally_tui.user_settings import UserSettings
from rally_tui.utils.keybindings import (
    ACTION_REGISTRY,
    find_conflicts,
    format_key_for_display,
    get_action_categories,
)

# Profile options for selector
PROFILE_OPTIONS: list[tuple[str, str]] = [
    ("Vim (Default)", "vim"),
    ("Emacs", "emacs"),
    ("Custom", "custom"),
]


class KeybindingRow(Static):
    """A single keybinding row showing action and current key."""

    DEFAULT_CSS = """
    KeybindingRow {
        height: 1;
        padding: 0 1;
    }

    KeybindingRow:hover {
        background: $accent 20%;
    }

    KeybindingRow.selected {
        background: $accent 40%;
    }

    KeybindingRow .action-name {
        width: 25;
    }

    KeybindingRow .key-display {
        width: 15;
        text-align: right;
    }

    KeybindingRow.conflict .key-display {
        color: $error;
    }
    """

    def __init__(
        self,
        action_id: str,
        action_name: str,
        key: str,
        has_conflict: bool = False,
    ) -> None:
        super().__init__()
        self.action_id = action_id
        self.action_name = action_name
        self.key = key
        self.has_conflict = has_conflict

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self.action_name, classes="action-name")
            yield Label(
                format_key_for_display(self.key),
                classes="key-display",
            )

    def on_mount(self) -> None:
        if self.has_conflict:
            self.add_class("conflict")

    def update_key(self, key: str, has_conflict: bool = False) -> None:
        """Update the displayed key."""
        self.key = key
        self.has_conflict = has_conflict
        key_label = self.query_one(".key-display", Label)
        key_label.update(format_key_for_display(key))
        if has_conflict:
            self.add_class("conflict")
        else:
            self.remove_class("conflict")


class KeybindingsScreen(Screen[bool]):
    """Screen for viewing and editing keybindings.

    Returns True if keybindings were changed, False otherwise.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    DEFAULT_CSS = """
    KeybindingsScreen {
        background: $background;
    }

    #keybindings-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #profile-row {
        height: 3;
        padding: 0 2;
        align: left middle;
    }

    #profile-row Label {
        padding-right: 1;
    }

    #profile-select {
        width: 25;
    }

    #keybindings-content {
        padding: 0 2;
        height: 1fr;
    }

    .category-header {
        text-style: bold;
        color: $text;
        margin-top: 1;
        margin-bottom: 0;
        padding: 0 1;
        background: $surface;
    }

    #conflict-warning {
        color: $error;
        text-align: center;
        padding: 0 1;
        display: none;
    }

    #conflict-warning.visible {
        display: block;
    }

    #button-row {
        align: center middle;
        padding: 1;
        height: 3;
    }

    #button-row Button {
        margin: 0 1;
        min-width: 14;
    }

    #btn-save {
        background: $success;
    }

    #btn-reset {
        background: $warning;
    }

    #instructions {
        text-align: center;
        color: $text-muted;
        padding: 0 1;
    }

    #editing-prompt {
        text-align: center;
        color: $warning;
        text-style: bold;
        padding: 1;
        display: none;
    }

    #editing-prompt.visible {
        display: block;
    }
    """

    def __init__(
        self,
        settings: UserSettings,
        name: str | None = None,
    ) -> None:
        """Initialize the keybindings screen.

        Args:
            settings: The user settings to edit.
            name: Optional screen name.
        """
        super().__init__(name=name)
        self._settings = settings
        self._temp_bindings = dict(settings.keybindings)
        self._editing_action: str | None = None
        self._changed = False

    @property
    def settings(self) -> UserSettings:
        """Get the user settings being edited."""
        return self._settings

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Keyboard Shortcuts", id="keybindings-title")

        # Profile selector
        with Horizontal(id="profile-row"):
            yield Label("Profile:")
            yield Select(
                [(name, value) for name, value in PROFILE_OPTIONS],
                value=self._settings.keybinding_profile,
                id="profile-select",
                allow_blank=False,
            )

        # Conflict warning
        yield Static(
            "Warning: Duplicate keybindings detected!",
            id="conflict-warning",
        )

        # Editing prompt
        yield Static(
            "Press any key to set binding, Esc to cancel",
            id="editing-prompt",
        )

        # Keybindings list
        with VerticalScroll(id="keybindings-content"):
            categories = get_action_categories()
            conflicts = find_conflicts(self._temp_bindings)
            conflict_keys = {c.key for c in conflicts}

            for category, action_ids in categories.items():
                yield Label(category, classes="category-header")
                for action_id in action_ids:
                    if action_id in ACTION_REGISTRY:
                        action = ACTION_REGISTRY[action_id]
                        key = self._temp_bindings.get(action_id, "")
                        has_conflict = key in conflict_keys
                        yield KeybindingRow(
                            action_id=action_id,
                            action_name=action.description,
                            key=key,
                            has_conflict=has_conflict,
                        )

        # Instructions
        yield Static(
            "Click a row to edit keybinding",
            id="instructions",
        )

        # Buttons
        with Horizontal(id="button-row"):
            yield Button("Save (Ctrl+S)", id="btn-save", variant="success")
            yield Button("Reset", id="btn-reset", variant="warning")
            yield Button("Cancel (Esc)", id="btn-cancel", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Update conflict warning on mount."""
        self._update_conflict_warning()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle profile change."""
        if event.select.id == "profile-select" and event.value:
            profile = str(event.value)
            if profile in ("vim", "emacs"):
                # Load profile defaults
                from rally_tui.utils.keybindings import get_profile_keybindings

                self._temp_bindings = get_profile_keybindings(profile)
                self._refresh_all_rows()
                self._changed = True

    def on_click(self, event) -> None:
        """Handle clicks on keybinding rows."""
        # Find if we clicked on a KeybindingRow
        widget = event.widget
        while widget is not None:
            if isinstance(widget, KeybindingRow):
                self._start_editing(widget.action_id)
                return
            widget = widget.parent

    def _start_editing(self, action_id: str) -> None:
        """Start editing a keybinding."""
        self._editing_action = action_id

        # Highlight the row being edited
        for row in self.query(KeybindingRow):
            if row.action_id == action_id:
                row.add_class("selected")
            else:
                row.remove_class("selected")

        # Show editing prompt
        prompt = self.query_one("#editing-prompt", Static)
        prompt.add_class("visible")

        # Hide instructions
        instructions = self.query_one("#instructions", Static)
        instructions.styles.display = "none"

    def _stop_editing(self) -> None:
        """Stop editing mode."""
        self._editing_action = None

        # Remove highlight
        for row in self.query(KeybindingRow):
            row.remove_class("selected")

        # Hide editing prompt
        prompt = self.query_one("#editing-prompt", Static)
        prompt.remove_class("visible")

        # Show instructions
        instructions = self.query_one("#instructions", Static)
        instructions.styles.display = "block"

    def on_key(self, event) -> None:
        """Handle key presses for editing."""
        if self._editing_action is None:
            return

        # Cancel editing on Escape
        if event.key == "escape":
            self._stop_editing()
            event.prevent_default()
            return

        # Build key string
        key_str = self._build_key_string(event)
        if key_str:
            self._temp_bindings[self._editing_action] = key_str
            self._changed = True

            # Update the row
            for row in self.query(KeybindingRow):
                if row.action_id == self._editing_action:
                    conflicts = find_conflicts(self._temp_bindings)
                    conflict_keys = {c.key for c in conflicts}
                    row.update_key(key_str, key_str in conflict_keys)
                    break

            # Update profile to custom
            profile_select = self.query_one("#profile-select", Select)
            profile_select.value = "custom"

            self._stop_editing()
            self._update_conflict_warning()
            event.prevent_default()

    def _build_key_string(self, event) -> str | None:
        """Build a key string from key event."""
        key = event.key

        # Skip pure modifier presses
        if key in ("ctrl", "alt", "meta", "shift"):
            return None

        # Handle special key names
        key_map = {
            "enter": "enter",
            "escape": "escape",
            "tab": "tab",
            "space": "space",
            "backspace": "backspace",
            "delete": "delete",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "home": "home",
            "end": "end",
            "pageup": "pageup",
            "pagedown": "pagedown",
        }

        # Check if it's a named key
        if key.lower() in key_map:
            base_key = key_map[key.lower()]
        elif key.startswith("f") and key[1:].isdigit():
            base_key = key.lower()
        elif len(key) == 1:
            base_key = key.lower()
        elif key.startswith("ctrl+"):
            # Already has modifier prefix
            return key.lower()
        elif key.startswith("shift+"):
            return key.lower()
        else:
            # Unknown key
            return None

        return base_key

    def _refresh_all_rows(self) -> None:
        """Refresh all keybinding rows with current temp bindings."""
        conflicts = find_conflicts(self._temp_bindings)
        conflict_keys = {c.key for c in conflicts}

        for row in self.query(KeybindingRow):
            key = self._temp_bindings.get(row.action_id, "")
            row.update_key(key, key in conflict_keys)

        self._update_conflict_warning()

    def _update_conflict_warning(self) -> None:
        """Show/hide conflict warning based on current bindings."""
        conflicts = find_conflicts(self._temp_bindings)
        warning = self.query_one("#conflict-warning", Static)
        if conflicts:
            warning.add_class("visible")
        else:
            warning.remove_class("visible")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            self._save_and_dismiss()
        elif event.button.id == "btn-reset":
            self._reset_to_vim()
        elif event.button.id == "btn-cancel":
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel and return without saving."""
        if self._editing_action:
            self._stop_editing()
        else:
            self.dismiss(False)

    def action_save(self) -> None:
        """Save keybindings and dismiss."""
        self._save_and_dismiss()

    def _save_and_dismiss(self) -> None:
        """Save keybindings and dismiss the screen."""
        if self._changed:
            # Save the keybindings
            profile_select = self.query_one("#profile-select", Select)
            profile = str(profile_select.value) if profile_select.value else "vim"

            if profile == "custom":
                self._settings.keybindings = self._temp_bindings
            else:
                self._settings.reset_keybindings(profile)

        self.dismiss(self._changed)

    def _reset_to_vim(self) -> None:
        """Reset keybindings to vim defaults."""
        from rally_tui.utils.keybindings import VIM_KEYBINDINGS

        self._temp_bindings = dict(VIM_KEYBINDINGS)
        self._changed = True

        # Update profile selector
        profile_select = self.query_one("#profile-select", Select)
        profile_select.value = "vim"

        self._refresh_all_rows()
