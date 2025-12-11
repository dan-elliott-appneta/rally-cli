"""Ticket list widget with keyboard navigation."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Label, ListItem, ListView

from rally_tui.models import Ticket


class TicketListItem(ListItem):
    """A single ticket item in the list."""

    def __init__(self, ticket: Ticket) -> None:
        super().__init__()
        self.ticket = ticket

    def compose(self) -> ComposeResult:
        """Create the ticket display label."""
        type_class = f"ticket-{self.ticket.type_prefix.lower()}"
        yield Label(
            self.ticket.display_text,
            classes=type_class,
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
        self._tickets = tickets or []
        self._all_tickets = list(self._tickets)
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
        self._tickets = tickets
        self._all_tickets = list(tickets)
        self._filter_query = ""
        self.clear()
        for ticket in tickets:
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
