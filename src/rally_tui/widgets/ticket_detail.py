"""Ticket detail widget for displaying full ticket information."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from rally_tui.models import Ticket


class TicketDetail(VerticalScroll):
    """Displays detailed information about a selected ticket.

    This widget shows all fields of a ticket in a scrollable view.
    It updates reactively when the ticket property changes.
    """

    ticket: reactive[Ticket | None] = reactive(None)

    def compose(self) -> ComposeResult:
        """Create the detail view structure."""
        yield Static(id="detail-header")
        yield Static(id="detail-divider")
        yield Static(id="detail-metadata")
        yield Static(id="detail-description-label")
        yield Static(id="detail-description")

    def watch_ticket(self, ticket: Ticket | None) -> None:
        """Update the display when ticket changes."""
        if ticket is None:
            self._show_empty_state()
        else:
            self._show_ticket(ticket)

    def _show_empty_state(self) -> None:
        """Display placeholder when no ticket selected."""
        self.query_one("#detail-header", Static).update("No ticket selected")
        self.query_one("#detail-divider", Static).update("")
        self.query_one("#detail-metadata", Static).update(
            "Select a ticket from the list to view details"
        )
        self.query_one("#detail-description-label", Static).update("")
        self.query_one("#detail-description", Static).update("")

    def _show_ticket(self, ticket: Ticket) -> None:
        """Display the ticket details."""
        # Header: ID and Name
        header = f"{ticket.formatted_id} - {ticket.name}"
        self.query_one("#detail-header", Static).update(header)

        # Divider
        self.query_one("#detail-divider", Static).update("─" * 40)

        # Metadata section: Owner, Iteration, Points, State
        owner_display = ticket.owner or "Unassigned"
        iteration_display = ticket.iteration or "Unscheduled"
        points_display = str(ticket.points) if ticket.points is not None else "—"
        metadata = (
            f"Owner: {owner_display}\n"
            f"Iteration: {iteration_display}\n"
            f"Points: {points_display}\n"
            f"State: {ticket.state}"
        )
        self.query_one("#detail-metadata", Static).update(metadata)

        # Description
        self.query_one("#detail-description-label", Static).update("\nDescription:")
        description = ticket.description or "No description available."
        self.query_one("#detail-description", Static).update(description)
