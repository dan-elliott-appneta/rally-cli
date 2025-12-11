"""Rally TUI - Main Application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from rally_tui.models.sample_data import SAMPLE_TICKETS
from rally_tui.widgets import TicketList


class RallyTUI(App[None]):
    """A TUI for browsing and managing Rally work items."""

    TITLE = "Rally TUI"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "help", "Help", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        yield TicketList(SAMPLE_TICKETS, id="ticket-list")
        yield Footer()

    def on_ticket_list_ticket_highlighted(
        self, event: TicketList.TicketHighlighted
    ) -> None:
        """Handle ticket highlight changes."""
        if event.ticket:
            self.log.info(f"Highlighted: {event.ticket.formatted_id}")

    def on_ticket_list_ticket_selected(
        self, event: TicketList.TicketSelected
    ) -> None:
        """Handle ticket selection (Enter key)."""
        self.log.info(f"Selected: {event.ticket.formatted_id}")


def main() -> None:
    """Entry point for the application."""
    app = RallyTUI()
    app.run()


if __name__ == "__main__":
    main()
