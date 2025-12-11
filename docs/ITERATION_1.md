# Iteration 1: Project Skeleton & Static Ticket List

## Goal

Create a minimal working Textual application that displays a static list of Rally tickets with full keyboard navigation. This establishes the project foundation, development workflow, and testing infrastructure.

**Success Criteria**:
- App launches and displays a list of 5-10 hardcoded tickets
- Arrow keys (↑/↓) and vim keys (j/k) navigate the list
- Selected item is visually highlighted
- First snapshot test passes

---

## Prerequisites

Before starting, ensure you have:
- Python 3.12+ installed
- A terminal that supports modern escape sequences (most do)
- Familiarity with async Python basics

---

## Step-by-Step Implementation

### Step 1: Initialize Project Structure

Create the directory structure and initialize the project:

```bash
cd ~/rally-cli

# Create directory structure
mkdir -p src/rally_tui/{widgets,models,services,screens}
mkdir -p tests/snapshots

# Create __init__.py files
touch src/rally_tui/__init__.py
touch src/rally_tui/widgets/__init__.py
touch src/rally_tui/models/__init__.py
touch src/rally_tui/services/__init__.py
touch src/rally_tui/screens/__init__.py
```

**Why src layout?** The `src/` layout ensures tests run against the installed package, not source files directly. This catches packaging issues early and matches how users will consume the library.

### Step 2: Create pyproject.toml

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=69.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "rally-tui"
version = "0.1.0"
description = "A TUI for Rally (Broadcom) work item management"
readme = "README.md"
requires-python = ">=3.12"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "[email protected]"}
]
keywords = ["rally", "tui", "textual", "agile"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Framework :: Textual",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]

dependencies = [
    "textual>=0.40.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-textual-snapshot>=0.4.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[project.scripts]
rally-tui = "rally_tui.app:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
```

### Step 3: Create the Ticket Model

Even though we're using hardcoded data, define the model now to establish the contract:

```python
# src/rally_tui/models/ticket.py
"""Ticket data model - decoupled from Rally API responses."""

from dataclasses import dataclass
from typing import Literal

TicketType = Literal["UserStory", "Defect", "Task", "TestCase"]


@dataclass(frozen=True)
class Ticket:
    """Represents a Rally work item.

    This is an internal model, separate from pyral's response objects.
    Using a dataclass provides immutability and easy equality checks for testing.
    """
    formatted_id: str
    name: str
    ticket_type: TicketType
    state: str
    owner: str | None = None

    @property
    def display_text(self) -> str:
        """Format for list display: 'US1234 User login feature'"""
        return f"{self.formatted_id} {self.name}"

    @property
    def type_prefix(self) -> str:
        """Extract prefix from formatted_id (US, DE, TA, TC)."""
        # FormattedID format: US1234, DE456, TA789, TC123
        for i, char in enumerate(self.formatted_id):
            if char.isdigit():
                return self.formatted_id[:i]
        return self.formatted_id[:2]
```

```python
# src/rally_tui/models/__init__.py
"""Data models for Rally TUI."""

from .ticket import Ticket, TicketType

__all__ = ["Ticket", "TicketType"]
```

### Step 4: Create Hardcoded Test Data

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
    ),
    Ticket(
        formatted_id="US1235",
        name="Password reset functionality",
        ticket_type="UserStory",
        state="Defined",
        owner="Jane Doe",
    ),
    Ticket(
        formatted_id="DE456",
        name="Fix null pointer exception on checkout",
        ticket_type="Defect",
        state="Open",
        owner="Bob Wilson",
    ),
    Ticket(
        formatted_id="US1236",
        name="Add logout button to navbar",
        ticket_type="UserStory",
        state="Completed",
        owner="Alice Chen",
    ),
    Ticket(
        formatted_id="TA789",
        name="Write unit tests for auth module",
        ticket_type="Task",
        state="In Progress",
        owner="John Smith",
    ),
    Ticket(
        formatted_id="DE457",
        name="Memory leak in image processing",
        ticket_type="Defect",
        state="Open",
        owner=None,
    ),
    Ticket(
        formatted_id="TC101",
        name="Verify login with valid credentials",
        ticket_type="TestCase",
        state="Defined",
        owner="QA Team",
    ),
    Ticket(
        formatted_id="US1237",
        name="Implement dark mode toggle",
        ticket_type="UserStory",
        state="Defined",
        owner=None,
    ),
]
```

### Step 5: Create the TicketList Widget

This is the core widget for Iteration 1:

```python
# src/rally_tui/widgets/ticket_list.py
"""Ticket list widget with keyboard navigation."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView

from rally_tui.models import Ticket


class TicketListItem(ListItem):
    """A single ticket item in the list."""

    def __init__(self, ticket: Ticket) -> None:
        super().__init__()
        self.ticket = ticket

    def compose(self) -> ComposeResult:
        """Create the ticket display label."""
        # Color-code by ticket type
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

    # Add vim-style navigation alongside default arrow keys
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
        """Replace the ticket list with new data.

        This will be used in later iterations when loading from Rally.
        """
        self._tickets = tickets
        self.clear()
        for ticket in tickets:
            self.append(TicketListItem(ticket))
```

```python
# src/rally_tui/widgets/__init__.py
"""TUI Widgets for Rally."""

from .ticket_list import TicketList, TicketListItem

__all__ = ["TicketList", "TicketListItem"]
```

### Step 6: Create the Main Application

```python
# src/rally_tui/app.py
"""Rally TUI - Main Application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from rally_tui.models.sample_data import SAMPLE_TICKETS
from rally_tui.widgets import TicketList


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
        yield TicketList(SAMPLE_TICKETS, id="ticket-list")
        yield Footer()

    def on_ticket_list_ticket_highlighted(
        self, event: TicketList.TicketHighlighted
    ) -> None:
        """Handle ticket highlight changes.

        In Iteration 1, just log for debugging.
        Iteration 2 will update the details panel.
        """
        if event.ticket:
            self.log.info(f"Highlighted: {event.ticket.formatted_id}")

    def on_ticket_list_ticket_selected(
        self, event: TicketList.TicketSelected
    ) -> None:
        """Handle ticket selection (Enter key).

        In Iteration 1, just log for debugging.
        Later iterations will open detail view or edit mode.
        """
        self.log.info(f"Selected: {event.ticket.formatted_id}")


def main() -> None:
    """Entry point for the application."""
    app = RallyTUI()
    app.run()


if __name__ == "__main__":
    main()
```

### Step 7: Create the CSS Stylesheet

```css
/* src/rally_tui/app.tcss */

/* Main application layout */
Screen {
    layout: vertical;
}

/* Ticket list styling */
#ticket-list {
    height: 1fr;
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
    color: $success;  /* Green for User Stories */
}

.ticket-de {
    color: $error;    /* Red for Defects */
}

.ticket-ta {
    color: $warning;  /* Yellow/Orange for Tasks */
}

.ticket-tc {
    color: $primary;  /* Blue for Test Cases */
}

/* Footer styling */
Footer {
    background: $surface;
}
```

### Step 8: Set Up Testing Infrastructure

```python
# tests/conftest.py
"""Pytest configuration and fixtures for Rally TUI tests."""

import pytest
from rally_tui.models import Ticket


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
        ),
        Ticket(
            formatted_id="DE200",
            name="Test defect",
            ticket_type="Defect",
            state="Open",
            owner=None,
        ),
        Ticket(
            formatted_id="TA300",
            name="Test task",
            ticket_type="Task",
            state="In Progress",
            owner="Another User",
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
    )
```

### Step 9: Write Unit Tests

```python
# tests/test_ticket_model.py
"""Unit tests for the Ticket model."""

import pytest
from rally_tui.models import Ticket


class TestTicket:
    """Tests for the Ticket dataclass."""

    def test_display_text(self, single_ticket: Ticket) -> None:
        """Display text should combine ID and name."""
        assert single_ticket.display_text == "US999 Single test ticket"

    def test_type_prefix_user_story(self) -> None:
        """User story prefix should be US."""
        ticket = Ticket("US1234", "Test", "UserStory", "Open")
        assert ticket.type_prefix == "US"

    def test_type_prefix_defect(self) -> None:
        """Defect prefix should be DE."""
        ticket = Ticket("DE456", "Test", "Defect", "Open")
        assert ticket.type_prefix == "DE"

    def test_type_prefix_task(self) -> None:
        """Task prefix should be TA."""
        ticket = Ticket("TA789", "Test", "Task", "Open")
        assert ticket.type_prefix == "TA"

    def test_type_prefix_test_case(self) -> None:
        """Test case prefix should be TC."""
        ticket = Ticket("TC101", "Test", "TestCase", "Open")
        assert ticket.type_prefix == "TC"

    def test_ticket_immutability(self, single_ticket: Ticket) -> None:
        """Tickets should be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            single_ticket.name = "Changed"  # type: ignore[misc]

    def test_ticket_equality(self) -> None:
        """Two tickets with same data should be equal."""
        t1 = Ticket("US1", "Test", "UserStory", "Open", "Owner")
        t2 = Ticket("US1", "Test", "UserStory", "Open", "Owner")
        assert t1 == t2

    def test_ticket_optional_owner(self) -> None:
        """Owner should be optional."""
        ticket = Ticket("US1", "Test", "UserStory", "Open")
        assert ticket.owner is None
```

```python
# tests/test_ticket_list.py
"""Tests for the TicketList widget."""

import pytest
from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.widgets import TicketList


class TestTicketListWidget:
    """Tests for TicketList widget behavior."""

    async def test_initial_render(self, sample_tickets: list[Ticket]) -> None:
        """List should render all provided tickets."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            # ListView creates children for each item
            assert len(ticket_list.children) == len(app.query("TicketListItem"))

    async def test_keyboard_navigation_down(self, sample_tickets: list[Ticket]) -> None:
        """Pressing j or down arrow should move selection down."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            initial_index = ticket_list.index

            await pilot.press("j")
            assert ticket_list.index == initial_index + 1

    async def test_keyboard_navigation_up(self, sample_tickets: list[Ticket]) -> None:
        """Pressing k or up arrow should move selection up."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Move down first, then up
            await pilot.press("j", "j")
            await pilot.press("k")
            assert ticket_list.index == 1

    async def test_vim_go_to_top(self) -> None:
        """Pressing g should jump to first item."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Move down several times
            await pilot.press("j", "j", "j")
            assert ticket_list.index > 0

            # Jump to top
            await pilot.press("g")
            assert ticket_list.index == 0

    async def test_vim_go_to_bottom(self) -> None:
        """Pressing G should jump to last item."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("G")
            # Should be at last item (index = count - 1)
            expected_last = len(list(app.query("TicketListItem"))) - 1
            assert ticket_list.index == expected_last

    async def test_arrow_keys_work(self) -> None:
        """Standard arrow keys should also navigate."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("down")
            assert ticket_list.index == 1

            await pilot.press("up")
            assert ticket_list.index == 0

    async def test_highlight_message_posted(self) -> None:
        """Moving selection should post TicketHighlighted message."""
        app = RallyTUI()
        messages: list[TicketList.TicketHighlighted] = []

        # Capture messages
        original_handler = app.on_ticket_list_ticket_highlighted
        def capture_handler(event: TicketList.TicketHighlighted) -> None:
            messages.append(event)
            original_handler(event)
        app.on_ticket_list_ticket_highlighted = capture_handler  # type: ignore

        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()

        assert len(messages) > 0
        assert messages[-1].ticket is not None
```

### Step 10: Write Snapshot Tests

```python
# tests/test_snapshots.py
"""Snapshot tests for visual regression."""

import pytest


class TestAppSnapshots:
    """Visual regression tests using pytest-textual-snapshot."""

    def test_initial_render(self, snap_compare) -> None:
        """Snapshot of initial app state with first item selected."""
        from rally_tui.app import RallyTUI
        assert snap_compare(RallyTUI())

    def test_selection_moved(self, snap_compare) -> None:
        """Snapshot after moving selection down twice."""
        from rally_tui.app import RallyTUI
        assert snap_compare(RallyTUI(), press=["j", "j"])

    def test_selection_at_bottom(self, snap_compare) -> None:
        """Snapshot with selection at the last item."""
        from rally_tui.app import RallyTUI
        assert snap_compare(RallyTUI(), press=["G"])

    def test_different_terminal_size(self, snap_compare) -> None:
        """Snapshot at a smaller terminal size."""
        from rally_tui.app import RallyTUI
        assert snap_compare(RallyTUI(), terminal_size=(60, 15))
```

---

## Running the Application

### Install in Development Mode

```bash
cd ~/rally-cli

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run the App

```bash
# Using the entry point
rally-tui

# Or directly
python -m rally_tui.app
```

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only unit tests (skip snapshots)
pytest -k "not snapshot"

# Run with coverage
pytest --cov=rally_tui --cov-report=html

# Run snapshot tests and update baselines (first run)
pytest tests/test_snapshots.py --snapshot-update
```

---

## Expected Behavior

When the app launches, you should see:

```
┌─────────────────────────────────────────────────────────┐
│ Rally TUI                                               │
├─────────────────────────────────────────────────────────┤
│ ▶ US1234 User login feature                             │
│   US1235 Password reset functionality                   │
│   DE456 Fix null pointer exception on checkout          │
│   US1236 Add logout button to navbar                    │
│   TA789 Write unit tests for auth module                │
│   DE457 Memory leak in image processing                 │
│   TC101 Verify login with valid credentials             │
│   US1237 Implement dark mode toggle                     │
│                                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ q Quit                                                  │
└─────────────────────────────────────────────────────────┘
```

**Keyboard interactions**:
- `j` / `↓`: Move highlight down
- `k` / `↑`: Move highlight up
- `g`: Jump to first item
- `G`: Jump to last item
- `Enter`: Select item (logs to console in this iteration)
- `q`: Quit the application

---

## Checklist

Before moving to Iteration 2, verify:

- [ ] Project installs successfully with `pip install -e ".[dev]"`
- [ ] App launches with `rally-tui` command
- [ ] All 8 sample tickets display in the list
- [ ] `j`/`k` keys navigate up/down
- [ ] Arrow keys also navigate
- [ ] `g` jumps to top, `G` jumps to bottom
- [ ] Selected item has visible highlight (background color change)
- [ ] Ticket types show different colors (US=green, DE=red, TA=yellow, TC=blue)
- [ ] `pytest` runs and all tests pass
- [ ] Snapshot tests generate SVG files in `tests/snapshots/`
- [ ] `q` key exits the application cleanly

---

## Files Created

```
rally-cli/
├── pyproject.toml
├── src/
│   └── rally_tui/
│       ├── __init__.py
│       ├── app.py
│       ├── app.tcss
│       ├── models/
│       │   ├── __init__.py
│       │   ├── ticket.py
│       │   └── sample_data.py
│       └── widgets/
│           ├── __init__.py
│           └── ticket_list.py
└── tests/
    ├── conftest.py
    ├── test_ticket_model.py
    ├── test_ticket_list.py
    └── test_snapshots.py
```

---

## Troubleshooting

### "Module not found" errors
Ensure you installed in editable mode: `pip install -e ".[dev]"`

### Snapshot tests fail on first run
This is expected! Run `pytest --snapshot-update` to create initial baselines.

### Colors don't appear
Your terminal may not support 256 colors. Try a modern terminal like iTerm2, Windows Terminal, or Kitty.

### App doesn't respond to keys
Make sure the TicketList widget has focus. Click on it or press Tab.

---

## Next Steps (Iteration 2)

Once this iteration is complete:
1. Add the `TicketDetail` widget (right panel)
2. Wire highlight changes to update the detail view
3. Implement the two-column layout with CSS
4. Add tests for the detail panel

See `PLAN.md` for the full roadmap.
