# Iteration 4: Layout Polish & Status Bar

## Overview

Iteration 4 focuses on visual polish and adding a status bar to display workspace/project information. The core layout is already functional from previous iterations, so this iteration enhances the UI with:

1. **Status Bar Widget** - Shows workspace/project info (placeholder values until Rally integration)
2. **Panel Titles** - Add border titles to panels for clearer visual hierarchy
3. **Visual Polish** - Enhanced CSS styling for a more professional appearance
4. **Responsive Layout** - Better handling of different terminal sizes

## Pre-Implementation Checklist

Before starting, verify:
- [x] Iteration 3 complete with 54 tests passing
- [x] CommandBar widget working with context switching
- [x] Two-panel layout with focus indicators
- [x] Color coding for ticket types

## Tasks

### Step 1: Create StatusBar Widget

Create a new `StatusBar` widget that displays:
- Workspace name (placeholder: "My Workspace")
- Project name (placeholder: "My Project")
- Connection status indicator (placeholder: "Offline")

**File**: `src/rally_tui/widgets/status_bar.py`

```python
class StatusBar(Static):
    """Displays workspace/project info and connection status."""

    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        height: 1;
        background: $primary-background;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        workspace: str = "Not Connected",
        project: str = "",
        *,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._workspace = workspace
        self._project = project

    def compose(self) -> ComposeResult:
        # Display format: "Workspace: X | Project: Y | Status"
        ...
```

### Step 2: Add Panel Titles

Add border titles to the TicketList and TicketDetail panels for clearer visual hierarchy.

**Changes to `app.py`**:
```python
def on_mount(self) -> None:
    # Set panel titles
    self.query_one("#ticket-list").border_title = "Tickets"
    self.query_one("#ticket-detail").border_title = "Details"
```

### Step 3: Update App Layout

Integrate the StatusBar into the app layout between Header and main content.

**Changes to `app.py`**:
```python
def compose(self) -> ComposeResult:
    yield Header()
    yield StatusBar(id="status-bar")
    with Horizontal(id="main-container"):
        yield TicketList(SAMPLE_TICKETS, id="ticket-list")
        yield TicketDetail(id="ticket-detail")
    yield CommandBar(id="command-bar")
```

### Step 4: Enhance CSS Styling

Update `app.tcss` with improved styling:
- Status bar styling
- Panel title colors
- Better spacing and visual hierarchy

**New CSS additions**:
```css
/* Status bar styling */
#status-bar {
    dock: top;
    height: 1;
    background: $primary-background;
    color: $text;
    padding: 0 1;
}

/* Panel titles */
#ticket-list {
    border-title-align: center;
}

#ticket-detail {
    border-title-align: center;
}
```

### Step 5: Write Tests

Create tests for the new StatusBar widget.

**File**: `tests/test_status_bar.py`

Tests to write:
- StatusBar renders with default values
- StatusBar displays workspace name
- StatusBar displays project name
- StatusBar shows "Not Connected" when no workspace set
- StatusBar appears in app layout

### Step 6: Update Snapshot Tests

Update snapshot baselines to reflect the new layout with StatusBar and panel titles.

## Implementation Order

1. **Commit 1**: Create StatusBar widget with tests
2. **Commit 2**: Add panel titles to TicketList and TicketDetail
3. **Commit 3**: Integrate StatusBar into app layout
4. **Commit 4**: Enhance CSS styling
5. **Commit 5**: Update snapshot baselines
6. **Commit 6**: Update documentation

## Test Coverage Goals

| Test Type | Description |
|-----------|-------------|
| Unit | StatusBar renders correctly |
| Unit | StatusBar shows workspace/project |
| Unit | StatusBar handles empty values |
| Unit | Panel titles are set correctly |
| Snapshot | Full app layout with StatusBar |
| Snapshot | Different terminal sizes |

## Files to Create/Modify

### New Files
- `src/rally_tui/widgets/status_bar.py`
- `tests/test_status_bar.py`

### Modified Files
- `src/rally_tui/widgets/__init__.py` - Export StatusBar
- `src/rally_tui/app.py` - Add StatusBar to layout, set panel titles
- `src/rally_tui/app.tcss` - Add status bar styling
- `tests/snapshots/*` - Update baselines

## Visual Mockup

```
┌─────────────────────────────────────────────────────────────────────┐
│  Rally TUI                                              12:34:56 PM │  <- Header
├─────────────────────────────────────────────────────────────────────┤
│  Workspace: My Workspace | Project: My Project | ● Offline          │  <- StatusBar (new)
├──────────────── Tickets ─────────┬────────────── Details ───────────┤
│  ▶ US1234 User login            │  US1234 - User login feature      │
│    US1235 Password reset        │  ─────────────────────────────    │
│    DE456  Fix null pointer      │  State: In Progress               │
│    US1236 Add logout            │  Owner: John Smith                │
│                                 │  Iteration: Sprint 5              │
│                                 │  Points: 3                        │
│                                 │                                   │
│                                 │  Description:                     │
│                                 │  As a user, I want to log in...   │
├─────────────────────────────────┴───────────────────────────────────┤
│  [j/k] Navigate  [g/G] Jump  [Enter] Select  [Tab] Switch  [q] Quit │  <- CommandBar
└─────────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Border Titles
Textual widgets with borders support `border_title` attribute:
```python
widget.border_title = "My Title"
```

### Static Widget with Reactive Content
The StatusBar can use reactive properties to update when workspace/project changes:
```python
workspace = reactive("Not Connected")
project = reactive("")

def watch_workspace(self, value: str) -> None:
    self._update_display()
```

### Placeholder Values
Since Rally integration isn't until Iteration 6, use placeholder values:
- Workspace: "My Workspace" or "Not Connected"
- Project: "My Project"
- Status: "Offline" (will become "Connected" in Iteration 6)

## Success Criteria

- [ ] StatusBar widget created and tested
- [ ] Panel titles visible on TicketList and TicketDetail
- [ ] StatusBar shows workspace/project placeholders
- [ ] All tests pass (target: 60+ tests)
- [ ] Snapshots updated and passing
- [ ] Documentation updated

## Notes

- The StatusBar is designed to be easily updated when Rally integration is added in Iteration 6
- Panel titles use Textual's built-in border title feature
- The "Offline" status indicator will change to show connection state in future iterations
