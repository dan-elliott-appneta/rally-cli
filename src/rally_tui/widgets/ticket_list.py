"""Ticket list widget with keyboard navigation."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Label, ListItem, ListView
from textual.containers import Horizontal

from rally_tui.models import Ticket

if TYPE_CHECKING:
    from rally_tui.user_settings import UserSettings


class SortMode(Enum):
    """Available sort modes for the ticket list."""

    STATE = "state"  # By state flow (Defined → In-Progress → Completed)
    CREATED = "created"  # By most recently created (newest first)
    OWNER = "owner"  # By owner name (unassigned first, then alphabetical)


class ViewMode(Enum):
    """Available view modes for the ticket list."""

    NORMAL = "normal"  # Default compact view
    WIDE = "wide"  # Expanded view with owner, points, parent columns


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
    "In-Progress": 30,  # Rally variant with hyphen
    "In Development": 31,
    "In Review": 32,
    "In Test": 33,
    # Completed states
    "Completed": 40,
    "Done": 41,
    "Closed": 42,
    "Accepted": 50,
}

# Colors for each state indicator
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
    "In-Progress": "yellow",  # Rally variant with hyphen
    "In Development": "yellow",
    "In Review": "cyan",
    "In Test": "magenta",
    # Completed - green
    "Completed": "green",
    "Done": "green",
    "Closed": "green",
    "Accepted": "bold green",
}

# Symbols for each state indicator
STATE_SYMBOLS: dict[str, str] = {
    # Idea/Backlog/Defined - period (not started)
    "Idea": ".",
    "Submitted": ".",
    "Backlog": ".",
    "Defined": ".",
    "Ready": ".",
    "Groomed": ".",
    # Open/In Progress - plus (active work)
    "Open": "+",
    "In Progress": "+",
    "In-Progress": "+",  # Rally variant with hyphen
    "In Development": "+",
    "In Review": "+",
    "In Test": "+",
    # Completed/Done - dash (done)
    "Completed": "-",
    "Done": "-",
    "Closed": "-",
    # Accepted - checkmark (verified)
    "Accepted": "✓",
}

DEFAULT_STATE_ORDER = 99  # Unknown states go at the bottom
DEFAULT_STATE_COLOR = "white"
DEFAULT_STATE_SYMBOL = "?"


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


def get_state_symbol(state: str | None) -> str:
    """Get symbol for a state indicator."""
    if not state:
        return DEFAULT_STATE_SYMBOL
    return STATE_SYMBOLS.get(state, DEFAULT_STATE_SYMBOL)


def sort_tickets_by_state(tickets: list[Ticket]) -> list[Ticket]:
    """Sort tickets by state order (earliest first)."""
    return sorted(tickets, key=lambda t: get_state_order(t.state))


def sort_tickets_by_created(tickets: list[Ticket]) -> list[Ticket]:
    """Sort tickets by creation date (newest first).

    Uses FormattedID as a proxy for creation order since higher IDs
    are assigned to newer tickets.
    """
    def get_id_number(ticket: Ticket) -> int:
        """Extract numeric part of FormattedID for sorting."""
        # Extract digits from FormattedID (e.g., "US1234" -> 1234)
        digits = "".join(c for c in ticket.formatted_id if c.isdigit())
        return int(digits) if digits else 0

    return sorted(tickets, key=get_id_number, reverse=True)


def sort_tickets_by_owner(tickets: list[Ticket]) -> list[Ticket]:
    """Sort tickets by owner name (unassigned first, then alphabetical)."""
    def get_owner_key(ticket: Ticket) -> tuple[int, str]:
        """Return sort key: (0, "") for None, (1, name) for assigned."""
        if ticket.owner is None:
            return (0, "")
        return (1, ticket.owner.lower())

    return sorted(tickets, key=get_owner_key)


def sort_tickets(tickets: list[Ticket], mode: SortMode) -> list[Ticket]:
    """Sort tickets by the specified mode.

    Args:
        tickets: List of tickets to sort.
        mode: The sort mode to use.

    Returns:
        Sorted list of tickets.
    """
    if mode == SortMode.STATE:
        return sort_tickets_by_state(tickets)
    elif mode == SortMode.CREATED:
        return sort_tickets_by_created(tickets)
    elif mode == SortMode.OWNER:
        return sort_tickets_by_owner(tickets)
    else:
        return sort_tickets_by_state(tickets)


class TicketListItem(ListItem):
    """A single ticket item in the list."""

    def __init__(self, ticket: Ticket, selected: bool = False) -> None:
        super().__init__()
        self.ticket = ticket
        self._selected = selected

    def compose(self) -> ComposeResult:
        """Create the ticket display with selection checkbox and state indicator."""
        type_class = f"ticket-{self.ticket.type_prefix.lower()}"
        state_color = get_state_color(self.ticket.state)
        state_symbol = get_state_symbol(self.ticket.state)
        checkbox = "[✓]" if self._selected else "[ ]"

        with Horizontal(classes="ticket-row"):
            yield Label(
                checkbox,
                classes="selection-checkbox",
            )
            yield Label(
                f"[{state_color}]{state_symbol}[/]",
                classes="state-indicator",
            )
            yield Label(
                self.ticket.display_text,
                classes=f"ticket-text {type_class}",
            )

    def set_selected(self, selected: bool) -> None:
        """Update selection state and refresh checkbox display."""
        if self._selected == selected:
            return
        self._selected = selected
        checkbox = "[✓]" if selected else "[ ]"
        try:
            label = self.query_one(".selection-checkbox", Label)
            label.update(checkbox)
        except Exception:
            pass  # Widget may not be mounted yet

    @property
    def is_selected(self) -> bool:
        """Check if this item is selected."""
        return self._selected


class WideTicketListItem(ListItem):
    """A ticket item with additional columns for wide view mode."""

    def __init__(self, ticket: Ticket, selected: bool = False) -> None:
        super().__init__()
        self.ticket = ticket
        self._selected = selected

    def compose(self) -> ComposeResult:
        """Create the ticket display with additional columns."""
        type_class = f"ticket-{self.ticket.type_prefix.lower()}"
        state_color = get_state_color(self.ticket.state)
        state_symbol = get_state_symbol(self.ticket.state)
        checkbox = "[✓]" if self._selected else "[ ]"

        # Format points display (show decimal only if not a whole number)
        if self.ticket.points is not None:
            if self.ticket.points == int(self.ticket.points):
                points_str = str(int(self.ticket.points))
            else:
                points_str = str(self.ticket.points)
        else:
            points_str = "-"

        # Format owner display (truncate long names)
        owner_str = self.ticket.owner[:18] if self.ticket.owner else "-"

        # Format parent ID display
        parent_str = self.ticket.parent_id if self.ticket.parent_id else "-"

        with Horizontal(classes="ticket-row-wide"):
            yield Label(
                checkbox,
                classes="selection-checkbox",
            )
            yield Label(
                f"[{state_color}]{state_symbol}[/]",
                classes="state-indicator",
            )
            yield Label(
                self.ticket.display_text,
                classes=f"ticket-text-wide {type_class}",
            )
            yield Label(
                owner_str,
                classes="ticket-owner",
            )
            yield Label(
                points_str,
                classes="ticket-points",
            )
            yield Label(
                parent_str,
                classes="ticket-parent",
            )

    def set_selected(self, selected: bool) -> None:
        """Update selection state and refresh checkbox display."""
        if self._selected == selected:
            return
        self._selected = selected
        checkbox = "[✓]" if selected else "[ ]"
        try:
            label = self.query_one(".selection-checkbox", Label)
            label.update(checkbox)
        except Exception:
            pass  # Widget may not be mounted yet

    @property
    def is_selected(self) -> bool:
        """Check if this item is selected."""
        return self._selected


class TicketList(ListView):
    """Scrollable list of tickets with keyboard navigation.

    Extends Textual's ListView to add vim-style keybindings
    and emit custom messages when selection changes.
    """

    # Only non-configurable bindings here
    # Configurable bindings (j/k/g/G) are applied dynamically in on_mount
    BINDINGS = [
        Binding("space", "toggle_selection", "Select", show=False),
        Binding("ctrl+a", "select_all", "Select All", show=False),
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

    class SelectionChanged(Message):
        """Posted when multi-select selection changes."""

        def __init__(self, count: int, selected_ids: set[str]) -> None:
            self.count = count
            self.selected_ids = selected_ids
            super().__init__()

    class ViewModeChanged(Message):
        """Posted when view mode changes."""

        def __init__(self, mode: ViewMode) -> None:
            self.mode = mode
            super().__init__()

    def __init__(
        self,
        tickets: list[Ticket] | None = None,
        *,
        id: str | None = None,
        classes: str | None = None,
        sort_mode: SortMode = SortMode.STATE,
        view_mode: ViewMode = ViewMode.NORMAL,
        user_settings: UserSettings | None = None,
    ) -> None:
        """Initialize the ticket list.

        Args:
            tickets: List of tickets to display. If None, list is empty.
            id: Widget ID for CSS targeting.
            classes: CSS classes to apply.
            sort_mode: How to sort the tickets.
            view_mode: Display mode (NORMAL or WIDE).
            user_settings: User settings for dynamic keybindings.
        """
        super().__init__(id=id, classes=classes)
        self._sort_mode = sort_mode
        self._view_mode = view_mode
        self._user_settings = user_settings
        # Sort tickets by the specified mode
        sorted_tickets = sort_tickets(tickets or [], self._sort_mode)
        self._tickets = sorted_tickets
        self._all_tickets = list(sorted_tickets)
        self._filter_query = ""
        # Multi-select tracking
        self._selected_ids: set[str] = set()

    def _create_list_item(self, ticket: Ticket, selected: bool = False) -> ListItem:
        """Create appropriate list item based on view mode."""
        if self._view_mode == ViewMode.WIDE:
            return WideTicketListItem(ticket, selected=selected)
        return TicketListItem(ticket, selected=selected)

    def compose(self) -> ComposeResult:
        """Create list items for each ticket."""
        for ticket in self._tickets:
            is_selected = ticket.formatted_id in self._selected_ids
            yield self._create_list_item(ticket, selected=is_selected)

    def on_mount(self) -> None:
        """Apply dynamic keybindings on mount."""
        self._apply_keybindings()

    def _apply_keybindings(self) -> None:
        """Apply keybindings from user settings."""
        from rally_tui.utils.keybindings import VIM_KEYBINDINGS

        # Get keybindings from settings or use vim defaults
        if self._user_settings:
            keybindings = self._user_settings.keybindings
        else:
            keybindings = VIM_KEYBINDINGS

        # Navigation bindings for TicketList
        navigation_bindings = {
            "navigation.down": "cursor_down",
            "navigation.up": "cursor_up",
            "navigation.top": "scroll_home",
            "navigation.bottom": "scroll_end",
        }

        for action_id, handler in navigation_bindings.items():
            if action_id in keybindings:
                key = keybindings[action_id]
                self._bindings.bind(key, handler, show=False)

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

    def action_toggle_selection(self) -> None:
        """Toggle selection on current ticket (Space key)."""
        if not self.selected_ticket:
            return

        ticket_id = self.selected_ticket.formatted_id
        if ticket_id in self._selected_ids:
            self._selected_ids.discard(ticket_id)
        else:
            self._selected_ids.add(ticket_id)

        # Update the checkbox display for current item
        self._update_item_selection(ticket_id)
        self.post_message(self.SelectionChanged(len(self._selected_ids), set(self._selected_ids)))

    def action_select_all(self) -> None:
        """Select all visible tickets, or deselect all if all are selected (Ctrl+A)."""
        if len(self._selected_ids) == len(self._tickets) and len(self._tickets) > 0:
            # All selected, deselect all
            self.clear_selection()
        else:
            # Select all
            self._selected_ids = {t.formatted_id for t in self._tickets}
            self._update_all_selection_display()
            self.post_message(self.SelectionChanged(len(self._selected_ids), set(self._selected_ids)))

    def clear_selection(self) -> None:
        """Clear all selections."""
        if not self._selected_ids:
            return
        self._selected_ids.clear()
        self._update_all_selection_display()
        self.post_message(self.SelectionChanged(0, set()))

    def _update_item_selection(self, ticket_id: str) -> None:
        """Update checkbox display for a specific ticket."""
        is_selected = ticket_id in self._selected_ids
        for item in self.query(TicketListItem):
            if item.ticket.formatted_id == ticket_id:
                item.set_selected(is_selected)
                break

    def _update_all_selection_display(self) -> None:
        """Update checkbox display for all items."""
        for item in self.query(TicketListItem):
            is_selected = item.ticket.formatted_id in self._selected_ids
            item.set_selected(is_selected)

    @property
    def selected_tickets(self) -> list[Ticket]:
        """Get list of selected tickets (multi-select)."""
        return [t for t in self._tickets if t.formatted_id in self._selected_ids]

    @property
    def selection_count(self) -> int:
        """Get count of selected tickets."""
        return len(self._selected_ids)

    @property
    def selected_ticket(self) -> Ticket | None:
        """Get the currently highlighted ticket."""
        if self.index is not None and 0 <= self.index < len(self._tickets):
            return self._tickets[self.index]
        return None

    @property
    def sort_mode(self) -> SortMode:
        """Get the current sort mode."""
        return self._sort_mode

    @property
    def view_mode(self) -> ViewMode:
        """Get the current view mode."""
        return self._view_mode

    def set_view_mode(self, mode: ViewMode) -> None:
        """Change the view mode and rebuild the list.

        Args:
            mode: The new view mode (NORMAL or WIDE).
        """
        if mode == self._view_mode:
            return

        self._view_mode = mode

        # Rebuild the list with new item type
        current_index = self.index
        self.remove_children()
        for ticket in self._tickets:
            is_selected = ticket.formatted_id in self._selected_ids
            self.mount(self._create_list_item(ticket, selected=is_selected))

        # Restore index
        if current_index is not None and self._tickets:
            self.index = min(current_index, len(self._tickets) - 1)

        # Notify about the change
        self.post_message(self.ViewModeChanged(mode))

    def toggle_view_mode(self) -> None:
        """Toggle between NORMAL and WIDE view modes."""
        new_mode = ViewMode.WIDE if self._view_mode == ViewMode.NORMAL else ViewMode.NORMAL
        self.set_view_mode(new_mode)

    def set_tickets(self, tickets: list[Ticket]) -> None:
        """Replace the ticket list with new data."""
        sorted_tickets = sort_tickets(tickets, self._sort_mode)
        self._tickets = sorted_tickets
        self._all_tickets = list(sorted_tickets)
        self._filter_query = ""
        # Clear selection when tickets are replaced
        had_selection = bool(self._selected_ids)
        self._selected_ids.clear()
        # Use remove_children/mount for synchronous update to avoid race conditions
        # (clear/append can have timing issues when called from worker callbacks)
        self.remove_children()
        for ticket in sorted_tickets:
            self.mount(self._create_list_item(ticket, selected=False))
        # Select first item if list is not empty
        if sorted_tickets:
            self.index = 0
        # Notify if selection was cleared
        if had_selection:
            self.post_message(self.SelectionChanged(0, set()))

    def set_sort_mode(self, mode: SortMode) -> None:
        """Change the sort mode and re-sort the current tickets.

        Args:
            mode: The new sort mode to use.
        """
        if mode == self._sort_mode:
            return

        self._sort_mode = mode
        # Re-sort the all_tickets list
        self._all_tickets = sort_tickets(self._all_tickets, mode)

        # Re-apply any active filter with new sort order
        if self._filter_query:
            query_lower = self._filter_query.lower()
            self._tickets = [
                t for t in self._all_tickets if self._matches_query(t, query_lower)
            ]
        else:
            self._tickets = list(self._all_tickets)

        # Refresh the display (preserve selection state)
        self.clear()
        for ticket in self._tickets:
            is_selected = ticket.formatted_id in self._selected_ids
            self.append(self._create_list_item(ticket, selected=is_selected))

        # Select first item if list is not empty
        if self._tickets:
            self.index = 0

    def filter_tickets(self, query: str) -> None:
        """Filter the ticket list by query.

        Args:
            query: Search query (case-insensitive, matches ID, title, owner, state).
                   Empty string shows all tickets.
        """
        self._filter_query = query

        if not query:
            filtered = list(self._all_tickets)
        else:
            query_lower = query.lower()
            filtered = [
                t for t in self._all_tickets if self._matches_query(t, query_lower)
            ]

        self._tickets = filtered
        # Use remove_children/mount for synchronous update to avoid race conditions
        self.remove_children()
        for ticket in filtered:
            is_selected = ticket.formatted_id in self._selected_ids
            self.mount(self._create_list_item(ticket, selected=is_selected))

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

    @property
    def filtered_tickets(self) -> list[Ticket]:
        """Get the list of currently displayed (filtered) tickets."""
        return list(self._tickets)

    def update_ticket(self, ticket: Ticket, resort: bool = True) -> None:
        """Update a ticket and optionally re-sort the list.

        Args:
            ticket: The updated ticket (matched by formatted_id).
            resort: If True, re-sort and rebuild the list (for state changes).
        """
        self.update_tickets([ticket], resort=resort)

    def update_tickets(self, tickets: list[Ticket], resort: bool = True) -> None:
        """Update multiple tickets and optionally re-sort the list.

        This method batches updates to avoid UI rebuild issues when updating
        multiple tickets in quick succession.

        Args:
            tickets: List of updated tickets (matched by formatted_id).
            resort: If True, re-sort and rebuild the list (for state changes).
        """
        if not tickets:
            return

        # Build a lookup for quick access
        updates = {t.formatted_id: t for t in tickets}

        # Update all matching tickets in _all_tickets
        for i, t in enumerate(self._all_tickets):
            if t.formatted_id in updates:
                self._all_tickets[i] = updates[t.formatted_id]

        if resort:
            # Re-sort all tickets by state
            self._all_tickets = sort_tickets_by_state(self._all_tickets)

            # If no filter is active, rebuild displayed tickets
            if not self._filter_query:
                self._tickets = list(self._all_tickets)
                # Rebuild the UI list (preserve selection state)
                # Use remove_children for synchronous removal to avoid race conditions
                self.remove_children()
                for t in self._tickets:
                    is_selected = t.formatted_id in self._selected_ids
                    self.mount(self._create_list_item(t, selected=is_selected))
            else:
                # Re-apply filter (which will also sort)
                self.filter_tickets(self._filter_query)
        else:
            # Update in filtered tickets without re-sorting
            for i, t in enumerate(self._tickets):
                if t.formatted_id in updates:
                    self._tickets[i] = updates[t.formatted_id]
                    # Update the corresponding list item
                    items = list(self.query(TicketListItem)) + list(self.query(WideTicketListItem))
                    if i < len(items):
                        items[i].ticket = updates[t.formatted_id]

    def add_ticket(self, ticket: Ticket) -> None:
        """Add a new ticket to the list.

        Args:
            ticket: The new ticket to add.
        """
        # Add to all_tickets
        self._all_tickets.append(ticket)

        # Re-sort all tickets by state
        self._all_tickets = sort_tickets_by_state(self._all_tickets)

        # If no filter is active, add to displayed tickets
        if not self._filter_query:
            self._tickets = list(self._all_tickets)
            # Rebuild the UI list (preserve selection state)
            # Use remove_children/mount for synchronous update
            self.remove_children()
            for t in self._tickets:
                is_selected = t.formatted_id in self._selected_ids
                self.mount(self._create_list_item(t, selected=is_selected))
            # Select the new ticket
            for i, t in enumerate(self._tickets):
                if t.formatted_id == ticket.formatted_id:
                    self.index = i
                    break
        else:
            # Re-apply filter
            self.filter_tickets(self._filter_query)
