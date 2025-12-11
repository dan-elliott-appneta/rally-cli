"""Ticket detail widget for displaying full ticket information."""

from typing import Literal

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from rally_tui.models import Ticket
from rally_tui.utils import html_to_text

ContentView = Literal["description", "notes"]


class TicketDetail(VerticalScroll):
    """Displays detailed information about a selected ticket.

    This widget shows all fields of a ticket in a scrollable view.
    It updates reactively when the ticket property changes.
    Supports toggling between description and notes view.
    """

    can_focus = True  # Allow this widget to receive focus via Tab

    ticket: reactive[Ticket | None] = reactive(None)
    content_view: reactive[ContentView] = reactive("description")

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

    def watch_content_view(self, view: ContentView) -> None:
        """Update content display when view changes."""
        if self.ticket:
            self._update_content_section(self.ticket)

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

        # Content section (description or notes)
        self._update_content_section(ticket)

    def _update_content_section(self, ticket: Ticket) -> None:
        """Update the content section based on current view."""
        if self.content_view == "description":
            label = "\nDescription:"
            content = ticket.description or "No description available."
            content = html_to_text(content) or "No description available."
        else:
            label = "\nNotes:"
            content = ticket.notes or "No notes available."
            content = html_to_text(content) or "No notes available."

        self.query_one("#detail-description-label", Static).update(label)
        self.query_one("#detail-description", Static).update(escape(content))

    def toggle_content_view(self) -> None:
        """Toggle between description and notes view."""
        self.content_view = "notes" if self.content_view == "description" else "description"
