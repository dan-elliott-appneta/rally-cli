# Iteration 3: Command Bar (Bottom Panel)

## Goal

Add a context-sensitive command bar at the bottom of the screen that displays relevant keyboard shortcuts based on which panel has focus. This replaces Textual's default Footer with a custom widget that provides better UX for our three-panel layout.

**Success Criteria**:
- Command bar docked at bottom of screen
- Shows different commands based on focused panel (list vs detail)
- Updates immediately when focus changes
- Tab key switches focus between panels
- Clean, readable command display format

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
│    DE456  Fix null ptr  │  Owner: John Smith                        │
│    US1236 Add logout    │  Iteration: Sprint 5                      │
│    TA789  Write tests   │  Points: 3                                │
│                         │  State: In Progress                       │
│                         │                                           │
│                         │  Description:                             │
│                         │  As a user, I want to log in so that...   │
│                         │                                           │
├─────────────────────────┴───────────────────────────────────────────┤
│  [j/k] Navigate  [g/G] Jump  [Tab] Switch Panel  [q] Quit           │
└─────────────────────────────────────────────────────────────────────┘
```

### Focus-Based Context Switching

The command bar updates based on which panel has focus:

```
┌──────────────────┐                    ┌──────────────────┐
│   TicketList     │      Tab key       │   TicketDetail   │
│   (focused)      │ ◄──────────────────│   (focused)      │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
         ▼                                       ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│ [j/k] Navigate           │    │ [Tab] Switch Panel       │
│ [g/G] Jump to top/bottom │    │ [q] Quit                 │
│ [Enter] Select           │    │                          │
│ [Tab] Switch Panel       │    │ (Future: [e] Edit)       │
│ [q] Quit                 │    │                          │
└──────────────────────────┘    └──────────────────────────┘
```

### Communication Pattern

We'll use Textual's focus events to detect when panels gain/lose focus:

1. User presses Tab or clicks a panel
2. Focus changes to new panel
3. App receives `DescendantFocus` event (or we watch `focused` property)
4. App calls `command_bar.set_context("list")` or `set_context("detail")`
5. CommandBar updates its display

```
┌─────────────────┐     Focus Event      ┌─────────────────┐
│ TicketList      │ ───────────────────► │    RallyTUI     │
│ or TicketDetail │                      │    (App)        │
└─────────────────┘                      └────────┬────────┘
                                                  │
                                         set_context()
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │   CommandBar    │
                                         └─────────────────┘
```

---

## Step-by-Step Implementation

### Step 1: Create the CommandBar Widget

Create a custom widget that extends `Static` and displays context-sensitive commands.

```python
# src/rally_tui/widgets/command_bar.py
"""Command bar widget for displaying context-sensitive keyboard shortcuts."""

from textual.widgets import Static


class CommandBar(Static):
    """Displays context-sensitive keyboard shortcuts at the bottom of the screen.

    The command bar shows different commands based on which panel has focus.
    It provides a cleaner alternative to the default Footer widget.
    """

    # Command sets for different contexts
    CONTEXTS = {
        "list": "[j/k] Navigate  [g/G] Jump  [Enter] Select  [Tab] Switch Panel  [q] Quit",
        "detail": "[Tab] Switch Panel  [q] Quit",
    }

    DEFAULT_CSS = """
    CommandBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        context: str = "list",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the command bar.

        Args:
            context: Initial context ("list" or "detail").
            id: Widget ID for CSS targeting.
            classes: CSS classes to apply.
        """
        super().__init__(id=id, classes=classes)
        self._context = context

    def on_mount(self) -> None:
        """Set initial content when mounted."""
        self.update(self.CONTEXTS.get(self._context, ""))

    def set_context(self, context: str) -> None:
        """Update the command bar for a new context.

        Args:
            context: The new context ("list" or "detail").
        """
        self._context = context
        commands = self.CONTEXTS.get(context, "")
        self.update(commands)

    @property
    def context(self) -> str:
        """Get the current context."""
        return self._context
```

### Step 2: Update the Widgets Package

Export the new CommandBar widget.

```python
# src/rally_tui/widgets/__init__.py
"""TUI Widgets for Rally."""

from .command_bar import CommandBar
from .ticket_detail import TicketDetail
from .ticket_list import TicketList, TicketListItem

__all__ = ["CommandBar", "TicketDetail", "TicketList", "TicketListItem"]
```

### Step 3: Update the Main Application

Modify `app.py` to:
- Use CommandBar instead of Footer
- Track focus changes
- Add Tab key binding to switch panels

```python
# src/rally_tui/app.py
"""Rally TUI - Main Application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Header

from rally_tui.models.sample_data import SAMPLE_TICKETS
from rally_tui.widgets import CommandBar, TicketDetail, TicketList


class RallyTUI(App[None]):
    """A TUI for browsing and managing Rally work items."""

    TITLE = "Rally TUI"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "switch_panel", "Switch Panel", show=False),
        Binding("?", "help", "Help", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        with Horizontal(id="main-container"):
            yield TicketList(SAMPLE_TICKETS, id="ticket-list")
            yield TicketDetail(id="ticket-detail")
        yield CommandBar(id="command-bar")

    def on_mount(self) -> None:
        """Initialize the app state."""
        # Set first ticket in detail panel
        if SAMPLE_TICKETS:
            detail = self.query_one(TicketDetail)
            detail.ticket = SAMPLE_TICKETS[0]

        # Focus the ticket list initially
        self.query_one(TicketList).focus()

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

    def watch_focused(self, focused: Widget | None) -> None:
        """Update command bar when focus changes."""
        command_bar = self.query_one(CommandBar)

        if focused is None:
            return

        # Determine context based on focused widget or its ancestors
        if isinstance(focused, TicketList) or self._is_descendant_of(focused, TicketList):
            command_bar.set_context("list")
        elif isinstance(focused, TicketDetail) or self._is_descendant_of(focused, TicketDetail):
            command_bar.set_context("detail")

    def _is_descendant_of(self, widget: Widget, ancestor_type: type) -> bool:
        """Check if widget is a descendant of a widget type."""
        parent = widget.parent
        while parent is not None:
            if isinstance(parent, ancestor_type):
                return True
            parent = parent.parent
        return False

    def action_switch_panel(self) -> None:
        """Switch focus between the list and detail panels."""
        ticket_list = self.query_one(TicketList)
        ticket_detail = self.query_one(TicketDetail)

        if ticket_list.has_focus:
            ticket_detail.focus()
        else:
            ticket_list.focus()


def main() -> None:
    """Entry point for the application."""
    app = RallyTUI()
    app.run()


if __name__ == "__main__":
    main()
```

**Note**: The `watch_focused` method is a watcher that Textual calls automatically when the `focused` reactive property changes. We need to import `Widget` for the type annotation.

### Step 4: Make TicketDetail Focusable

Update the TicketDetail widget to accept focus so Tab can switch to it.

```python
# src/rally_tui/widgets/ticket_detail.py (add to class)
class TicketDetail(VerticalScroll):
    """Displays detailed information about a selected ticket."""

    can_focus = True  # Allow this widget to receive focus

    # ... rest of the class remains the same
```

### Step 5: Update the CSS Stylesheet

Update the CSS to style the command bar and remove Footer styling.

```css
/* src/rally_tui/app.tcss */

/* ... existing styles ... */

/* Command bar styling - replaces Footer */
#command-bar {
    dock: bottom;
    height: 1;
    background: $surface;
    color: $text-muted;
    padding: 0 1;
}
```

Note: We can remove the Footer-specific CSS since we're no longer using Footer.

---

## Testing

### Step 6: Create CommandBar Unit Tests

```python
# tests/test_command_bar.py
"""Tests for the CommandBar widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.widgets import CommandBar, TicketDetail, TicketList


class TestCommandBarWidget:
    """Tests for CommandBar widget behavior."""

    async def test_initial_context_is_list(self) -> None:
        """Command bar should start with list context."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)
            assert command_bar.context == "list"

    async def test_list_context_shows_navigation_commands(self) -> None:
        """List context should show navigation commands."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)
            rendered = str(command_bar.render())
            assert "[j/k] Navigate" in rendered
            assert "[g/G] Jump" in rendered

    async def test_context_changes_on_tab(self) -> None:
        """Pressing Tab should switch focus and update context."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)

            # Initially in list context
            assert command_bar.context == "list"

            # Press Tab to switch to detail
            await pilot.press("tab")
            assert command_bar.context == "detail"

            # Press Tab again to switch back to list
            await pilot.press("tab")
            assert command_bar.context == "list"

    async def test_detail_context_shows_different_commands(self) -> None:
        """Detail context should show detail-specific commands."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            # Switch to detail panel
            await pilot.press("tab")

            command_bar = app.query_one(CommandBar)
            rendered = str(command_bar.render())

            # Should not show list navigation
            assert "[j/k] Navigate" not in rendered
            # Should show common commands
            assert "[Tab] Switch Panel" in rendered
            assert "[q] Quit" in rendered

    async def test_focus_starts_on_list(self) -> None:
        """Focus should start on the ticket list."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            assert ticket_list.has_focus

    async def test_tab_switches_to_detail(self) -> None:
        """Tab should switch focus to detail panel."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            ticket_detail = app.query_one(TicketDetail)

            assert ticket_list.has_focus

            await pilot.press("tab")

            assert ticket_detail.has_focus
            assert not ticket_list.has_focus

    async def test_tab_switches_back_to_list(self) -> None:
        """Tab should switch focus back to list from detail."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Tab to detail
            await pilot.press("tab")
            # Tab back to list
            await pilot.press("tab")

            assert ticket_list.has_focus

    async def test_set_context_updates_display(self) -> None:
        """set_context should update the displayed commands."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)

            command_bar.set_context("detail")
            assert command_bar.context == "detail"

            command_bar.set_context("list")
            assert command_bar.context == "list"
```

### Step 7: Update Snapshot Tests

Add new snapshot tests for the command bar in different contexts.

```python
# tests/test_snapshots.py (add new tests)

def test_command_bar_list_context(self, snap_compare) -> None:
    """Snapshot showing command bar with list context."""
    from rally_tui.app import RallyTUI
    assert snap_compare(RallyTUI())

def test_command_bar_detail_context(self, snap_compare) -> None:
    """Snapshot showing command bar with detail context (after Tab)."""
    from rally_tui.app import RallyTUI
    assert snap_compare(RallyTUI(), press=["tab"])
```

---

## Checklist

Before moving to Iteration 4, verify:

- [ ] App launches with command bar at bottom
- [ ] Command bar shows list commands initially
- [ ] Focus starts on the ticket list
- [ ] Tab key switches focus between list and detail panels
- [ ] Command bar updates immediately when focus changes
- [ ] List context shows: Navigate, Jump, Select, Switch Panel, Quit
- [ ] Detail context shows: Switch Panel, Quit
- [ ] All existing keyboard navigation still works
- [ ] All existing tests still pass
- [ ] New unit tests pass (8 tests for CommandBar)
- [ ] Snapshot tests updated and passing

---

## Files Modified/Created

**Created:**
```
src/rally_tui/widgets/
└── command_bar.py      # New CommandBar widget

tests/
└── test_command_bar.py # New tests for CommandBar
```

**Modified:**
```
src/rally_tui/
├── app.py              # Use CommandBar, add Tab binding, watch focus
├── app.tcss            # Add command bar styling
└── widgets/
    ├── __init__.py     # Export CommandBar
    └── ticket_detail.py # Add can_focus = True
```

---

## Key Concepts Introduced

### Custom Widget with DEFAULT_CSS

```python
class CommandBar(Static):
    DEFAULT_CSS = """
    CommandBar {
        dock: bottom;
        height: 1;
    }
    """
```

Bundling CSS with the widget ensures it works without external stylesheets.

### Watching Reactive Properties

```python
def watch_focused(self, focused: Widget | None) -> None:
    """Called automatically when self.focused changes."""
    # Update UI based on new focused widget
```

Textual's reactive system calls `watch_<property>` methods automatically.

### Focus Management

```python
# Make a widget focusable
class TicketDetail(VerticalScroll):
    can_focus = True

# Switch focus programmatically
ticket_detail.focus()

# Check focus state
if ticket_list.has_focus:
    ...
```

---

## Next Steps (Iteration 4)

Once this iteration is complete:
1. Refine layout and styling
2. Add header with workspace/project info
3. Polish visual design and focus indicators

See `PLAN.md` for the full roadmap.
