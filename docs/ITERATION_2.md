# Iteration 2: Details Panel (Right Side)

## Goal

Add a details panel on the right side of the screen that displays full ticket information when a ticket is selected in the list. This creates the classic master-detail pattern where the list (left) drives the detail view (right).

**Success Criteria**:
- Two-panel horizontal layout: list (left) and details (right)
- Selecting a ticket in the list updates the details panel
- Details panel shows all ticket fields with proper formatting
- Empty state displayed when no ticket is selected
- Details panel scrolls for long content

---

## Architecture Overview

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│  Rally TUI                                                   Header │
├─────────────────────────┬───────────────────────────────────────────┤
│  TICKETS (TicketList)   │  DETAILS (TicketDetail)                   │
│  ~~~~~~~~~~~~~~~~~~~~~~ │  ~~~~~~~~~~~~~~~~~~~~~                    │
│  ▶ US1234 User login    │  US1234 - User login feature              │
│    US1235 Password rst  │  ─────────────────────────────────────    │
│    DE456  Fix null ptr  │  Type: User Story                         │
│    US1236 Add logout    │  State: In Progress                       │
│    TA789  Write tests   │  Owner: John Smith                        │
│                         │                                           │
│                         │  Description:                             │
│                         │  As a user, I want to log in so that...   │
│                         │                                           │
├─────────────────────────┴───────────────────────────────────────────┤
│  q Quit                                                      Footer │
└─────────────────────────────────────────────────────────────────────┘
```

### Communication Pattern

We'll use Textual's message system (already implemented in Iteration 1) to communicate between widgets:

1. User navigates list with j/k keys
2. `TicketList` posts `TicketHighlighted` message with the ticket
3. `RallyTUI` app handles message and updates `TicketDetail` widget
4. `TicketDetail` re-renders with new ticket data

```
┌─────────────┐     TicketHighlighted      ┌─────────────┐
│ TicketList  │ ─────────────────────────► │  RallyTUI   │
└─────────────┘         (Message)          └──────┬──────┘
                                                  │
                                           update_ticket()
                                                  │
                                                  ▼
                                           ┌─────────────┐
                                           │TicketDetail │
                                           └─────────────┘
```

---

## Step-by-Step Implementation

### Step 1: Create the TicketDetail Widget

The detail widget displays a single ticket's information in a formatted view.

```python
# src/rally_tui/widgets/ticket_detail.py
"""Ticket detail widget for displaying full ticket information."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static

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

        # Metadata section
        type_display = self._format_type(ticket.ticket_type)
        owner_display = ticket.owner or "Unassigned"
        metadata = (
            f"Type: {type_display}\n"
            f"State: {ticket.state}\n"
            f"Owner: {owner_display}"
        )
        self.query_one("#detail-metadata", Static).update(metadata)

        # Description (placeholder for now - will be added to model later)
        self.query_one("#detail-description-label", Static).update("\nDescription:")
        self.query_one("#detail-description", Static).update(
            "No description available."
        )

    def _format_type(self, ticket_type: str) -> str:
        """Format ticket type for display."""
        type_names = {
            "UserStory": "User Story",
            "Defect": "Defect",
            "Task": "Task",
            "TestCase": "Test Case",
        }
        return type_names.get(ticket_type, ticket_type)
```

### Step 2: Update the Widgets Package

```python
# src/rally_tui/widgets/__init__.py
"""TUI Widgets for Rally."""

from .ticket_detail import TicketDetail
from .ticket_list import TicketList, TicketListItem

__all__ = ["TicketDetail", "TicketList", "TicketListItem"]
```

### Step 3: Update the Main Application

Modify `app.py` to use a horizontal layout with both panels:

```python
# src/rally_tui/app.py
"""Rally TUI - Main Application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from rally_tui.models.sample_data import SAMPLE_TICKETS
from rally_tui.widgets import TicketDetail, TicketList


class RallyTUI(App[None]):
    """A TUI for browsing and managing Rally work items."""

    TITLE = "Rally TUI"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "help", "Help", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        with Horizontal(id="main-container"):
            yield TicketList(SAMPLE_TICKETS, id="ticket-list")
            yield TicketDetail(id="ticket-detail")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the detail panel with the first ticket."""
        if SAMPLE_TICKETS:
            detail = self.query_one(TicketDetail)
            detail.ticket = SAMPLE_TICKETS[0]

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


def main() -> None:
    """Entry point for the application."""
    app = RallyTUI()
    app.run()


if __name__ == "__main__":
    main()
```

### Step 4: Update the CSS Stylesheet

Add styles for the two-panel layout:

```css
/* src/rally_tui/app.tcss */

/* Main application layout */
Screen {
    layout: vertical;
}

/* Main content container - horizontal split */
#main-container {
    height: 1fr;
}

/* Ticket list styling - left panel */
#ticket-list {
    width: 35%;
    min-width: 25;
    max-width: 50;
    height: 100%;
    border: solid $primary;
    border-title-color: $text;
    border-title-style: bold;
}

#ticket-list:focus {
    border: double $accent;
}

/* Individual list items */
TicketListItem {
    padding: 0 1;
}

TicketListItem > Label {
    width: 100%;
}

/* Highlighted (cursor) item */
TicketListItem.-highlight {
    background: $accent 30%;
}

TicketListItem.-highlight > Label {
    text-style: bold;
}

/* Color coding by ticket type */
.ticket-us {
    color: $success;
}

.ticket-de {
    color: $error;
}

.ticket-ta {
    color: $warning;
}

.ticket-tc {
    color: $primary;
}

/* Ticket detail panel - right panel */
#ticket-detail {
    width: 1fr;
    height: 100%;
    border: solid $secondary;
    padding: 1 2;
}

#ticket-detail:focus {
    border: double $accent;
}

/* Detail content styling */
#detail-header {
    text-style: bold;
    color: $text;
    margin-bottom: 0;
}

#detail-divider {
    color: $text-muted;
    margin-bottom: 1;
}

#detail-metadata {
    margin-bottom: 1;
}

#detail-description-label {
    text-style: bold;
    color: $text;
}

#detail-description {
    color: $text-muted;
}

/* Footer styling */
Footer {
    background: $surface;
}
```

### Step 5: Add Description to Ticket Model

Extend the Ticket model to include a description field:

```python
# src/rally_tui/models/ticket.py
"""Ticket data model - decoupled from Rally API responses."""

from dataclasses import dataclass
from typing import Literal

TicketType = Literal["UserStory", "Defect", "Task", "TestCase"]


@dataclass(frozen=True)
class Ticket:
    """Represents a Rally work item."""

    formatted_id: str
    name: str
    ticket_type: TicketType
    state: str
    owner: str | None = None
    description: str = ""

    @property
    def display_text(self) -> str:
        """Format for list display."""
        return f"{self.formatted_id} {self.name}"

    @property
    def type_prefix(self) -> str:
        """Extract prefix from formatted_id."""
        for i, char in enumerate(self.formatted_id):
            if char.isdigit():
                return self.formatted_id[:i]
        return self.formatted_id[:2]
```

### Step 6: Update Sample Data with Descriptions

```python
# src/rally_tui/models/sample_data.py
"""Sample ticket data for development and testing."""

from .ticket import Ticket

SAMPLE_TICKETS: list[Ticket] = [
    Ticket(
        formatted_id="US1234",
        name="User login feature",
        ticket_type="UserStory",
        state="In Progress",
        owner="John Smith",
        description="As a user, I want to log in with my email and password so that I can access my account securely.",
    ),
    Ticket(
        formatted_id="US1235",
        name="Password reset functionality",
        ticket_type="UserStory",
        state="Defined",
        owner="Jane Doe",
        description="As a user, I want to reset my password via email so that I can regain access if I forget it.",
    ),
    Ticket(
        formatted_id="DE456",
        name="Fix null pointer exception on checkout",
        ticket_type="Defect",
        state="Open",
        owner="Bob Wilson",
        description="NullPointerException thrown when user clicks checkout with an empty cart. Stack trace attached.",
    ),
    Ticket(
        formatted_id="US1236",
        name="Add logout button to navbar",
        ticket_type="UserStory",
        state="Completed",
        owner="Alice Chen",
        description="Add a clearly visible logout button in the navigation bar for authenticated users.",
    ),
    Ticket(
        formatted_id="TA789",
        name="Write unit tests for auth module",
        ticket_type="Task",
        state="In Progress",
        owner="John Smith",
        description="Create comprehensive unit tests for the authentication module including login, logout, and session management.",
    ),
    Ticket(
        formatted_id="DE457",
        name="Memory leak in image processing",
        ticket_type="Defect",
        state="Open",
        owner=None,
        description="Memory usage grows unbounded when processing multiple images. Heap dump analysis needed.",
    ),
    Ticket(
        formatted_id="TC101",
        name="Verify login with valid credentials",
        ticket_type="TestCase",
        state="Defined",
        owner="QA Team",
        description="Test that users can successfully log in with valid email/password combinations.",
    ),
    Ticket(
        formatted_id="US1237",
        name="Implement dark mode toggle",
        ticket_type="UserStory",
        state="Defined",
        owner=None,
        description="Allow users to switch between light and dark themes via a toggle in settings.",
    ),
]
```

### Step 7: Update TicketDetail to Show Description

Update the `_show_ticket` method:

```python
def _show_ticket(self, ticket: Ticket) -> None:
    """Display the ticket details."""
    # Header: ID and Name
    header = f"{ticket.formatted_id} - {ticket.name}"
    self.query_one("#detail-header", Static).update(header)

    # Divider
    self.query_one("#detail-divider", Static).update("─" * 40)

    # Metadata section
    type_display = self._format_type(ticket.ticket_type)
    owner_display = ticket.owner or "Unassigned"
    metadata = (
        f"Type: {type_display}\n"
        f"State: {ticket.state}\n"
        f"Owner: {owner_display}"
    )
    self.query_one("#detail-metadata", Static).update(metadata)

    # Description
    self.query_one("#detail-description-label", Static).update("\nDescription:")
    description = ticket.description or "No description available."
    self.query_one("#detail-description", Static).update(description)
```

---

## Testing

### Step 8: Update Test Fixtures

```python
# tests/conftest.py - add description to fixtures
@pytest.fixture
def sample_tickets() -> list[Ticket]:
    """Provide a small set of tickets for testing."""
    return [
        Ticket(
            formatted_id="US100",
            name="Test story one",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            description="Test description for story one.",
        ),
        Ticket(
            formatted_id="DE200",
            name="Test defect",
            ticket_type="Defect",
            state="Open",
            owner=None,
            description="Test description for defect.",
        ),
        Ticket(
            formatted_id="TA300",
            name="Test task",
            ticket_type="Task",
            state="In Progress",
            owner="Another User",
            description="",
        ),
    ]


@pytest.fixture
def single_ticket() -> Ticket:
    """Provide a single ticket for unit tests."""
    return Ticket(
        formatted_id="US999",
        name="Single test ticket",
        ticket_type="UserStory",
        state="Completed",
        owner="Owner Name",
        description="This is a test description.",
    )
```

### Step 9: Write TicketDetail Unit Tests

```python
# tests/test_ticket_detail.py
"""Tests for the TicketDetail widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.widgets import TicketDetail


class TestTicketDetailWidget:
    """Tests for TicketDetail widget behavior."""

    async def test_initial_state_shows_first_ticket(self) -> None:
        """Detail panel should show first ticket on mount."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "US1234"

    async def test_detail_updates_on_navigation(self) -> None:
        """Detail panel should update when navigating list."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)

            # Move to second item
            await pilot.press("j")
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "US1235"

    async def test_detail_shows_ticket_name(self) -> None:
        """Detail panel should display ticket name."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)
            header = app.query_one("#detail-header")
            assert "User login feature" in header.render()

    async def test_detail_shows_ticket_state(self) -> None:
        """Detail panel should display ticket state."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "In Progress" in rendered

    async def test_detail_shows_owner(self) -> None:
        """Detail panel should display owner name."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "John Smith" in rendered

    async def test_detail_shows_unassigned_for_no_owner(self) -> None:
        """Detail panel should show 'Unassigned' when owner is None."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            # Navigate to DE457 which has no owner
            await pilot.press("j", "j", "j", "j", "j")  # 5 times to DE457
            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            assert detail.ticket.owner is None

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Unassigned" in rendered

    async def test_detail_shows_description(self) -> None:
        """Detail panel should display ticket description."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            description = app.query_one("#detail-description")
            rendered = str(description.render())
            assert "email and password" in rendered
```

### Step 10: Write Snapshot Tests for Two-Panel Layout

```python
# tests/test_snapshots.py - add new snapshot tests

def test_two_panel_layout(self, snap_compare) -> None:
    """Snapshot of two-panel layout with detail visible."""
    from rally_tui.app import RallyTUI
    assert snap_compare(RallyTUI())

def test_detail_after_navigation(self, snap_compare) -> None:
    """Snapshot showing detail panel updated after navigation."""
    from rally_tui.app import RallyTUI
    assert snap_compare(RallyTUI(), press=["j", "j"])

def test_defect_detail_view(self, snap_compare) -> None:
    """Snapshot showing defect type in detail panel."""
    from rally_tui.app import RallyTUI
    # Navigate to first defect (DE456)
    assert snap_compare(RallyTUI(), press=["j", "j"])
```

---

## Checklist

Before moving to Iteration 3, verify:

- [ ] App launches with two-panel horizontal layout
- [ ] Left panel (TicketList) occupies ~35% width
- [ ] Right panel (TicketDetail) fills remaining space
- [ ] First ticket details shown on app launch
- [ ] Navigating with j/k updates the detail panel immediately
- [ ] Detail panel shows: Header (ID + Name), Type, State, Owner, Description
- [ ] "Unassigned" displayed when ticket has no owner
- [ ] Empty descriptions show "No description available"
- [ ] Detail panel scrolls when content exceeds height
- [ ] All existing tests still pass
- [ ] New unit tests pass (7+ tests for TicketDetail)
- [ ] Snapshot tests updated and passing

---

## Files Modified/Created

**Modified:**
```
src/rally_tui/
├── app.py              # Add Horizontal container, TicketDetail, on_mount
├── app.tcss            # Two-panel layout CSS, detail styling
├── models/
│   ├── ticket.py       # Add description field
│   └── sample_data.py  # Add descriptions to sample tickets
└── widgets/
    └── __init__.py     # Export TicketDetail
```

**Created:**
```
src/rally_tui/widgets/
└── ticket_detail.py    # New TicketDetail widget

tests/
└── test_ticket_detail.py  # New tests for detail widget
```

---

## Key Concepts Introduced

### Horizontal Container
```python
from textual.containers import Horizontal

with Horizontal(id="main-container"):
    yield TicketList(...)
    yield TicketDetail(...)
```

### Reactive Properties
```python
from textual.reactive import reactive

class TicketDetail(VerticalScroll):
    ticket: reactive[Ticket | None] = reactive(None)

    def watch_ticket(self, ticket: Ticket | None) -> None:
        """Called automatically when ticket changes."""
        self._update_display()
```

### CSS Fractional Units
```css
#ticket-list {
    width: 35%;      /* Fixed percentage */
}

#ticket-detail {
    width: 1fr;      /* Fill remaining space */
}
```

---

## Next Steps (Iteration 3)

Once this iteration is complete:
1. Add the `CommandBar` widget (bottom panel)
2. Make command bar context-sensitive (different commands for list vs detail)
3. Update layout to dock command bar at bottom

See `PLAN.md` for the full roadmap.
