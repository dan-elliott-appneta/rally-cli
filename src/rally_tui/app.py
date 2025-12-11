"""Rally TUI - Main Application."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Header

from rally_tui.config import RallyConfig
from rally_tui.screens import DiscussionScreen, SplashScreen
from rally_tui.services import MockRallyClient, RallyClient, RallyClientProtocol
from rally_tui.widgets import (
    CommandBar,
    SearchInput,
    StatusBar,
    TicketDetail,
    TicketList,
)


class RallyTUI(App[None]):
    """A TUI for browsing and managing Rally work items."""

    TITLE = "Rally TUI"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "switch_panel", "Switch Panel", show=False, priority=True),
        Binding("?", "help", "Help", show=False),
        Binding("/", "start_search", "Search", show=False),
        Binding("d", "open_discussions", "Discussions", show=False),
    ]

    def __init__(
        self,
        client: RallyClientProtocol | None = None,
        config: RallyConfig | None = None,
        show_splash: bool = True,
    ) -> None:
        """Initialize the application.

        Args:
            client: Rally client to use for data. Takes precedence over config.
            config: Rally configuration for connecting to API.
                   If not provided, uses MockRallyClient.
            show_splash: Whether to show splash screen on startup.
        """
        super().__init__()
        self._show_splash = show_splash

        if client is not None:
            # Explicit client provided (e.g., for testing)
            self._client = client
            self._connected = isinstance(client, RallyClient)
        elif config is not None and config.is_configured:
            # Try to connect with provided config
            try:
                self._client = RallyClient(config)
                self._connected = True
            except Exception:
                # Fall back to mock client on connection failure
                self._client = MockRallyClient()
                self._connected = False
        else:
            # No config or not configured - use mock client
            self._client = MockRallyClient()
            self._connected = False

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        yield StatusBar(
            workspace=self._client.workspace,
            project=self._client.project,
            connected=self._connected,
            id="status-bar",
        )
        tickets = self._client.get_tickets()
        with Horizontal(id="main-container"):
            with Vertical(id="list-container"):
                yield TicketList(tickets, id="ticket-list")
                yield SearchInput(id="search-input")
            yield TicketDetail(id="ticket-detail")
        yield CommandBar(id="command-bar")

    def on_mount(self) -> None:
        """Initialize the app state."""
        # Set panel titles
        self.query_one("#ticket-list").border_title = "Tickets"
        self.query_one("#ticket-detail").border_title = "Details"

        # Hide search input initially
        self.query_one("#search-input").display = False

        # Set first ticket in detail panel
        tickets = self._client.get_tickets()
        if tickets:
            detail = self.query_one(TicketDetail)
            detail.ticket = tickets[0]

        # Focus the ticket list initially
        self.query_one(TicketList).focus()

        # Show splash screen on startup
        if self._show_splash:
            self.push_screen(SplashScreen())

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
        search_input = self.query_one(SearchInput)

        # If search is active, don't switch panels
        if search_input.has_focus:
            return

        if ticket_list.has_focus:
            ticket_detail.focus()
            command_bar.set_context("detail")
        else:
            ticket_list.focus()
            command_bar.set_context("list")

    def action_start_search(self) -> None:
        """Activate search mode."""
        search_input = self.query_one(SearchInput)
        search_input.display = True
        search_input.focus()
        self.query_one(CommandBar).set_context("search")

    def _end_search(self, clear: bool = False) -> None:
        """End search mode and return to list.

        Args:
            clear: If True, also clear the filter.
        """
        search_input = self.query_one(SearchInput)
        ticket_list = self.query_one(TicketList)
        command_bar = self.query_one(CommandBar)
        status_bar = self.query_one(StatusBar)

        if clear:
            search_input.value = ""
            ticket_list.clear_filter()
            status_bar.clear_filter_info()

        search_input.display = False
        ticket_list.focus()
        command_bar.set_context("list")

    def on_search_input_search_changed(
        self, event: SearchInput.SearchChanged
    ) -> None:
        """Filter list as user types."""
        ticket_list = self.query_one(TicketList)
        ticket_list.filter_tickets(event.query)
        self._update_filter_status()

    def on_search_input_search_submitted(
        self, event: SearchInput.SearchSubmitted
    ) -> None:
        """Confirm search and focus list."""
        self._end_search(clear=False)

    def on_search_input_search_cleared(
        self, event: SearchInput.SearchCleared
    ) -> None:
        """Clear filter and return to list."""
        self._end_search(clear=True)

    def _update_filter_status(self) -> None:
        """Update status bar with filter info."""
        ticket_list = self.query_one(TicketList)
        status_bar = self.query_one(StatusBar)

        if ticket_list.filter_query:
            status_bar.set_filter_info(
                ticket_list.filtered_count, ticket_list.total_count
            )
        else:
            status_bar.clear_filter_info()

    def action_open_discussions(self) -> None:
        """Open discussions for the currently selected ticket."""
        detail = self.query_one(TicketDetail)
        if detail.ticket:
            self.push_screen(DiscussionScreen(detail.ticket, self._client))


def main() -> None:
    """Entry point for the application.

    Loads configuration from environment variables and starts the app.
    If RALLY_APIKEY is set, attempts to connect to Rally.
    Otherwise, runs in offline mode with sample data.
    """
    config = RallyConfig()
    app = RallyTUI(config=config)
    app.run()


if __name__ == "__main__":
    main()
