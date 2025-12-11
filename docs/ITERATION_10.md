# Iteration 10: Iteration & User Filtering

## Overview

This iteration adds the ability to navigate between Rally iterations (sprints) and toggle between viewing your tickets vs. all team tickets. Currently, the app defaults to showing the current iteration filtered to the current user - this iteration makes those filters controllable.

## Goals

- Allow users to switch between iterations (current, previous, next, backlog)
- Toggle between "My tickets" and "All team tickets"
- Display current filter state clearly in status bar
- Provide keyboard shortcuts for quick navigation

## Features

### 1. Iteration Picker Screen (`i` key)

A modal screen showing available iterations:

```
┌─────────────────────────────────────────┐
│           Select Iteration              │
├─────────────────────────────────────────┤
│  [1] ● Current: Sprint 26 (Dec 2-15)    │
│  [2]   Previous: Sprint 25 (Nov 18-Dec 1)│
│  [3]   Next: Sprint 27 (Dec 16-29)      │
│  [4]   Backlog (Unscheduled)            │
│  [5]   All Iterations                   │
├─────────────────────────────────────────┤
│  [1-5] Select  [Esc] Cancel             │
└─────────────────────────────────────────┘
```

**Behavior:**
- Shows current, previous, and next iteration with dates
- "Backlog" option shows unscheduled tickets (no iteration)
- "All Iterations" removes the iteration filter
- Current selection highlighted with `●`
- Number keys for quick selection

### 2. User Filter Toggle (`u` key)

Toggle between:
- **My tickets** (default) - `Owner.DisplayName = "{current_user}"`
- **All tickets** - No owner filter

Status bar indicator: `[Me]` or `[All]`

### 3. Quick Iteration Navigation

| Key | Action |
|-----|--------|
| `[` | Previous iteration |
| `]` | Next iteration |
| `i` | Open iteration picker |
| `u` | Toggle user filter |

### 4. Status Bar Updates

Current status bar:
```
rally-tui │ Project Name │ Connected as User
```

New status bar with filters:
```
rally-tui │ Project Name │ Sprint 26 [Me] │ Connected as User
```

Filter indicators:
- Iteration name (or "Backlog" / "All")
- `[Me]` or `[All]` for user filter

## Implementation Plan

### Step 1: Add iteration list to RallyClient

**Files:** `services/protocol.py`, `services/rally_client.py`, `services/mock_client.py`

Add methods:
```python
def get_iterations(self, count: int = 5) -> list[Iteration]:
    """Get recent iterations (past, current, future)."""

def get_previous_iteration(self) -> str | None:
    """Get name of iteration before current."""

def get_next_iteration(self) -> str | None:
    """Get name of iteration after current."""
```

New model:
```python
@dataclass(frozen=True)
class Iteration:
    name: str
    start_date: date
    end_date: date
    is_current: bool = False
```

### Step 2: Create IterationScreen

**Files:** `screens/iteration_screen.py`

Modal screen for iteration selection:
- List of iterations with dates
- Backlog option
- All iterations option
- Returns selected iteration name or special values ("_backlog_", "_all_")

### Step 3: Update StatusBar with filter display

**Files:** `widgets/status_bar.py`

Add properties:
- `iteration_filter: str | None`
- `user_filter: Literal["me", "all"]`

Update display to show current filters.

### Step 4: Add filter state to app

**Files:** `app.py`

Add instance variables:
- `_iteration_filter: str | None` (None = current iteration)
- `_user_filter: Literal["me", "all"]` = "me"

Add methods:
- `_refresh_tickets()` - Reload with current filters
- `_build_query()` - Build Rally query from filters

### Step 5: Add key bindings

**Files:** `app.py`

| Binding | Action |
|---------|--------|
| `i` | `action_iteration_picker` |
| `u` | `action_toggle_user_filter` |
| `[` | `action_prev_iteration` |
| `]` | `action_next_iteration` |

### Step 6: Update MockRallyClient

**Files:** `services/mock_client.py`

Add mock iterations for testing:
- 3 sample iterations (past, current, future)
- Support filtering by iteration name
- Support filtering by user

## Test Plan

### Unit Tests

**test_iteration_model.py:**
- Iteration dataclass creation
- Date formatting
- is_current property

**test_iteration_screen.py:**
- Screen renders with iteration list
- Number key selection
- Escape cancels
- Returns correct values

**test_status_bar.py (additions):**
- Filter display with iteration
- Filter display with user filter
- Both filters displayed

**test_rally_client.py (additions):**
- get_iterations returns correct list
- get_previous_iteration
- get_next_iteration

### Integration Tests

- Iteration picker opens and closes
- Selecting iteration reloads tickets
- User filter toggle reloads tickets
- Quick navigation with `[` and `]`
- Status bar updates on filter change

### Snapshot Tests

- Iteration picker screen
- Status bar with filters

## UI Mockups

### Iteration Picker
```
┌──────────────────────────────────────────────────────┐
│                  Select Iteration                     │
├──────────────────────────────────────────────────────┤
│                                                       │
│   [1] ● FY26-Q1 PI Sprint 3 (Dec 2 - Dec 15)        │
│   [2]   FY26-Q1 PI Sprint 2 (Nov 18 - Dec 1)        │
│   [3]   FY26-Q1 PI Sprint 4 (Dec 16 - Dec 29)       │
│   [4]   Backlog (Unscheduled)                        │
│   [5]   All Iterations                               │
│                                                       │
├──────────────────────────────────────────────────────┤
│   [1-5] Select   [Esc] Cancel                        │
└──────────────────────────────────────────────────────┘
```

### Status Bar with Filters
```
┌──────────────────────────────────────────────────────────────────┐
│ rally-tui │ AppNeta-FourNines │ Sprint 3 [Me] │ Connected as Dan │
└──────────────────────────────────────────────────────────────────┘
```

### Status Bar - Backlog View
```
┌──────────────────────────────────────────────────────────────────┐
│ rally-tui │ AppNeta-FourNines │ Backlog [All] │ Connected as Dan │
└──────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Rally Query Building

Current query (default):
```
((Iteration.Name = "Sprint 3") AND (Owner.DisplayName = "Daniel Elliot"))
```

With "All" user filter:
```
(Iteration.Name = "Sprint 3")
```

With "Backlog" iteration:
```
((Iteration = null) AND (Owner.DisplayName = "Daniel Elliot"))
```

With "All Iterations" + "All Users":
```
(no query - returns all tickets in project)
```

### Filter State Management

```python
class RallyTUI(App):
    # Filter state
    _iteration_filter: str | None = None  # None = use current_iteration
    _user_filter: Literal["me", "all"] = "me"

    # Special values for iteration_filter
    BACKLOG = "_backlog_"  # Iteration = null
    ALL_ITERATIONS = "_all_"  # No iteration filter
```

## Deliverables

1. **Iteration model** - `models/iteration.py`
2. **IterationScreen** - `screens/iteration_screen.py`
3. **Updated StatusBar** - Filter display
4. **Updated RallyClient** - Iteration list methods
5. **Updated MockRallyClient** - Mock iterations
6. **Updated app.py** - Filter state and key bindings
7. **Tests** - Unit, integration, snapshot
8. **Documentation** - README, CLAUDE.md updates

## Success Criteria

- [ ] User can press `i` to open iteration picker
- [ ] Selecting iteration reloads ticket list
- [ ] User can press `u` to toggle between My/All tickets
- [ ] Status bar shows current filters
- [ ] `[` and `]` navigate between iterations
- [ ] Backlog view shows unscheduled tickets
- [ ] All tests pass
- [ ] Documentation updated
