"""Owner selection screen for assigning ticket owners."""

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static


@dataclass
class OwnerOption:
    """Represents an owner option for selection."""

    display_name: str

    def display_text(self, index: int) -> str:
        """Format for button display: '1. Owner Name'."""
        return f"{index}. {self.display_name}"


class OwnerScreen(Screen[str | None]):
    """Screen for selecting an owner for tickets.

    Shows users who have work items in the current iteration,
    plus an option to enter a custom owner name.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("1", "select_1", "1", show=False),
        Binding("2", "select_2", "2", show=False),
        Binding("3", "select_3", "3", show=False),
        Binding("4", "select_4", "4", show=False),
        Binding("5", "select_5", "5", show=False),
        Binding("6", "select_6", "6", show=False),
        Binding("7", "select_7", "7", show=False),
        Binding("8", "select_8", "8", show=False),
        Binding("9", "select_9", "9", show=False),
        Binding("0", "select_custom", "0", show=False),
    ]

    DEFAULT_CSS = """
    OwnerScreen {
        background: $background;
    }

    #owner-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #owner-info {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #owner-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #owner-buttons {
        align: center middle;
        padding: 1 2;
    }

    #owner-buttons Button {
        margin: 0 1;
        min-width: 40;
    }

    #owner-buttons Button.-selected {
        background: $primary;
    }

    #custom-input-container {
        align: center middle;
        padding: 1;
        height: auto;
    }

    #custom-input {
        width: 50;
        display: none;
    }

    #custom-input.visible {
        display: block;
    }
    """

    def __init__(
        self,
        owner_options: list[OwnerOption],
        ticket_count: int = 1,
        name: str | None = None,
    ) -> None:
        """Initialize the owner selection screen.

        Args:
            owner_options: List of OwnerOption with display names.
            ticket_count: Number of tickets being assigned.
            name: Optional screen name.
        """
        super().__init__(name=name)
        self._owner_options = owner_options
        self._ticket_count = ticket_count
        self._custom_mode = False

    @property
    def owner_options(self) -> list[OwnerOption]:
        """Get the available owner options."""
        return self._owner_options

    def compose(self) -> ComposeResult:
        yield Header()
        suffix = "s" if self._ticket_count != 1 else ""
        yield Static(
            f"Assign Owner - {self._ticket_count} ticket{suffix}",
            id="owner-title",
        )
        yield Static(
            "Select an owner from the current iteration's users.",
            id="owner-info",
        )

        # Show different hint based on whether options are available
        if self._owner_options:
            num_opts = len(self._owner_options)
            custom_key = "0" if num_opts >= 9 else str(num_opts + 1)
            yield Static(
                f"Select an owner (1-{min(num_opts, 9)}) or enter custom ({custom_key}):",
                id="owner-hint",
            )
        else:
            yield Static(
                "No users found. Enter owner name below:",
                id="owner-hint",
            )

        with Vertical(id="owner-buttons"):
            # Show up to 9 options (1-9 keys)
            for i, option in enumerate(self._owner_options[:9], 1):
                yield Button(option.display_text(i), id=f"btn-owner-{i}")
            # Custom button
            custom_index = min(len(self._owner_options) + 1, 10)
            custom_label = "0" if custom_index == 10 else str(custom_index)
            yield Button(f"{custom_label}. Enter custom name...", id="btn-owner-custom")
        with Vertical(id="custom-input-container"):
            yield Input(
                placeholder="Enter owner display name",
                id="custom-input",
            )
        yield Footer()

    def on_mount(self) -> None:
        """Focus first owner button or custom button if no options."""
        if self._owner_options:
            self.query_one("#btn-owner-1", Button).focus()
        else:
            # No owner options - focus custom button
            self.query_one("#btn-owner-custom", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle owner button clicks."""
        btn_id = event.button.id
        if btn_id == "btn-owner-custom":
            self._show_custom_input()
        elif btn_id and btn_id.startswith("btn-owner-"):
            index = int(btn_id.split("-")[-1]) - 1
            if 0 <= index < len(self._owner_options):
                self.dismiss(self._owner_options[index].display_name)

    def _show_custom_input(self) -> None:
        """Show the custom input field."""
        self._custom_mode = True
        custom_input = self.query_one("#custom-input", Input)
        custom_input.add_class("visible")
        custom_input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle custom name submission."""
        value = event.value.strip()
        if value:
            self.dismiss(value)

    def action_cancel(self) -> None:
        """Cancel and return without changes."""
        self.dismiss(None)

    def _select_option(self, index: int) -> None:
        """Select an owner option by index (1-based)."""
        if index <= len(self._owner_options):
            self.dismiss(self._owner_options[index - 1].display_name)
        elif index == len(self._owner_options) + 1:
            # This index is the custom option
            self._show_custom_input()

    def action_select_1(self) -> None:
        """Select first owner option."""
        self._select_option(1)

    def action_select_2(self) -> None:
        """Select second owner option."""
        self._select_option(2)

    def action_select_3(self) -> None:
        """Select third owner option."""
        self._select_option(3)

    def action_select_4(self) -> None:
        """Select fourth owner option."""
        self._select_option(4)

    def action_select_5(self) -> None:
        """Select fifth owner option."""
        self._select_option(5)

    def action_select_6(self) -> None:
        """Select sixth owner option."""
        self._select_option(6)

    def action_select_7(self) -> None:
        """Select seventh owner option."""
        self._select_option(7)

    def action_select_8(self) -> None:
        """Select eighth owner option."""
        self._select_option(8)

    def action_select_9(self) -> None:
        """Select ninth owner option."""
        self._select_option(9)

    def action_select_custom(self) -> None:
        """Show custom input field (bound to 0)."""
        self._show_custom_input()
