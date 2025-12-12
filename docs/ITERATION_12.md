# Iteration 12: Bulk Operations / Multi-Select

## Goal

Enable users to select multiple tickets and perform bulk operations on them, including setting parent, state, iteration, and points.

## Overview

This iteration adds multi-select capability to the ticket list, allowing users to:
1. Select/deselect individual tickets with Space key
2. Select all visible tickets with Ctrl+A
3. Clear selection with Escape
4. Open bulk actions menu with `m` key to perform operations on selected tickets

## Key Features

### Multi-Select UI
- Space key toggles selection on current ticket
- Checkboxes displayed in ticket list: `[ ]` unselected, `[✓]` selected
- Status bar shows selection count when tickets are selected
- Selection persists when navigating list
- Selection cleared when:
  - Filter/search changes
  - Tickets are replaced (refresh)
  - Escape pressed (when not in search mode)

### Bulk Actions Menu (`m` key)
When one or more tickets are selected, pressing `m` opens a modal with:
1. **Set Parent** - Assign a parent Feature to all selected tickets
2. **Set State** - Change state of all selected tickets
3. **Set Iteration** - Move all selected tickets to an iteration
4. **Set Points** - Set story points on all selected tickets

### Operations Behavior
- Parent selection: Only applies to tickets without a parent (skips those with parents)
- State changes: Validates parent requirement for "In-Progress" state
- Progress feedback: Shows "Updating 3/10..." notifications
- Error handling: Reports partial failures ("5 updated, 2 failed")

## UI Layout

### Ticket List with Selection
```
┌─────────────────────────┐
│  TICKETS                │
│                         │
│ [✓]. US1234 User login  │  ← Selected (checkbox + state indicator)
│ [ ]. US1235 Password    │  ← Not selected
│ [✓]+ DE456  Fix null    │  ← Selected, In Progress
│ [ ]. US1236 Add logout  │  ← Not selected
│                         │
└─────────────────────────┘
```

### Bulk Actions Screen
```
┌─────────────────────────────────────────┐
│ Bulk Actions - 3 tickets selected       │
├─────────────────────────────────────────┤
│                                         │
│ Select an action for 3 tickets:         │
│                                         │
│ [1. Set Parent   ]                      │
│ [2. Set State    ]                      │
│ [3. Set Iteration]                      │
│ [4. Set Points   ]                      │
│                                         │
│ Press 1-4 or click, ESC to cancel       │
└─────────────────────────────────────────┘
```

## Implementation Plan

### Step 1: Selection Model in TicketList
**File**: `src/rally_tui/widgets/ticket_list.py`

Add selection tracking to TicketList:
```python
class TicketList(ListView):
    BINDINGS = [
        # ... existing bindings
        Binding("space", "toggle_selection", "Select", show=False),
        Binding("ctrl+a", "select_all", "Select All", show=False),
    ]

    def __init__(self, ...):
        # ... existing init
        self._selected_ids: set[str] = set()

    class SelectionChanged(Message):
        """Posted when selection changes."""
        def __init__(self, count: int) -> None:
            self.count = count
            super().__init__()

    def action_toggle_selection(self) -> None:
        """Toggle selection on current ticket."""
        if self.selected_ticket:
            ticket_id = self.selected_ticket.formatted_id
            if ticket_id in self._selected_ids:
                self._selected_ids.discard(ticket_id)
            else:
                self._selected_ids.add(ticket_id)
            self._update_selection_display()
            self.post_message(self.SelectionChanged(len(self._selected_ids)))

    def action_select_all(self) -> None:
        """Select all visible tickets."""
        self._selected_ids = {t.formatted_id for t in self._tickets}
        self._update_selection_display()
        self.post_message(self.SelectionChanged(len(self._selected_ids)))

    def clear_selection(self) -> None:
        """Clear all selections."""
        self._selected_ids.clear()
        self._update_selection_display()
        self.post_message(self.SelectionChanged(0))

    @property
    def selected_tickets(self) -> list[Ticket]:
        """Get list of selected tickets."""
        return [t for t in self._tickets if t.formatted_id in self._selected_ids]

    @property
    def selection_count(self) -> int:
        """Get count of selected tickets."""
        return len(self._selected_ids)
```

### Step 2: Update TicketListItem Display
**File**: `src/rally_tui/widgets/ticket_list.py`

Modify TicketListItem to show selection checkbox:
```python
class TicketListItem(ListItem):
    def __init__(self, ticket: Ticket, selected: bool = False) -> None:
        super().__init__()
        self.ticket = ticket
        self._selected = selected

    def compose(self) -> ComposeResult:
        checkbox = "[✓]" if self._selected else "[ ]"
        state_symbol = get_state_symbol(self.ticket.state)
        state_color = get_state_color(self.ticket.state)

        with Horizontal(classes="ticket-row"):
            yield Label(checkbox, classes="selection-checkbox")
            yield Label(f"[{state_color}]{state_symbol}[/]", classes="state-indicator")
            yield Label(self.ticket.display_text, classes=f"ticket-text ...")

    def set_selected(self, selected: bool) -> None:
        """Update selection state."""
        self._selected = selected
        checkbox = self.query_one(".selection-checkbox", Label)
        checkbox.update("[✓]" if selected else "[ ]")
```

### Step 3: Create BulkActionsScreen
**File**: `src/rally_tui/screens/bulk_actions_screen.py`

```python
from dataclasses import dataclass
from enum import Enum
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Label, Static
from textual.containers import Vertical


class BulkAction(Enum):
    """Available bulk actions."""
    SET_PARENT = "parent"
    SET_STATE = "state"
    SET_ITERATION = "iteration"
    SET_POINTS = "points"


class BulkActionsScreen(Screen[BulkAction | None]):
    """Screen for selecting a bulk action."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("1", "select_parent", "Parent", show=False),
        Binding("2", "select_state", "State", show=False),
        Binding("3", "select_iteration", "Iteration", show=False),
        Binding("4", "select_points", "Points", show=False),
    ]

    def __init__(self, count: int) -> None:
        super().__init__()
        self._count = count

    def compose(self) -> ComposeResult:
        with Vertical(id="bulk-actions-container"):
            yield Label(f"Bulk Actions - {self._count} tickets selected", id="bulk-title")
            yield Static(f"Select an action for {self._count} tickets:")
            yield Button("1. Set Parent", id="btn-parent", variant="primary")
            yield Button("2. Set State", id="btn-state", variant="primary")
            yield Button("3. Set Iteration", id="btn-iteration", variant="primary")
            yield Button("4. Set Points", id="btn-points", variant="primary")
            yield Static("Press 1-4 or click, ESC to cancel", id="bulk-hint")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_select_parent(self) -> None:
        self.dismiss(BulkAction.SET_PARENT)

    def action_select_state(self) -> None:
        self.dismiss(BulkAction.SET_STATE)

    def action_select_iteration(self) -> None:
        self.dismiss(BulkAction.SET_ITERATION)

    def action_select_points(self) -> None:
        self.dismiss(BulkAction.SET_POINTS)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-parent":
            self.dismiss(BulkAction.SET_PARENT)
        elif button_id == "btn-state":
            self.dismiss(BulkAction.SET_STATE)
        elif button_id == "btn-iteration":
            self.dismiss(BulkAction.SET_ITERATION)
        elif button_id == "btn-points":
            self.dismiss(BulkAction.SET_POINTS)
```

### Step 4: Add Bulk Operations to Protocol
**File**: `src/rally_tui/services/protocol.py`

```python
@dataclass
class BulkResult:
    """Result of a bulk operation."""
    success_count: int
    failed_count: int
    updated_tickets: list[Ticket]
    errors: list[str]

class RallyClientProtocol(Protocol):
    # ... existing methods

    def bulk_set_parent(
        self, tickets: list[Ticket], parent_id: str
    ) -> BulkResult:
        """Set parent on multiple tickets."""
        ...

    def bulk_update_state(
        self, tickets: list[Ticket], state: str
    ) -> BulkResult:
        """Update state on multiple tickets."""
        ...

    def bulk_set_iteration(
        self, tickets: list[Ticket], iteration_name: str | None
    ) -> BulkResult:
        """Set iteration on multiple tickets."""
        ...

    def bulk_update_points(
        self, tickets: list[Ticket], points: float
    ) -> BulkResult:
        """Update points on multiple tickets."""
        ...
```

### Step 5: Implement Bulk Operations in Clients
**Files**: `mock_client.py`, `rally_client.py`

```python
def bulk_set_parent(self, tickets: list[Ticket], parent_id: str) -> BulkResult:
    """Set parent on multiple tickets."""
    success = 0
    failed = 0
    updated = []
    errors = []

    for ticket in tickets:
        # Skip tickets that already have a parent
        if ticket.parent_id:
            continue

        try:
            result = self.set_parent(ticket, parent_id)
            if result:
                updated.append(result)
                success += 1
            else:
                failed += 1
                errors.append(f"{ticket.formatted_id}: Failed to set parent")
        except Exception as e:
            failed += 1
            errors.append(f"{ticket.formatted_id}: {str(e)}")

    return BulkResult(success, failed, updated, errors)
```

### Step 6: Integrate into App
**File**: `src/rally_tui/app.py`

```python
BINDINGS = [
    # ... existing bindings
    Binding("m", "bulk_actions", "Bulk", show=False),
]

def on_ticket_list_selection_changed(self, event: TicketList.SelectionChanged) -> None:
    """Update status bar when selection changes."""
    status_bar = self.query_one(StatusBar)
    status_bar.set_selection_count(event.count)

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
        return

    ticket_list = self.query_one(TicketList)
    selected = ticket_list.selected_tickets

    if action == BulkAction.SET_PARENT:
        self._bulk_set_parent(selected)
    elif action == BulkAction.SET_STATE:
        self._bulk_set_state(selected)
    # ... etc
```

## Key Bindings

| Key | Context | Action |
|-----|---------|--------|
| `Space` | list | Toggle selection on current ticket |
| `Ctrl+A` | list | Select all visible tickets |
| `Escape` | list (with selection) | Clear selection |
| `m` | list (with selection) | Open bulk actions menu |

## Test Coverage

### Unit Tests
- TicketList selection toggle (single item)
- TicketList select all
- TicketList clear selection
- TicketList selection count
- TicketList selected_tickets property
- TicketListItem checkbox display
- BulkActionsScreen button rendering
- BulkActionsScreen number key bindings
- BulkActionsScreen dismiss with action
- BulkResult dataclass

### Integration Tests
- Full bulk parent selection flow
- Full bulk state change flow
- Bulk operation with partial failures
- Selection cleared on filter change
- Selection count in status bar

### Snapshot Tests
- Ticket list with selections
- Bulk actions screen

## Files to Create/Modify

### New Files
- `src/rally_tui/screens/bulk_actions_screen.py`
- `tests/test_bulk_actions_screen.py`
- `tests/test_bulk_operations.py`

### Modified Files
- `src/rally_tui/widgets/ticket_list.py` - Add selection model
- `src/rally_tui/widgets/status_bar.py` - Add selection count display
- `src/rally_tui/services/protocol.py` - Add bulk operation methods
- `src/rally_tui/services/mock_client.py` - Implement bulk operations
- `src/rally_tui/services/rally_client.py` - Implement bulk operations
- `src/rally_tui/screens/__init__.py` - Export new screen
- `src/rally_tui/app.py` - Add bulk action handling
- `src/rally_tui/app.tcss` - Add styling for checkboxes
- `tests/test_ticket_list.py` - Add selection tests
- `tests/test_status_bar.py` - Add selection count tests
- `tests/test_services.py` - Add bulk operation tests

## Commit Plan

1. `feat: add selection model to TicketList widget`
2. `feat: update TicketListItem to show selection checkbox`
3. `feat: create BulkActionsScreen modal`
4. `feat: add bulk operations to protocol`
5. `feat: implement bulk operations in MockRallyClient`
6. `feat: implement bulk operations in RallyClient`
7. `feat: integrate bulk actions into app`
8. `test: add comprehensive tests for bulk operations`
9. `docs: update README and PLAN for Iteration 12`
10. `chore: bump version to 0.4.0`

## Notes

- Parent setting only applies to tickets without existing parents
- State changes to "In-Progress" will skip tickets without parents (no parent prompt in bulk mode)
- All operations are performed sequentially (not parallel) to avoid Rally API rate limits
- Progress notifications update every 5 tickets or on completion
