"""Rally TUI - Main Application."""

from __future__ import annotations

import argparse
import sys

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header
from textual.worker import Worker, WorkerState

from rally_tui import __version__
from rally_tui.config import RallyConfig
from rally_tui.screens import (
    BulkAction,
    BulkActionsScreen,
    ConfigData,
    ConfigScreen,
    DiscussionScreen,
    FILTER_ALL,
    FILTER_BACKLOG,
    IterationScreen,
    ParentOption,
    ParentScreen,
    PointsScreen,
    QuickTicketData,
    QuickTicketScreen,
    SplashScreen,
    StateScreen,
)
from rally_tui.models import Ticket
from rally_tui.services import BulkResult, MockRallyClient, RallyClient, RallyClientProtocol
from rally_tui.user_settings import UserSettings
from rally_tui.utils import get_logger, setup_logging
from rally_tui.widgets import (
    SearchInput,
    SortMode,
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
        Binding("o", "cycle_sort", "Sort"),
        Binding("n", "toggle_notes", "Notes"),
        Binding("d", "open_discussions", "Discuss"),
        Binding("i", "iteration_filter", "Sprint"),
        Binding("u", "toggle_user_filter", "My Items"),
        Binding("m", "bulk_actions", "Bulk"),
        Binding("/", "start_search", "Search"),
        Binding("f2", "open_settings", "Settings"),
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

        # Filter state
        self._iteration_filter: str | None = None  # Iteration name or FILTER_BACKLOG
        self._user_filter_active: bool = False
        self._all_tickets: list = []  # Store all tickets for filtering

        # State for parent selection flow
        self._pending_state: str | None = None  # State to set after parent selected

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
        # Start with empty list - tickets loaded async after splash shows
        self._all_tickets = []
        self._all_tickets_loaded = False
        with Horizontal(id="main-container"):
            with Vertical(id="list-container"):
                yield TicketList([], id="ticket-list")
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

        # Set initial filter state for connected mode
        if self._connected and self._client.current_iteration:
            self._iteration_filter = self._client.current_iteration
            self._user_filter_active = True
            status_bar = self.query_one(StatusBar)
            status_bar.set_iteration_filter(self._iteration_filter)
            status_bar.set_user_filter(True)
            _log.debug(f"Initial filters: iteration={self._iteration_filter}, user=True")

        # Focus the ticket list initially
        self.query_one(TicketList).focus()

        # Show splash screen first, then load tickets async
        # If no splash (test mode), load synchronously for predictable test behavior
        if self._show_splash:
            self.push_screen(SplashScreen())
            # Start loading tickets async (will dismiss splash when done)
            self.run_worker(self._load_initial_tickets, thread=True, exclusive=True)
        else:
            # Synchronous load for tests
            self._all_tickets = self._load_initial_tickets()
            self._on_initial_tickets_loaded_sync()

        _log.info("Rally TUI started successfully")

    def _load_initial_tickets(self) -> list:
        """Load initial filtered tickets in a thread."""
        _log.debug("Loading initial tickets...")
        try:
            # Load filtered tickets first (current iteration + user)
            tickets = self._client.get_tickets()
            return list(tickets)
        except Exception as e:
            _log.error(f"Failed to load tickets: {e}")
            return []

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker completion."""
        if event.state != WorkerState.SUCCESS:
            return

        if event.worker.name == "_load_initial_tickets":
            # Initial tickets loaded - update UI
            tickets = event.worker.result
            self._all_tickets = tickets
            self._on_initial_tickets_loaded()

            # Now load ALL tickets in background for filter changes
            if self._connected:
                self.run_worker(self._load_all_tickets, thread=True, exclusive=False)

        elif event.worker.name == "_load_all_tickets":
            # All tickets loaded - update cache
            tickets = event.worker.result
            if tickets:
                self._all_tickets = tickets
                self._all_tickets_loaded = True
                _log.info(f"Background load complete: {len(self._all_tickets)} total tickets")

        elif event.worker.name == "_fetch_filtered_tickets":
            # Filtered tickets fetched - update UI directly
            tickets = event.worker.result
            self._on_filtered_tickets_loaded(tickets)

    def _load_all_tickets(self) -> list:
        """Load all tickets in background thread."""
        _log.debug("Loading all tickets in background...")
        try:
            all_tickets = self._client.get_tickets(query="")
            return list(all_tickets)
        except Exception as e:
            _log.error(f"Failed to load all tickets: {e}")
            return []

    def _fetch_filtered_tickets(self) -> list:
        """Fetch tickets with current filter from server."""
        _log.debug(f"Fetching tickets for iteration filter: {self._iteration_filter}")
        try:
            # Build query for the selected iteration
            if self._iteration_filter == FILTER_BACKLOG:
                # Backlog = no iteration assigned
                query = '(Iteration = null)'
            elif self._iteration_filter:
                query = f'(Iteration.Name = "{self._iteration_filter}")'
            else:
                query = ""

            tickets = self._client.get_tickets(query=query)
            return list(tickets)
        except Exception as e:
            _log.error(f"Failed to fetch filtered tickets: {e}")
            return []

    def _on_initial_tickets_loaded(self) -> None:
        """Called when initial tickets are loaded async - update UI and dismiss splash."""
        ticket_list = self.query_one(TicketList)
        ticket_list.set_tickets(self._all_tickets)
        _log.debug(f"Loaded {len(self._all_tickets)} tickets")

        # Set first ticket in detail panel (from sorted list)
        if ticket_list.selected_ticket:
            detail = self.query_one(TicketDetail)
            detail.ticket = ticket_list.selected_ticket

        # Dismiss splash screen if showing
        if self._show_splash and len(self.screen_stack) > 1:
            self.pop_screen()

    def _on_initial_tickets_loaded_sync(self) -> None:
        """Called when initial tickets are loaded sync (no splash) - update UI."""
        ticket_list = self.query_one(TicketList)
        ticket_list.set_tickets(self._all_tickets)
        _log.debug(f"Loaded {len(self._all_tickets)} tickets (sync)")

        # Set first ticket in detail panel (from sorted list)
        if ticket_list.selected_ticket:
            detail = self.query_one(TicketDetail)
            detail.ticket = ticket_list.selected_ticket

    def _on_filtered_tickets_loaded(self, tickets: list) -> None:
        """Called when filtered tickets are loaded from server."""
        # Apply user filter if active
        if self._user_filter_active and self._client.current_user:
            tickets = [t for t in tickets if t.owner == self._client.current_user]

        # Update the ticket list
        ticket_list = self.query_one(TicketList)
        ticket_list.set_tickets(tickets)

        # Update status bar
        status_bar = self.query_one(StatusBar)
        if self._iteration_filter == FILTER_BACKLOG:
            status_bar.set_iteration_filter("Backlog")
        elif self._iteration_filter:
            status_bar.set_iteration_filter(self._iteration_filter)
        else:
            status_bar.set_iteration_filter(None)
        status_bar.set_user_filter(self._user_filter_active)

        # Update detail panel
        if tickets:
            detail = self.query_one(TicketDetail)
            if detail.ticket not in tickets:
                detail.ticket = tickets[0]
        else:
            detail = self.query_one(TicketDetail)
            detail.ticket = None

        # Show notification
        filter_desc = []
        if self._iteration_filter == FILTER_BACKLOG:
            filter_desc.append("Backlog")
        elif self._iteration_filter:
            filter_desc.append(self._iteration_filter)
        if self._user_filter_active:
            filter_desc.append("My Items")

        if filter_desc:
            self.notify(f"Filter: {', '.join(filter_desc)} ({len(tickets)} items)", timeout=2)
        else:
            self.notify(f"Showing all items ({len(tickets)})", timeout=2)

        _log.info(f"Filtered tickets loaded: {len(tickets)} items")

    def on_ticket_list_ticket_highlighted(
        self, event: TicketList.TicketHighlighted
    ) -> None:
        """Update detail panel when ticket highlight changes."""
        try:
            detail = self.query_one(TicketDetail)
            detail.ticket = event.ticket
        except Exception:
            # TicketDetail may not exist during initial setup
            pass

    def on_ticket_list_ticket_selected(
        self, event: TicketList.TicketSelected
    ) -> None:
        """Handle ticket selection (Enter key)."""
        self.log.info(f"Selected: {event.ticket.formatted_id}")

    def on_ticket_list_selection_changed(
        self, event: TicketList.SelectionChanged
    ) -> None:
        """Update status bar when multi-select changes."""
        status_bar = self.query_one(StatusBar)
        status_bar.set_selection_count(event.count)

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
        """Handle the result from StateScreen.

        If transitioning to "In-Progress" and ticket has no parent,
        prompts user to select a parent first.
        """
        if state is None:
            _log.debug("State update cancelled")
            return

        detail = self.query_one(TicketDetail)
        if not detail.ticket:
            return

        # Check if moving to "In-Progress" without a parent
        if state == "In-Progress" and not detail.ticket.parent_id:
            _log.info(f"Ticket {detail.ticket.formatted_id} needs parent before In-Progress")
            # Store the pending state and show parent selection screen
            self._pending_state = state
            parent_options = self._build_parent_options()

            # If no parent options configured, notify user and still show screen
            # (they can use custom ID input)
            if not parent_options:
                self.notify(
                    "No parent options configured. Use custom ID or configure parent_options in settings.",
                    severity="warning",
                    timeout=5,
                )

            self.push_screen(
                ParentScreen(detail.ticket, parent_options),
                callback=self._handle_parent_result,
            )
            return

        self._update_ticket_state(detail.ticket, state)

    def _build_parent_options(self) -> list[ParentOption]:
        """Build list of ParentOption from user settings and client data."""
        parent_ids = self._user_settings.parent_options
        options: list[ParentOption] = []

        for parent_id in parent_ids:
            feature = self._client.get_feature(parent_id)
            if feature:
                options.append(ParentOption(feature[0], feature[1]))
            else:
                # Include ID even if we can't get the name (feature might not exist)
                options.append(ParentOption(parent_id, f"(not found) {parent_id}"))

        # If no valid features found, show helpful message
        if all("(not found)" in opt.name for opt in options):
            _log.warning(
                "No configured parent Features found. "
                "Update parent_options in ~/.config/rally-tui/config.json"
            )

        return options

    def _handle_parent_result(self, parent_id: str | None) -> None:
        """Handle the result from ParentScreen.

        If a parent was selected, sets the parent and then updates the state.
        """
        if parent_id is None:
            _log.debug("Parent selection cancelled")
            self._pending_state = None
            return

        detail = self.query_one(TicketDetail)
        if not detail.ticket:
            self._pending_state = None
            return

        ticket_id = detail.ticket.formatted_id
        _log.info(f"Setting parent for {ticket_id} to {parent_id}")

        try:
            # Set the parent
            updated = self._client.set_parent(detail.ticket, parent_id)
            if updated:
                # Update detail and list with parent set
                detail.ticket = updated
                ticket_list = self.query_one(TicketList)
                ticket_list.update_ticket(updated, resort=False)
                self.notify(f"Parent set to {parent_id}", timeout=2)
                _log.info(f"Parent set successfully for {ticket_id}")

                # Now update the state if we have a pending state
                if self._pending_state:
                    pending = self._pending_state
                    self._pending_state = None
                    self._update_ticket_state(updated, pending)
            else:
                _log.error(f"Failed to set parent for {ticket_id}")
                self.notify("Failed to set parent", severity="error", timeout=3)
                self._pending_state = None
        except Exception as e:
            _log.exception(f"Error setting parent for {ticket_id}: {e}")
            self.notify("Failed to set parent", severity="error", timeout=3)
            self._pending_state = None

    def _update_ticket_state(self, ticket: "Ticket", state: str) -> None:
        """Update a ticket's state and refresh the UI."""
        ticket_id = ticket.formatted_id
        _log.info(f"Updating state for {ticket_id} to {state}")

        try:
            updated = self._client.update_state(ticket, state)
            if updated:
                # Update the detail panel with new ticket data
                detail = self.query_one(TicketDetail)
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

    def action_iteration_filter(self) -> None:
        """Open the iteration filter screen."""
        iterations = self._client.get_iterations()
        self.push_screen(
            IterationScreen(iterations, current_filter=self._iteration_filter),
            callback=self._handle_iteration_filter_result,
        )

    def _handle_iteration_filter_result(self, result: str | None) -> None:
        """Handle the result from IterationScreen."""
        if result is None:
            _log.debug("Iteration filter cancelled")
            return

        # Update iteration filter state
        if result == FILTER_ALL:
            self._iteration_filter = None
            _log.info("Iteration filter cleared (showing all)")
        elif result == FILTER_BACKLOG:
            self._iteration_filter = FILTER_BACKLOG
            _log.info("Iteration filter set to Backlog")
        else:
            self._iteration_filter = result
            _log.info(f"Iteration filter set to: {result}")

        self._apply_filters()

    def action_toggle_user_filter(self) -> None:
        """Toggle the user filter (My Items)."""
        self._user_filter_active = not self._user_filter_active
        _log.info(f"User filter {'enabled' if self._user_filter_active else 'disabled'}")
        self._apply_filters()

    def action_cycle_sort(self) -> None:
        """Cycle through sort modes: State → Created → Owner → State."""
        ticket_list = self.query_one(TicketList)
        current = ticket_list.sort_mode

        # Cycle to next mode
        if current == SortMode.STATE:
            next_mode = SortMode.CREATED
        elif current == SortMode.CREATED:
            next_mode = SortMode.OWNER
        else:
            next_mode = SortMode.STATE

        ticket_list.set_sort_mode(next_mode)

        # Update status bar
        status_bar = self.query_one(StatusBar)
        status_bar.set_sort_mode(next_mode)

        # Notify user
        mode_names = {
            SortMode.STATE: "State Flow",
            SortMode.CREATED: "Recently Created",
            SortMode.OWNER: "Owner",
        }
        self.notify(f"Sort: {mode_names[next_mode]}", timeout=2)
        _log.info(f"Sort mode changed to {next_mode.value}")

    def action_bulk_actions(self) -> None:
        """Open bulk actions menu if tickets are selected."""
        ticket_list = self.query_one(TicketList)
        if ticket_list.selection_count == 0:
            self.notify("No tickets selected. Use Space to select.", timeout=2)
            return

        self.push_screen(
            BulkActionsScreen(ticket_list.selection_count),
            callback=self._handle_bulk_action_result,
        )

    def _handle_bulk_action_result(self, action: BulkAction | None) -> None:
        """Handle the selected bulk action."""
        if action is None:
            _log.debug("Bulk action cancelled")
            return

        ticket_list = self.query_one(TicketList)
        selected = ticket_list.selected_tickets

        if not selected:
            self.notify("No tickets selected", severity="warning", timeout=2)
            return

        _log.info(f"Bulk action {action.value} on {len(selected)} tickets")

        if action == BulkAction.SET_PARENT:
            self._bulk_set_parent(selected)
        elif action == BulkAction.SET_STATE:
            self._bulk_set_state(selected)
        elif action == BulkAction.SET_ITERATION:
            self._bulk_set_iteration(selected)
        elif action == BulkAction.SET_POINTS:
            self._bulk_set_points(selected)

    def _bulk_set_parent(self, tickets: list[Ticket]) -> None:
        """Set parent on multiple tickets."""
        # Get parent options from settings
        parent_ids = self._user_settings.parent_options
        parent_options: list[ParentOption] = []

        for pid in parent_ids:
            feature = self._client.get_feature(pid)
            if feature:
                parent_options.append(ParentOption(formatted_id=feature[0], name=feature[1]))

        # Use the first ticket for display purposes
        self.push_screen(
            ParentScreen(tickets[0], parent_options),
            callback=lambda parent_id: self._execute_bulk_parent(tickets, parent_id),
        )

    def _execute_bulk_parent(self, tickets: list[Ticket], parent_id: str | None) -> None:
        """Execute bulk parent assignment."""
        if parent_id is None:
            _log.debug("Bulk parent cancelled")
            return

        self.notify(f"Setting parent {parent_id} on {len(tickets)} tickets...", timeout=2)

        result = self._client.bulk_set_parent(tickets, parent_id)
        self._handle_bulk_result(result, "parent")

    def _bulk_set_state(self, tickets: list[Ticket]) -> None:
        """Set state on multiple tickets."""
        # Use the first ticket for display purposes
        self.push_screen(
            StateScreen(tickets[0]),
            callback=lambda state: self._execute_bulk_state(tickets, state),
        )

    def _execute_bulk_state(self, tickets: list[Ticket], state: str | None) -> None:
        """Execute bulk state update."""
        if state is None:
            _log.debug("Bulk state cancelled")
            return

        # For In-Progress state, filter to only tickets with parents
        if state == "In-Progress":
            eligible = [t for t in tickets if t.parent_id]
            skipped = len(tickets) - len(eligible)
            if skipped > 0:
                self.notify(f"Skipping {skipped} tickets without parent", timeout=2)
            if not eligible:
                self.notify("No tickets have parents set", severity="warning", timeout=3)
                return
            tickets = eligible

        self.notify(f"Setting state to {state} on {len(tickets)} tickets...", timeout=2)

        result = self._client.bulk_update_state(tickets, state)
        self._handle_bulk_result(result, "state")

    def _bulk_set_iteration(self, tickets: list[Ticket]) -> None:
        """Set iteration on multiple tickets."""
        iterations = self._client.get_iterations()
        self.push_screen(
            IterationScreen(iterations, current_filter=None),
            callback=lambda iter_name: self._execute_bulk_iteration(tickets, iter_name),
        )

    def _execute_bulk_iteration(self, tickets: list[Ticket], iteration: str | None) -> None:
        """Execute bulk iteration update."""
        if iteration is None:
            _log.debug("Bulk iteration cancelled")
            return

        # Handle special filter values
        if iteration == FILTER_ALL:
            iteration = None  # Remove iteration (backlog)
        elif iteration == FILTER_BACKLOG:
            iteration = None  # Same as backlog

        iter_name = iteration or "Backlog"
        self.notify(f"Moving {len(tickets)} tickets to {iter_name}...", timeout=2)

        result = self._client.bulk_set_iteration(tickets, iteration)
        self._handle_bulk_result(result, "iteration")

    def _bulk_set_points(self, tickets: list[Ticket]) -> None:
        """Set points on multiple tickets."""
        # Use the first ticket for display purposes
        self.push_screen(
            PointsScreen(tickets[0]),
            callback=lambda points: self._execute_bulk_points(tickets, points),
        )

    def _execute_bulk_points(self, tickets: list[Ticket], points: float | None) -> None:
        """Execute bulk points update."""
        if points is None:
            _log.debug("Bulk points cancelled")
            return

        self.notify(f"Setting {points} points on {len(tickets)} tickets...", timeout=2)

        result = self._client.bulk_update_points(tickets, points)
        self._handle_bulk_result(result, "points")

    def _handle_bulk_result(self, result: BulkResult, operation: str) -> None:
        """Handle the result of a bulk operation."""
        ticket_list = self.query_one(TicketList)

        # Update all tickets at once (batched to avoid UI rebuild issues)
        ticket_list.update_tickets(result.updated_tickets)

        # Clear selection after bulk operation
        ticket_list.clear_selection()

        # Notify user of result
        if result.failed_count == 0:
            self.notify(
                f"Updated {operation} on {result.success_count} tickets",
                timeout=3,
            )
            _log.info(f"Bulk {operation}: {result.success_count} success")
        else:
            self.notify(
                f"{result.success_count} updated, {result.failed_count} failed",
                severity="warning",
                timeout=5,
            )
            _log.warning(f"Bulk {operation}: {result.success_count} success, {result.failed_count} failed")
            for error in result.errors[:3]:  # Show first 3 errors
                _log.warning(f"  {error}")

    def action_open_settings(self) -> None:
        """Open the settings configuration screen."""
        self.push_screen(
            ConfigScreen(self._user_settings),
            callback=self._handle_settings_result,
        )

    def _handle_settings_result(self, result: ConfigData | None) -> None:
        """Handle the result from ConfigScreen."""
        if result is None:
            _log.debug("Settings cancelled")
            return

        _log.info(f"Settings saved: theme={result.theme_name}, log_level={result.log_level}")

        # Apply theme immediately if changed
        if result.theme_name in self.available_themes:
            self.theme = result.theme_name

        # Note: Log level change takes effect on next startup
        self.notify("Settings saved", timeout=2)

    def _apply_filters(self) -> None:
        """Apply iteration and user filters to the ticket list."""
        # When connected to Rally, always fetch from server when changing iteration filter
        # This ensures Rally does the matching (avoids string mismatch issues)
        if self._connected and self._iteration_filter:
            _log.debug(f"Fetching from server for iteration filter: {self._iteration_filter}")
            self.notify("Loading tickets...", timeout=1)
            self.run_worker(self._fetch_filtered_tickets, thread=True)
            return

        # For offline mode or no iteration filter, filter locally
        filtered = list(self._all_tickets)

        # Apply iteration filter
        if self._iteration_filter == FILTER_BACKLOG:
            # Show only tickets with no iteration (backlog)
            filtered = [t for t in filtered if not t.iteration]
        elif self._iteration_filter:
            # Show only tickets in the specified iteration
            filtered = [t for t in filtered if t.iteration == self._iteration_filter]

        # Apply user filter
        if self._user_filter_active and self._client.current_user:
            filtered = [t for t in filtered if t.owner == self._client.current_user]

        # Update the ticket list
        ticket_list = self.query_one(TicketList)
        ticket_list.set_tickets(filtered)

        # Update status bar
        status_bar = self.query_one(StatusBar)

        # Set iteration filter display
        if self._iteration_filter == FILTER_BACKLOG:
            status_bar.set_iteration_filter("Backlog")
        elif self._iteration_filter:
            status_bar.set_iteration_filter(self._iteration_filter)
        else:
            status_bar.set_iteration_filter(None)

        # Set user filter display
        status_bar.set_user_filter(self._user_filter_active)

        # Update detail panel
        if filtered:
            detail = self.query_one(TicketDetail)
            if detail.ticket not in filtered:
                detail.ticket = filtered[0]
        else:
            detail = self.query_one(TicketDetail)
            detail.ticket = None

        # Show notification
        filter_desc = []
        if self._iteration_filter == FILTER_BACKLOG:
            filter_desc.append("Backlog")
        elif self._iteration_filter:
            filter_desc.append(self._iteration_filter)
        if self._user_filter_active:
            filter_desc.append("My Items")

        if filter_desc:
            self.notify(f"Filter: {', '.join(filter_desc)} ({len(filtered)} items)", timeout=2)
        else:
            self.notify(f"Showing all items ({len(filtered)})", timeout=2)


def main() -> None:
    """Entry point for the application.

    Loads configuration from environment variables and starts the app.
    If RALLY_APIKEY is set, attempts to connect to Rally.
    Otherwise, runs in offline mode with sample data.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        prog="rally-tui",
        description="A terminal user interface for Rally work items.",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.parse_args()

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
