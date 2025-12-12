"""Bulk actions screen for multi-select operations."""

from enum import Enum

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from rally_tui.user_settings import UserSettings
from rally_tui.utils.keybindings import VIM_KEYBINDINGS


class BulkAction(Enum):
    """Available bulk actions for selected tickets."""

    SET_PARENT = "parent"
    SET_STATE = "state"
    SET_ITERATION = "iteration"
    SET_POINTS = "points"
    YANK = "yank"


class BulkActionsScreen(Screen[BulkAction | None]):
    """Screen for selecting a bulk action to perform on selected tickets.

    Shows available bulk operations:
    - Set Parent: Assign a parent Feature to all selected tickets
    - Set State: Change state of all selected tickets
    - Set Iteration: Move all selected tickets to an iteration
    - Set Points: Set story points on all selected tickets
    - Yank: Copy space-separated list of ticket URLs to clipboard
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("1", "select_parent", "1", show=False),
        Binding("2", "select_state", "2", show=False),
        Binding("3", "select_iteration", "3", show=False),
        Binding("4", "select_points", "4", show=False),
        Binding("5", "select_yank", "5", show=False),
    ]

    DEFAULT_CSS = """
    BulkActionsScreen {
        background: $background;
    }

    #bulk-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #bulk-info {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #bulk-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #bulk-buttons {
        align: center middle;
        padding: 1 2;
    }

    #bulk-buttons Button {
        margin: 0 1;
        min-width: 30;
    }
    """

    def __init__(
        self,
        count: int,
        name: str | None = None,
        user_settings: UserSettings | None = None,
    ) -> None:
        """Initialize the bulk actions screen.

        Args:
            count: Number of selected tickets.
            name: Optional screen name.
            user_settings: User settings for keybindings.
        """
        super().__init__(name=name)
        self._count = count
        self._user_settings = user_settings

    @property
    def count(self) -> int:
        """Get the number of selected tickets."""
        return self._count

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Bulk Actions - {self._count} ticket{'s' if self._count != 1 else ''} selected",
            id="bulk-title",
        )
        yield Static(
            f"Select an action to perform on {self._count} ticket{'s' if self._count != 1 else ''}:",
            id="bulk-info",
        )
        with Vertical(id="bulk-buttons"):
            yield Button("1. Set Parent", id="btn-parent", variant="primary")
            yield Button("2. Set State", id="btn-state", variant="primary")
            yield Button("3. Set Iteration", id="btn-iteration", variant="primary")
            yield Button("4. Set Points", id="btn-points", variant="primary")
            yield Button("5. Yank (Copy URLs)", id="btn-yank", variant="primary")
        yield Static(
            "Press 1-5 or click a button, ESC to cancel",
            id="bulk-hint",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Focus first button and apply keybindings."""
        self._apply_keybindings()
        self.query_one("#btn-parent", Button).focus()

    def _apply_keybindings(self) -> None:
        """Apply vim-style keybindings for button navigation."""
        if self._user_settings:
            keybindings = self._user_settings.keybindings
        else:
            keybindings = VIM_KEYBINDINGS

        navigation_bindings = {
            "navigation.down": "focus_next_button",
            "navigation.up": "focus_prev_button",
        }

        for action_id, handler in navigation_bindings.items():
            if action_id in keybindings:
                key = keybindings[action_id]
                self._bindings.bind(key, handler, show=False)

    def action_focus_next_button(self) -> None:
        """Move focus to the next button."""
        self.focus_next()

    def action_focus_prev_button(self) -> None:
        """Move focus to the previous button."""
        self.focus_previous()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id
        if button_id == "btn-parent":
            self.dismiss(BulkAction.SET_PARENT)
        elif button_id == "btn-state":
            self.dismiss(BulkAction.SET_STATE)
        elif button_id == "btn-iteration":
            self.dismiss(BulkAction.SET_ITERATION)
        elif button_id == "btn-points":
            self.dismiss(BulkAction.SET_POINTS)
        elif button_id == "btn-yank":
            self.dismiss(BulkAction.YANK)

    def action_cancel(self) -> None:
        """Cancel and return without action."""
        self.dismiss(None)

    def action_select_parent(self) -> None:
        """Select Set Parent action."""
        self.dismiss(BulkAction.SET_PARENT)

    def action_select_state(self) -> None:
        """Select Set State action."""
        self.dismiss(BulkAction.SET_STATE)

    def action_select_iteration(self) -> None:
        """Select Set Iteration action."""
        self.dismiss(BulkAction.SET_ITERATION)

    def action_select_points(self) -> None:
        """Select Set Points action."""
        self.dismiss(BulkAction.SET_POINTS)

    def action_select_yank(self) -> None:
        """Select Yank action."""
        self.dismiss(BulkAction.YANK)
