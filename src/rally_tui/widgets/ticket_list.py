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
        self.clear()
        for ticket in tickets:
            self.append(TicketListItem(ticket))
