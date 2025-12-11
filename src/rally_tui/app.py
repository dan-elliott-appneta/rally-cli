"""Rally TUI - Main Application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from rally_tui.models.sample_data import SAMPLE_TICKETS
from rally_tui.widgets import TicketDetail, TicketList


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
        with Horizontal(id="main-container"):
            yield TicketList(SAMPLE_TICKETS, id="ticket-list")
            yield TicketDetail(id="ticket-detail")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the detail panel with the first ticket."""
        if SAMPLE_TICKETS:
            detail = self.query_one(TicketDetail)
            detail.ticket = SAMPLE_TICKETS[0]

    def on_ticket_list_ticket_highlighted(
        self, event: TicketList.TicketHighlighted
    ) -> None:
        """Update detail panel when ticket highlight changes."""
        detail = self.query_one(TicketDetail)
        detail.ticket = event.ticket

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
