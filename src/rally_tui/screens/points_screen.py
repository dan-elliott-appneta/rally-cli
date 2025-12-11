"""Points input screen for setting story points."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from rally_tui.models import Ticket


class PointsScreen(Screen[int | None]):
    """Screen for setting story points on a ticket."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "submit", "Submit", show=False),
    ]

    DEFAULT_CSS = """
    PointsScreen {
        background: $background;
    }

    #points-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #points-current {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #points-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #points-input {
        margin: 1 2;
        width: 20;
    }

    #points-error {
        text-align: center;
        padding: 1;
        color: $error;
        display: none;
    }
    """

    def __init__(
        self,
        ticket: Ticket,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._ticket = ticket

    @property
    def ticket(self) -> Ticket:
        """Get the ticket being updated."""
        return self._ticket

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Set Points - {self._ticket.formatted_id}",
            id="points-title",
        )
        current = self._ticket.points
        current_text = f"Current: {current}" if current is not None else "Current: Not set"
        yield Static(current_text, id="points-current")
        yield Static(
            "Enter story points (0-100) and press Enter",
            id="points-hint",
        )
        yield Input(
            placeholder="Points",
            id="points-input",
            type="integer",
        )
        yield Static("", id="points-error")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the input and pre-fill current value."""
        input_widget = self.query_one("#points-input", Input)
        if self._ticket.points is not None:
            input_widget.value = str(self._ticket.points)
        input_widget.focus()

    def action_cancel(self) -> None:
        """Cancel and return without changes."""
        self.dismiss(None)

    def action_submit(self) -> None:
        """Submit the points value."""
        input_widget = self.query_one("#points-input", Input)
        error_widget = self.query_one("#points-error", Static)
        value = input_widget.value.strip()

        if not value:
            # Empty value means clear points
            self.dismiss(0)
            return

        try:
            points = int(value)
            if points < 0 or points > 100:
                error_widget.update("Points must be between 0 and 100")
                error_widget.display = True
                return
            self.dismiss(points)
        except ValueError:
            error_widget.update("Please enter a valid number")
            error_widget.display = True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input."""
        self.action_submit()
