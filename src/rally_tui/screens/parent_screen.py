"""Parent selection screen for assigning ticket parents."""

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from rally_tui.models import Ticket


@dataclass
class ParentOption:
    """Represents a parent Feature option."""

    formatted_id: str
    name: str

    @property
    def truncated_name(self, max_length: int = 35) -> str:
        """Get truncated name for display."""
        if len(self.name) <= max_length:
            return self.name
        return self.name[: max_length - 3] + "..."

    def display_text(self, index: int) -> str:
        """Format for button display: '1. F59625 - Feature Name...'."""
        truncated = self.truncated_name
        return f"{index}. {self.formatted_id} - {truncated}"


class ParentScreen(Screen[str | None]):
    """Screen for selecting a parent Feature for a ticket.

    Shows configurable parent options with truncated titles,
    plus an option to enter a custom parent ID.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("1", "select_1", "1", show=False),
        Binding("2", "select_2", "2", show=False),
        Binding("3", "select_3", "3", show=False),
        Binding("4", "select_custom", "4", show=False),
    ]

    DEFAULT_CSS = """
    ParentScreen {
        background: $background;
    }

    #parent-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #parent-info {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #parent-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #parent-buttons {
        align: center middle;
        padding: 1 2;
    }

    #parent-buttons Button {
        margin: 0 1;
        min-width: 50;
    }

    #parent-buttons Button.-selected {
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
        ticket: Ticket,
        parent_options: list[ParentOption],
        name: str | None = None,
    ) -> None:
        """Initialize the parent selection screen.

        Args:
            ticket: The ticket that needs a parent.
            parent_options: List of ParentOption with ID and name.
            name: Optional screen name.
        """
        super().__init__(name=name)
        self._ticket = ticket
        self._parent_options = parent_options
        self._custom_mode = False

    @property
    def ticket(self) -> Ticket:
        """Get the ticket being updated."""
        return self._ticket

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Select Parent Feature - {self._ticket.formatted_id}",
            id="parent-title",
        )
        yield Static(
            "Ticket must have a parent before moving to In Progress.",
            id="parent-info",
        )

        # Show different hint based on whether options are configured
        if self._parent_options:
            yield Static(
                f"Select a parent (1-{len(self._parent_options)}) or enter custom ID ({len(self._parent_options) + 1}):",
                id="parent-hint",
            )
        else:
            yield Static(
                "Enter a Feature ID below (e.g., F12345):",
                id="parent-hint",
            )

        with Vertical(id="parent-buttons"):
            for i, option in enumerate(self._parent_options, 1):
                yield Button(option.display_text(i), id=f"btn-parent-{i}")
            # Custom button index is number of options + 1
            custom_index = len(self._parent_options) + 1
            yield Button(f"{custom_index}. Enter custom ID...", id="btn-parent-custom")
        with Vertical(id="custom-input-container"):
            yield Input(
                placeholder="Enter Feature ID (e.g., F12345)",
                id="custom-input",
            )
        yield Footer()

    def on_mount(self) -> None:
        """Focus first parent button or custom button if no options."""
        if self._parent_options:
            self.query_one("#btn-parent-1", Button).focus()
        else:
            # No parent options - focus custom button
            self.query_one("#btn-parent-custom", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle parent button clicks."""
        btn_id = event.button.id
        if btn_id == "btn-parent-custom":
            self._show_custom_input()
        elif btn_id and btn_id.startswith("btn-parent-"):
            index = int(btn_id.split("-")[-1]) - 1
            if 0 <= index < len(self._parent_options):
                self.dismiss(self._parent_options[index].formatted_id)

    def _show_custom_input(self) -> None:
        """Show the custom input field."""
        self._custom_mode = True
        custom_input = self.query_one("#custom-input", Input)
        custom_input.add_class("visible")
        custom_input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle custom ID submission."""
        value = event.value.strip().upper()
        if value:
            self.dismiss(value)

    def action_cancel(self) -> None:
        """Cancel and return without changes."""
        self.dismiss(None)

    def action_select_1(self) -> None:
        """Select first parent option, or show custom input if no options."""
        if len(self._parent_options) >= 1:
            self.dismiss(self._parent_options[0].formatted_id)
        else:
            # No options configured - "1" triggers custom input
            self._show_custom_input()

    def action_select_2(self) -> None:
        """Select second parent option, or show custom input if only 1 option."""
        if len(self._parent_options) >= 2:
            self.dismiss(self._parent_options[1].formatted_id)
        elif len(self._parent_options) == 1:
            # Only 1 option - "2" triggers custom input
            self._show_custom_input()

    def action_select_3(self) -> None:
        """Select third parent option, or show custom input if only 2 options."""
        if len(self._parent_options) >= 3:
            self.dismiss(self._parent_options[2].formatted_id)
        elif len(self._parent_options) == 2:
            # Only 2 options - "3" triggers custom input
            self._show_custom_input()

    def action_select_custom(self) -> None:
        """Show custom input field (always bound to 4, or next number after options)."""
        self._show_custom_input()
