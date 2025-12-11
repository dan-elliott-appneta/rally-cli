# Iteration 7: Search & Filtering

**Goal**: Add search/filter functionality to quickly find tickets in the list.

## Overview

This iteration adds a search overlay that filters the ticket list as the user types. The search is activated with `/` (vim-style), filters in real-time, and can be cleared with `Esc`. The implementation maintains the existing architecture while adding a new SearchInput widget and filter logic to TicketList.

## Design Decisions

### 1. Search Activation Pattern
- **`/` key**: Activates search mode (vim-style, familiar to developers)
- **`Esc`**: Clears search and returns to normal mode
- **`Enter`**: Confirms search and focuses list (keeps filter active)

### 2. Search Behavior
- **Real-time filtering**: List updates as user types
- **Case-insensitive**: "bug" matches "Bug", "BUG", "Debugging"
- **Multi-field search**: Searches formatted_id, title, owner, and state
- **Empty search**: Shows all tickets (no filter)

### 3. UI Approach
- **Overlay input**: Search input appears at bottom of ticket list panel
- **Filter indicator**: Status bar shows "Filtered: X of Y" when search active
- **Preserved selection**: Tries to maintain selected ticket after filter

### 4. Architecture
- **SearchInput widget**: New widget for search input with specific keybindings
- **TicketList.filter()**: Method to apply filter and update display
- **App coordination**: Handles `/` key, manages search mode state

## Implementation Steps

### Step 1: Create SearchInput Widget

Create `src/rally_tui/widgets/search_input.py`:

```python
"""Search input widget for filtering tickets."""

from textual.widgets import Input
from textual.message import Message


class SearchInput(Input):
    """Input field for search/filter queries.

    Emits SearchChanged on each keystroke and SearchCleared on Escape.
    """

    class SearchChanged(Message):
        """Posted when search text changes."""
        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    class SearchCleared(Message):
        """Posted when search is cleared (Escape)."""
        pass

    class SearchSubmitted(Message):
        """Posted when search is submitted (Enter)."""
        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    DEFAULT_CSS = """
    SearchInput {
        dock: bottom;
        height: 1;
        border: none;
        background: $surface;
        padding: 0 1;
    }

    SearchInput:focus {
        border: none;
    }

    SearchInput > .input--placeholder {
        color: $text-muted;
    }
    """

    def __init__(
        self,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            placeholder="Search...",
            id=id,
            classes=classes,
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Emit SearchChanged when input changes."""
        self.post_message(self.SearchChanged(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Emit SearchSubmitted when Enter pressed."""
        self.post_message(self.SearchSubmitted(event.value))

    def action_escape(self) -> None:
        """Clear search and emit SearchCleared."""
        self.value = ""
        self.post_message(self.SearchCleared())
```

### Step 2: Add Filter Logic to TicketList

Update `src/rally_tui/widgets/ticket_list.py`:

```python
# Add to TicketList class:

def __init__(
    self,
    tickets: list[Ticket] | None = None,
    *,
    id: str | None = None,
    classes: str | None = None,
) -> None:
    super().__init__(id=id, classes=classes)
    self._tickets = tickets or []
    self._all_tickets = list(self._tickets)  # Keep original list
    self._filter_query = ""

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
            t for t in self._all_tickets
            if self._matches_query(t, query_lower)
        ]

    self._tickets = filtered
    self.clear()
    for ticket in filtered:
        self.append(TicketListItem(ticket))

    # Emit message about filter results
    self.post_message(self.FilterApplied(len(filtered), len(self._all_tickets)))

def _matches_query(self, ticket: Ticket, query: str) -> bool:
    """Check if ticket matches search query."""
    searchable = " ".join([
        ticket.formatted_id.lower(),
        ticket.title.lower(),
        (ticket.owner or "").lower(),
        (ticket.state or "").lower(),
    ])
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

# New message class:
class FilterApplied(Message):
    """Posted when filter is applied."""
    def __init__(self, filtered: int, total: int) -> None:
        self.filtered = filtered
        self.total = total
        super().__init__()
```

### Step 3: Update App with Search Mode

Update `src/rally_tui/app.py`:

```python
# Add binding:
BINDINGS = [
    Binding("q", "quit", "Quit"),
    Binding("tab", "switch_panel", "Switch Panel", show=False, priority=True),
    Binding("?", "help", "Help", show=False),
    Binding("/", "start_search", "Search", show=False),
    Binding("escape", "clear_search", "Clear", show=False, priority=True),
]

# Add to compose():
def compose(self) -> ComposeResult:
    yield Header()
    yield StatusBar(...)
    tickets = self._client.get_tickets()
    with Horizontal(id="main-container"):
        with Vertical(id="list-container"):
            yield TicketList(tickets, id="ticket-list")
            yield SearchInput(id="search-input")
        yield TicketDetail(id="ticket-detail")
    yield CommandBar(id="command-bar")

# Add search actions:
def action_start_search(self) -> None:
    """Activate search mode."""
    search = self.query_one(SearchInput)
    search.display = True
    search.focus()
    self.query_one(CommandBar).set_context("search")

def action_clear_search(self) -> None:
    """Clear search and return to list."""
    search = self.query_one(SearchInput)
    search.value = ""
    search.display = False
    self.query_one(TicketList).clear_filter()
    self.query_one(TicketList).focus()
    self.query_one(CommandBar).set_context("list")
    self._update_status_filter()

def on_search_input_search_changed(self, event: SearchInput.SearchChanged) -> None:
    """Filter list as user types."""
    self.query_one(TicketList).filter_tickets(event.query)
    self._update_status_filter()

def on_search_input_search_submitted(self, event: SearchInput.SearchSubmitted) -> None:
    """Keep filter, focus list."""
    search = self.query_one(SearchInput)
    search.display = False
    self.query_one(TicketList).focus()
    self.query_one(CommandBar).set_context("list")

def on_search_input_search_cleared(self, event: SearchInput.SearchCleared) -> None:
    """Clear filter and return to list."""
    self.action_clear_search()

def _update_status_filter(self) -> None:
    """Update status bar with filter info."""
    ticket_list = self.query_one(TicketList)
    status = self.query_one(StatusBar)
    if ticket_list.filter_query:
        status.set_filter_info(ticket_list.filtered_count, ticket_list.total_count)
    else:
        status.clear_filter_info()
```

### Step 4: Update StatusBar with Filter Info

Update `src/rally_tui/widgets/status_bar.py`:

```python
# Add to __init__:
self._filter_info = ""

# Update _update_display:
def _update_display(self) -> None:
    parts = [f"Workspace: {self._workspace}"]
    if self._project:
        parts.append(f"Project: {self._project}")
    if self._filter_info:
        parts.append(self._filter_info)
    status = "Connected" if self._connected else "Offline"
    parts.append(status)
    self._display_content = " | ".join(parts)
    self.update(self._display_content)

# Add methods:
def set_filter_info(self, filtered: int, total: int) -> None:
    """Show filter count in status bar."""
    self._filter_info = f"Filtered: {filtered}/{total}"
    self._update_display()

def clear_filter_info(self) -> None:
    """Clear filter info from status bar."""
    self._filter_info = ""
    self._update_display()
```

### Step 5: Update CommandBar with Search Context

Update `src/rally_tui/widgets/command_bar.py`:

```python
CONTEXTS = {
    "list": "[j/k] Navigate  [g/G] Jump  [/] Search  [Enter] Select  [Tab] Switch  [q] Quit",
    "detail": "[Tab] Switch Panel  [q] Quit",
    "search": "[Enter] Confirm  [Esc] Clear  Type to filter...",
}
```

### Step 6: Update CSS

Add to `src/rally_tui/app.tcss`:

```css
/* Search input container */
#list-container {
    height: 100%;
}

/* Search input - initially hidden */
#search-input {
    display: none;
    height: 1;
    background: $surface;
    border-top: solid $primary;
}

#search-input.visible {
    display: block;
}
```

### Step 7: Export SearchInput from widgets

Update `src/rally_tui/widgets/__init__.py`:

```python
from rally_tui.widgets.command_bar import CommandBar
from rally_tui.widgets.search_input import SearchInput
from rally_tui.widgets.status_bar import StatusBar
from rally_tui.widgets.ticket_detail import TicketDetail
from rally_tui.widgets.ticket_list import TicketList, TicketListItem

__all__ = [
    "CommandBar",
    "SearchInput",
    "StatusBar",
    "TicketDetail",
    "TicketList",
    "TicketListItem",
]
```

## Tests to Write

### test_search_input.py

```python
class TestSearchInputUnit:
    def test_default_placeholder(self) -> None:
        """SearchInput should have 'Search...' placeholder."""

    def test_initial_value_empty(self) -> None:
        """SearchInput should start empty."""

class TestSearchInputWidget:
    async def test_typing_emits_search_changed(self) -> None:
        """Typing should emit SearchChanged messages."""

    async def test_enter_emits_search_submitted(self) -> None:
        """Enter key should emit SearchSubmitted."""

    async def test_escape_clears_and_emits(self) -> None:
        """Escape should clear input and emit SearchCleared."""
```

### test_ticket_list.py (additions)

```python
class TestTicketListFilter:
    def test_filter_by_id(self) -> None:
        """Filter should match ticket ID."""

    def test_filter_by_title(self) -> None:
        """Filter should match ticket title."""

    def test_filter_case_insensitive(self) -> None:
        """Filter should be case-insensitive."""

    def test_filter_empty_shows_all(self) -> None:
        """Empty filter should show all tickets."""

    def test_clear_filter(self) -> None:
        """clear_filter should restore all tickets."""

    def test_filter_no_match(self) -> None:
        """Filter with no matches should show empty list."""

    def test_filter_counts(self) -> None:
        """filtered_count and total_count should be accurate."""
```

### test_app.py (additions)

```python
class TestAppSearch:
    async def test_slash_activates_search(self) -> None:
        """Pressing / should focus search input."""

    async def test_escape_clears_search(self) -> None:
        """Escape should clear search and refocus list."""

    async def test_typing_filters_list(self) -> None:
        """Typing in search should filter ticket list."""

    async def test_enter_confirms_search(self) -> None:
        """Enter should confirm search and focus list."""
```

## Acceptance Criteria

1. **Search Activation**
   - [ ] `/` key activates search input
   - [ ] Search input appears at bottom of ticket list
   - [ ] Focus moves to search input

2. **Real-time Filtering**
   - [ ] List filters as user types
   - [ ] Matches formatted_id, title, owner, state
   - [ ] Case-insensitive matching
   - [ ] Empty search shows all tickets

3. **Search Completion**
   - [ ] `Enter` confirms filter and focuses list
   - [ ] `Esc` clears filter and focuses list
   - [ ] Filter persists after confirmation

4. **Status Display**
   - [ ] Status bar shows "Filtered: X/Y" when filter active
   - [ ] Command bar shows search-specific shortcuts

5. **Tests**
   - [ ] SearchInput widget tests
   - [ ] TicketList filter tests
   - [ ] App integration tests
   - [ ] All existing tests still pass

## Files to Create/Modify

### New Files
- `src/rally_tui/widgets/search_input.py`
- `tests/test_search_input.py`

### Modified Files
- `src/rally_tui/widgets/ticket_list.py` - Add filter logic
- `src/rally_tui/widgets/status_bar.py` - Add filter info display
- `src/rally_tui/widgets/command_bar.py` - Add search context
- `src/rally_tui/widgets/__init__.py` - Export SearchInput
- `src/rally_tui/app.py` - Add search mode handling
- `src/rally_tui/app.tcss` - Add search input styles
- `tests/test_ticket_list.py` - Add filter tests
- `tests/test_status_bar.py` - Add filter info tests

## Commit Strategy

1. **Add SearchInput widget** - New widget with tests
2. **Add filter logic to TicketList** - filter_tickets method with tests
3. **Update StatusBar with filter info** - set_filter_info method with tests
4. **Update CommandBar with search context** - Add "search" context
5. **Integrate search in app** - Wire up all components
6. **Update CSS and layout** - Add search input styling
7. **Complete Iteration 7** - Documentation updates
