"""Ticket list widget with keyboard navigation."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Label, ListItem, ListView
from textual.containers import Horizontal

from rally_tui.models import Ticket


# State ordering from earliest (top) to latest (bottom) in workflow
# Lower number = earlier in workflow = displayed first
STATE_ORDER: dict[str, int] = {
    # Idea/Backlog states
    "Idea": 0,
    "Submitted": 1,
    "Backlog": 2,
    # Definition states
    "Defined": 10,
    "Ready": 11,
    "Groomed": 12,
    # Open/Active states
    "Open": 20,
    "In Progress": 30,
    "In Development": 31,
    "In Review": 32,
    "In Test": 33,
    # Completed states
    "Completed": 40,
    "Done": 41,
    "Closed": 42,
    "Accepted": 50,
}

# Colors for each state (first letter indicator)
STATE_COLORS: dict[str, str] = {
    # Idea/Backlog - gray
    "Idea": "gray",
    "Submitted": "gray",
    "Backlog": "gray",
    # Definition - blue
    "Defined": "dodger_blue",
    "Ready": "dodger_blue",
    "Groomed": "dodger_blue",
    # Open - yellow/orange
    "Open": "orange",
    "In Progress": "yellow",
    "In Development": "yellow",
    "In Review": "cyan",
    "In Test": "magenta",
    # Completed - green
    "Completed": "green",
    "Done": "green",
    "Closed": "green",
    "Accepted": "bright_green",
}

DEFAULT_STATE_ORDER = 99  # Unknown states go at the bottom
DEFAULT_STATE_COLOR = "white"


def get_state_order(state: str | None) -> int:
    """Get sort order for a state. Lower = earlier in workflow."""
    if not state:
        return DEFAULT_STATE_ORDER
    return STATE_ORDER.get(state, DEFAULT_STATE_ORDER)


def get_state_color(state: str | None) -> str:
    """Get color for a state indicator."""
    if not state:
        return DEFAULT_STATE_COLOR
    return STATE_COLORS.get(state, DEFAULT_STATE_COLOR)


def sort_tickets_by_state(tickets: list[Ticket]) -> list[Ticket]:
    """Sort tickets by state order (earliest first)."""
    return sorted(tickets, key=lambda t: get_state_order(t.state))


class TicketListItem(ListItem):
    """A single ticket item in the list."""

    def __init__(self, ticket: Ticket) -> None:
        super().__init__()
        self.ticket = ticket

    def compose(self) -> ComposeResult:
        """Create the ticket display with state indicator."""
        type_class = f"ticket-{self.ticket.type_prefix.lower()}"
        state_color = get_state_color(self.ticket.state)
        state_letter = (self.ticket.state or "?")[0].upper()

        with Horizontal(classes="ticket-row"):
            yield Label(
                f"[{state_color}]{state_letter}[/]",
                classes="state-indicator",
            )
            yield Label(
                self.ticket.display_text,
                classes=f"ticket-text {type_class}",
            )


class TicketList(ListView):
    """Scrollable list of tickets with keyboard navigation.

    Extends Textual's ListView to add vim-style keybindings
    and emit custom messages when selection changes.
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
    ]

    class TicketHighlighted(Message):
        """Posted when a ticket is highlighted (cursor moved)."""

        def __init__(self, ticket: Ticket | None) -> None:
            self.ticket = ticket
            super().__init__()

    class TicketSelected(Message):
        """Posted when a ticket is selected (Enter pressed)."""

        def __init__(self, ticket: Ticket) -> None:
            self.ticket = ticket
            super().__init__()

    class FilterApplied(Message):
        """Posted when filter is applied."""

        def __init__(self, filtered: int, total: int) -> None:
            self.filtered = filtered
            self.total = total
            super().__init__()

    def __init__(
        self,
        tickets: list[Ticket] | None = None,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the ticket list.

        Args:
            tickets: List of tickets to display. If None, list is empty.
            id: Widget ID for CSS targeting.
            classes: CSS classes to apply.
        """
        super().__init__(id=id, classes=classes)
        # Sort tickets by state order
        sorted_tickets = sort_tickets_by_state(tickets or [])
        self._tickets = sorted_tickets
        self._all_tickets = list(sorted_tickets)
        self._filter_query = ""

    def compose(self) -> ComposeResult:
        """Create list items for each ticket."""
        for ticket in self._tickets:
            yield TicketListItem(ticket)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle highlight changes and emit our custom message."""
        ticket = None
        if event.item is not None and isinstance(event.item, TicketListItem):
            ticket = event.item.ticket
        self.post_message(self.TicketHighlighted(ticket))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection (Enter key) and emit our custom message."""
        if isinstance(event.item, TicketListItem):
            self.post_message(self.TicketSelected(event.item.ticket))

    def action_scroll_home(self) -> None:
        """Jump to the first item (vim 'g' key)."""
        if len(self._tickets) > 0:
            self.index = 0

    def action_scroll_end(self) -> None:
        """Jump to the last item (vim 'G' key)."""
        if len(self._tickets) > 0:
            self.index = len(self._tickets) - 1

    @property
    def selected_ticket(self) -> Ticket | None:
        """Get the currently highlighted ticket."""
        if self.index is not None and 0 <= self.index < len(self._tickets):
            return self._tickets[self.index]
        return None

    def set_tickets(self, tickets: list[Ticket]) -> None:
        """Replace the ticket list with new data."""
        sorted_tickets = sort_tickets_by_state(tickets)
        self._tickets = sorted_tickets
        self._all_tickets = list(sorted_tickets)
        self._filter_query = ""
        self.clear()
        for ticket in sorted_tickets:
            self.append(TicketListItem(ticket))

    def filter_tickets(self, query: str) -> None:
        """Filter the ticket list by query.

        Args:
            query: Search query (case-insensitive, matches ID, title, owner, state).
                   Empty string shows all tickets.
        """
        self._filter_query = query

        if not query:
            filtered = self._all_tickets
        else:
            query_lower = query.lower()
            filtered = [
                t for t in self._all_tickets if self._matches_query(t, query_lower)
            ]

        self._tickets = filtered
        self.clear()
        for ticket in filtered:
            self.append(TicketListItem(ticket))

        self.post_message(self.FilterApplied(len(filtered), len(self._all_tickets)))

    def _matches_query(self, ticket: Ticket, query: str) -> bool:
        """Check if ticket matches search query."""
        searchable = " ".join(
            [
                ticket.formatted_id.lower(),
                ticket.name.lower(),
                (ticket.owner or "").lower(),
                (ticket.state or "").lower(),
            ]
        )
        return query in searchable

    def clear_filter(self) -> None:
        """Clear filter and show all tickets."""
        self.filter_tickets("")

    @property
    def filter_query(self) -> str:
        """Get current filter query."""
        return self._filter_query

    @property
    def total_count(self) -> int:
        """Get total ticket count (unfiltered)."""
        return len(self._all_tickets)

    @property
    def filtered_count(self) -> int:
        """Get filtered ticket count."""
        return len(self._tickets)
