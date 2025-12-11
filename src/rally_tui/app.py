"""Rally TUI - Main Application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Header

from rally_tui.models.sample_data import SAMPLE_TICKETS
from rally_tui.widgets import CommandBar, TicketDetail, TicketList


class RallyTUI(App[None]):
    """A TUI for browsing and managing Rally work items."""

    TITLE = "Rally TUI"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "switch_panel", "Switch Panel", show=False, priority=True),
        Binding("?", "help", "Help", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        with Horizontal(id="main-container"):
            yield TicketList(SAMPLE_TICKETS, id="ticket-list")
            yield TicketDetail(id="ticket-detail")
        yield CommandBar(id="command-bar")

    def on_mount(self) -> None:
        """Initialize the app state."""
        # Set panel titles
        self.query_one("#ticket-list").border_title = "Tickets"
        self.query_one("#ticket-detail").border_title = "Details"

        # Set first ticket in detail panel
        if SAMPLE_TICKETS:
            detail = self.query_one(TicketDetail)
            detail.ticket = SAMPLE_TICKETS[0]

        # Focus the ticket list initially
        self.query_one(TicketList).focus()

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

    def action_switch_panel(self) -> None:
        """Switch focus between the list and detail panels."""
        ticket_list = self.query_one(TicketList)
        ticket_detail = self.query_one(TicketDetail)
        command_bar = self.query_one(CommandBar)

        if ticket_list.has_focus:
            ticket_detail.focus()
            command_bar.set_context("detail")
        else:
            ticket_list.focus()
            command_bar.set_context("list")


def main() -> None:
    """Entry point for the application."""
    app = RallyTUI()
    app.run()


if __name__ == "__main__":
    main()
