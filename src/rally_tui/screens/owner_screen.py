"""Owner selection screen for assigning tickets to owners."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, ListItem, ListView, Static

from rally_tui.models import Owner
from rally_tui.user_settings import UserSettings
from rally_tui.utils.keybindings import VIM_KEYBINDINGS

# Special marker for custom owner option
CUSTOM_OWNER_MARKER = "__CUSTOM_OWNER__"


class OwnerSelectionScreen(Screen[Owner | None]):
    """Screen for selecting an owner for ticket assignment.

    Returns the selected Owner object, or None if cancelled.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
    ]

    DEFAULT_CSS = """
    OwnerSelectionScreen {
        background: $background;
    }

    #owner-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #owner-subtitle {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #owner-list-container {
        height: auto;
        max-height: 60%;
        padding: 1 2;
    }

    #owner-list {
        height: auto;
        max-height: 100%;
        background: $surface;
        border: solid $primary;
    }

    #owner-list > ListItem {
        padding: 0 1;
    }

    #owner-list > ListItem.--highlight {
        background: $primary 30%;
    }

    #owner-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #custom-owner-container {
        align: center middle;
        padding: 1 2;
        display: none;
    }

    #custom-owner-container.visible {
        display: block;
    }

    #custom-owner-input {
        width: 50;
    }

    #no-owners-message {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        owners: set[Owner],
        title: str = "Select Owner",
        name: str | None = None,
        user_settings: UserSettings | None = None,
    ) -> None:
        """Initialize owner selection screen.

        Args:
            owners: Set of Owner objects to display in list
            title: Screen title (e.g., "Assign Owner - US1234")
            name: Screen name
            user_settings: User settings for keybindings
        """
        super().__init__(name=name)
        self._owners = sorted(list(owners), key=lambda o: o.display_name.lower())
        self._title = title
        self._user_settings = user_settings
        self._show_custom_input = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._title, id="owner-title")
        yield Static("Select an owner for this ticket:", id="owner-subtitle")

        with Vertical(id="owner-list-container"):
            list_items = []
            for owner in self._owners:
                list_items.append(ListItem(Static(owner.display_name), id=f"owner-{owner.object_id}"))
            # Add "Custom Owner..." option
            list_items.append(ListItem(Static("[Custom Owner...]"), id="owner-custom"))

            if not self._owners:
                yield Static("No owners found in current iteration.", id="no-owners-message")

            yield ListView(*list_items, id="owner-list")

        yield Static("j/k: Navigate  Enter: Select  ESC: Cancel", id="owner-hint")

        with Vertical(id="custom-owner-container"):
            yield Static("Enter owner name:")
            yield Input(placeholder="Display Name", id="custom-owner-input")
            yield Button("Search", id="btn-search-owner")

        yield Footer()

    def on_mount(self) -> None:
        """Focus the owner list and apply keybindings."""
        self._apply_keybindings()
        list_view = self.query_one("#owner-list", ListView)
        list_view.focus()

    def _apply_keybindings(self) -> None:
        """Apply vim-style keybindings for list navigation."""
        if self._user_settings:
            keybindings = self._user_settings.keybindings
        else:
            keybindings = VIM_KEYBINDINGS

        # Bind j/k for navigation
        navigation_bindings = {
            "navigation.down": "cursor_down",
            "navigation.up": "cursor_up",
        }

        for action_id, handler in navigation_bindings.items():
            if action_id in keybindings:
                key = keybindings[action_id]
                self._bindings.bind(key, handler, show=False)

    def action_cursor_down(self) -> None:
        """Move cursor down in list."""
        list_view = self.query_one("#owner-list", ListView)
        list_view.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in list."""
        list_view = self.query_one("#owner-list", ListView)
        list_view.action_cursor_up()

    def action_select(self) -> None:
        """Select the highlighted owner."""
        list_view = self.query_one("#owner-list", ListView)
        if list_view.highlighted_child:
            item_id = list_view.highlighted_child.id
            if item_id == "owner-custom":
                self._show_custom_input_dialog()
            elif item_id and item_id.startswith("owner-"):
                object_id = item_id[6:]  # Remove "owner-" prefix
                owner = next((o for o in self._owners if o.object_id == object_id), None)
                if owner:
                    self.dismiss(owner)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection (double-click or enter on ListView)."""
        item_id = event.item.id
        if item_id == "owner-custom":
            self._show_custom_input_dialog()
        elif item_id and item_id.startswith("owner-"):
            object_id = item_id[6:]
            owner = next((o for o in self._owners if o.object_id == object_id), None)
            if owner:
                self.dismiss(owner)

    def _show_custom_input_dialog(self) -> None:
        """Show the custom owner input area."""
        container = self.query_one("#custom-owner-container")
        container.add_class("visible")
        input_field = self.query_one("#custom-owner-input", Input)
        input_field.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle search button press."""
        if event.button.id == "btn-search-owner":
            self._search_custom_owner()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in custom owner input."""
        if event.input.id == "custom-owner-input":
            self._search_custom_owner()

    def _search_custom_owner(self) -> None:
        """Search for custom owner by display name.

        Creates a temporary Owner with the display name.
        The caller will need to resolve this to a real Owner via API.
        """
        input_field = self.query_one("#custom-owner-input", Input)
        name = input_field.value.strip()
        if name:
            # Return a temporary Owner - caller must resolve via API
            temp_owner = Owner(
                object_id=f"TEMP:{name}",  # Temporary ID, needs API resolution
                display_name=name,
                user_name=None,
            )
            self.dismiss(temp_owner)

    def action_cancel(self) -> None:
        """Cancel and return without selection."""
        self.dismiss(None)
