"""Rally TUI - Main Application."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header

from rally_tui.config import RallyConfig
from rally_tui.screens import (
    DiscussionScreen,
    PointsScreen,
    QuickTicketData,
    QuickTicketScreen,
    SplashScreen,
    StateScreen,
)
from rally_tui.services import MockRallyClient, RallyClient, RallyClientProtocol
from rally_tui.user_settings import UserSettings
from rally_tui.utils import get_logger, setup_logging
from rally_tui.widgets import (
    SearchInput,
    StatusBar,
    TicketDetail,
    TicketList,
)

# Module logger
_log = get_logger("rally_tui.app")


class RallyTUI(App[None]):
    """A TUI for browsing and managing Rally work items."""

    TITLE = "Rally TUI"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("w", "quick_ticket", "Workitem"),
        Binding("s", "set_state", "State"),
        Binding("p", "set_points", "Points"),
        Binding("n", "toggle_notes", "Notes"),
        Binding("d", "open_discussions", "Discuss"),
        Binding("/", "start_search", "Search"),
        Binding("q", "quit", "Quit"),
        Binding("tab", "switch_panel", "Switch Panel", show=False, priority=True),
        Binding("t", "toggle_theme", "Theme", show=False),
        Binding("y", "copy_ticket_url", "Copy URL", show=False),
    ]

    def __init__(
        self,
        client: RallyClientProtocol | None = None,
        config: RallyConfig | None = None,
        show_splash: bool = True,
        user_settings: UserSettings | None = None,
    ) -> None:
        """Initialize the application.

        Args:
            client: Rally client to use for data. Takes precedence over config.
            config: Rally configuration for connecting to API.
                   If not provided, uses MockRallyClient.
            show_splash: Whether to show splash screen on startup.
            user_settings: User preferences. If None, loads from config file.
        """
        super().__init__()
        self._show_splash = show_splash
        self._user_settings = user_settings or UserSettings()
        self._server = config.server if config else "rally1.rallydev.com"

        _log.debug("Initializing RallyTUI application")

        if client is not None:
            # Explicit client provided (e.g., for testing)
            self._client = client
            self._connected = isinstance(client, RallyClient)
            _log.debug("Using provided client (test mode)")
        elif config is not None and config.is_configured:
            # Try to connect with provided config
            try:
                _log.info(f"Connecting to Rally server: {config.server}")
                self._client = RallyClient(config)
                self._connected = True
                _log.info(f"Connected to Rally as {self._client.current_user}")
            except Exception as e:
                # Fall back to mock client on connection failure
                _log.error(f"Failed to connect to Rally: {e}")
                self._client = MockRallyClient()
                self._connected = False
        else:
            # No config or not configured - use mock client
            _log.info("No Rally config provided, using offline mode")
            self._client = MockRallyClient()
            self._connected = False

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        yield StatusBar(
            workspace=self._client.workspace,
            project=self._client.project,
            connected=self._connected,
            current_user=self._client.current_user,
            id="status-bar",
        )
        tickets = self._client.get_tickets()
        with Horizontal(id="main-container"):
            with Vertical(id="list-container"):
                yield TicketList(tickets, id="ticket-list")
                yield SearchInput(id="search-input")
            yield TicketDetail(id="ticket-detail")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app state."""
        _log.debug("App mounted, initializing state")

        # Apply saved theme name (e.g., catppuccin-mocha)
        saved_theme = self._user_settings.theme_name
        if saved_theme in self.available_themes:
            self.theme = saved_theme
            _log.debug(f"Applied saved theme: {saved_theme}")
        else:
            # Fallback to basic dark/light theme
            self.theme = "textual-dark" if self._user_settings.theme == "dark" else "textual-light"

        # Set panel titles
        self.query_one("#ticket-list").border_title = "Tickets"
        self.query_one("#ticket-detail").border_title = "Details"

        # Hide search input initially
        self.query_one("#search-input").display = False

        # Set first ticket in detail panel (reuse tickets from TicketList, don't call API again)
        ticket_list = self.query_one(TicketList)
        _log.debug(f"Loaded {len(ticket_list._tickets)} tickets")
        if ticket_list._tickets:
            detail = self.query_one(TicketDetail)
            detail.ticket = ticket_list._tickets[0]

        # Focus the ticket list initially
        self.query_one(TicketList).focus()

        # Show splash screen on startup
        if self._show_splash:
            self.push_screen(SplashScreen())

        _log.info("Rally TUI started successfully")

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
        search_input = self.query_one(SearchInput)

        # If search is active, don't switch panels
        if search_input.has_focus:
            return

        if ticket_list.has_focus:
            ticket_detail.focus()
        else:
            ticket_list.focus()

    def action_start_search(self) -> None:
        """Activate search mode."""
        search_input = self.query_one(SearchInput)
        search_input.display = True
        search_input.focus()

    def _end_search(self, clear: bool = False) -> None:
        """End search mode and return to list.

        Args:
            clear: If True, also clear the filter.
        """
        search_input = self.query_one(SearchInput)
        ticket_list = self.query_one(TicketList)
        status_bar = self.query_one(StatusBar)

        if clear:
            search_input.value = ""
            ticket_list.clear_filter()
            status_bar.clear_filter_info()

        search_input.display = False
        ticket_list.focus()

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

    def action_toggle_theme(self) -> None:
        """Toggle between dark and light theme and persist setting."""
        # In Textual 0.40+, use theme property instead of deprecated dark property
        if self.theme and "light" in self.theme:
            self.theme = "textual-dark"
        else:
            self.theme = "textual-light"
        self._user_settings.theme = "dark" if "dark" in self.theme else "light"

    def watch_theme(self, theme: str) -> None:
        """Persist theme when changed via command palette."""
        self._user_settings.theme_name = theme

    def action_copy_ticket_url(self) -> None:
        """Copy the selected ticket's Rally URL to clipboard."""
        detail = self.query_one(TicketDetail)
        if detail.ticket:
            url = detail.ticket.rally_url(self._server)
            if url:
                self.copy_to_clipboard(url)
                self.notify(f"Copied: {url}", timeout=2)

    def action_toggle_notes(self) -> None:
        """Toggle between description and notes view in detail panel."""
        detail = self.query_one(TicketDetail)
        detail.toggle_content_view()

    def action_set_points(self) -> None:
        """Open the points screen for the selected ticket."""
        detail = self.query_one(TicketDetail)
        if detail.ticket:
            self.push_screen(
                PointsScreen(detail.ticket),
                callback=self._handle_points_result,
            )

    def _handle_points_result(self, points: float | None) -> None:
        """Handle the result from PointsScreen."""
        if points is None:
            _log.debug("Points update cancelled")
            return

        detail = self.query_one(TicketDetail)
        if not detail.ticket:
            return

        ticket_id = detail.ticket.formatted_id
        _log.info(f"Updating points for {ticket_id} to {points}")

        try:
            updated = self._client.update_points(detail.ticket, points)
            if updated:
                # Update the detail panel with new ticket data
                detail.ticket = updated
                # Update the ticket in the list (no resort needed for points)
                ticket_list = self.query_one(TicketList)
                ticket_list.update_ticket(updated, resort=False)
                # Display as int if whole number
                display_points = int(points) if points == int(points) else points
                self.notify(f"Points set to {display_points}", timeout=2)
                _log.info(f"Points updated successfully for {ticket_id}")
            else:
                _log.error(f"Failed to update points for {ticket_id}")
                self.notify("Failed to update points", severity="error", timeout=3)
        except Exception as e:
            _log.exception(f"Error updating points for {ticket_id}: {e}")
            self.notify("Failed to update points", severity="error", timeout=3)

    def action_set_state(self) -> None:
        """Open the state selection screen for the selected ticket."""
        detail = self.query_one(TicketDetail)
        if detail.ticket:
            self.push_screen(
                StateScreen(detail.ticket),
                callback=self._handle_state_result,
            )

    def _handle_state_result(self, state: str | None) -> None:
        """Handle the result from StateScreen."""
        if state is None:
            _log.debug("State update cancelled")
            return

        detail = self.query_one(TicketDetail)
        if not detail.ticket:
            return

        ticket_id = detail.ticket.formatted_id
        _log.info(f"Updating state for {ticket_id} to {state}")

        try:
            updated = self._client.update_state(detail.ticket, state)
            if updated:
                # Update the detail panel with new ticket data
                detail.ticket = updated
                # Update the ticket in the list
                ticket_list = self.query_one(TicketList)
                ticket_list.update_ticket(updated)
                self.notify(f"State set to {state}", timeout=2)
                _log.info(f"State updated successfully for {ticket_id}")
            else:
                _log.error(f"Failed to update state for {ticket_id}")
                self.notify("Failed to update state", severity="error", timeout=3)
        except Exception as e:
            _log.exception(f"Error updating state for {ticket_id}: {e}")
            self.notify("Failed to update state", severity="error", timeout=3)

    def action_quick_ticket(self) -> None:
        """Open the quick ticket creation screen."""
        self.push_screen(
            QuickTicketScreen(),
            callback=self._handle_quick_ticket_result,
        )

    def _handle_quick_ticket_result(self, data: QuickTicketData | None) -> None:
        """Handle the result from QuickTicketScreen."""
        if data is None:
            _log.debug("Quick ticket creation cancelled")
            return

        _log.info(f"Creating {data.ticket_type}: {data.title}")

        try:
            created = self._client.create_ticket(
                title=data.title,
                ticket_type=data.ticket_type,
                description=data.description,
            )
            if created:
                # Add the ticket to the list
                ticket_list = self.query_one(TicketList)
                ticket_list.add_ticket(created)
                # Select the new ticket
                detail = self.query_one(TicketDetail)
                detail.ticket = created
                # Show notification
                type_display = "User Story" if data.ticket_type == "HierarchicalRequirement" else "Defect"
                self.notify(f"Created {type_display}: {created.formatted_id}", timeout=3)
                _log.info(f"Created ticket: {created.formatted_id}")
            else:
                _log.error("Failed to create ticket")
                self.notify("Failed to create ticket", severity="error", timeout=3)
        except Exception as e:
            _log.exception(f"Error creating ticket: {e}")
            self.notify("Failed to create ticket", severity="error", timeout=3)


def main() -> None:
    """Entry point for the application.

    Loads configuration from environment variables and starts the app.
    If RALLY_APIKEY is set, attempts to connect to Rally.
    Otherwise, runs in offline mode with sample data.
    """
    # Initialize logging first
    user_settings = UserSettings()
    setup_logging(user_settings)

    _log.info("Starting Rally TUI")

    try:
        config = RallyConfig()
        app = RallyTUI(config=config, user_settings=user_settings)
        app.run()
    except Exception as e:
        _log.exception(f"Fatal error: {e}")
        raise
    finally:
        _log.info("Rally TUI shutdown")


if __name__ == "__main__":
    main()
