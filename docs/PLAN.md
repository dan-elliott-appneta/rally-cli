# Rally CLI - Project Plan

## Overview

A Python TUI (Text User Interface) application for interacting with Rally (Broadcom) via the WSAPI. The interface features a three-panel layout: ticket list (left), ticket details (right), and context-sensitive command bar (bottom).

## Goals

- Provide an intuitive TUI for browsing and managing Rally work items
- Full keyboard navigation with vim-style bindings
- Testable architecture with snapshot testing for UI components
- Clean separation between UI and Rally API logic

---

## Architecture

### Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| TUI Framework | **Textual** | Modern async Python TUI, CSS-like styling, built-in testing support |
| Rally API | **pyral** | Official Python toolkit for Rally WSAPI |
| Testing | **pytest + pytest-textual-snapshot** | Snapshot testing for visual regression, async test support |
| Config | **pydantic-settings** | Type-safe configuration with env/file support |

### Project Structure

```
rally-cli/
├── pyproject.toml
├── README.md
├── src/
│   └── rally_tui/
│       ├── __init__.py
│       ├── app.py              # Main Textual application
│       ├── app.tcss            # CSS stylesheet
│       ├── config.py           # Configuration (pydantic-settings)
│       ├── widgets/
│       │   ├── __init__.py
│       │   ├── ticket_list.py  # Left panel - scrollable ticket list
│       │   ├── ticket_detail.py # Right panel - ticket details view
│       │   ├── command_bar.py  # Bottom panel - context commands
│       │   ├── status_bar.py   # Top bar - workspace/project/status
│       │   └── search_input.py # Search input for filtering
│       ├── models/
│       │   ├── __init__.py
│       │   ├── ticket.py       # Ticket data models (decoupled from pyral)
│       │   └── sample_data.py  # Sample tickets for offline mode
│       └── services/
│           ├── __init__.py
│           ├── protocol.py     # RallyClientProtocol interface
│           ├── rally_client.py # Real Rally API client (pyral)
│           └── mock_client.py  # Mock client for testing/offline
├── tests/
│   ├── conftest.py             # Fixtures, mock Rally client
│   ├── test_ticket_model.py
│   ├── test_ticket_list.py
│   ├── test_ticket_detail.py
│   ├── test_command_bar.py
│   ├── test_status_bar.py
│   ├── test_search_input.py
│   ├── test_services.py
│   ├── test_config.py
│   ├── test_rally_client.py
│   ├── test_snapshots.py
│   └── __snapshots__/          # SVG snapshots for visual tests
└── docs/
    ├── API.md                  # Rally WSAPI reference
    ├── PLAN.md                 # This file
    └── ITERATION_*.md          # Implementation guides (1-7)
```

### Testability Strategy

1. **Dependency Injection**: Rally client is injected into the app, allowing mock substitution
2. **Data Models**: Internal `Ticket` model decouples UI from pyral response objects
3. **Snapshot Testing**: Visual regression tests using pytest-textual-snapshot
4. **Unit Tests**: Individual widget behavior tested in isolation
5. **Integration Tests**: Full app flow with mock Rally data

```python
# Example: Injecting mock client for tests
class RallyTUI(App):
    def __init__(self, client: RallyClientProtocol):
        self.client = client
        super().__init__()

# In tests
def test_ticket_list(snap_compare):
    mock_client = MockRallyClient(tickets=[...])
    app = RallyTUI(client=mock_client)
    assert snap_compare(app)
```

---

## UI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Rally TUI - Workspace: MyWorkspace | Project: MyProject            │
├─────────────────────────┬───────────────────────────────────────────┤
│  TICKETS                │  DETAILS                                  │
│                         │                                           │
│  ▶ US1234 User login    │  US1234 - User login feature              │
│    US1235 Password rst  │  ─────────────────────────────────────    │
│    DE456  Fix null ptr  │  State: In Progress                       │
│    US1236 Add logout    │  Owner: John Smith                        │
│    TA789  Write tests   │  Iteration: Sprint 5                      │
│                         │  Points: 3                                │
│                         │                                           │
│                         │  Description:                             │
│                         │  As a user, I want to log in so that...   │
│                         │                                           │
│                         │  Tasks (2/3 complete):                    │
│                         │  ☑ Design login form                      │
│                         │  ☑ Implement backend                      │
│                         │  ☐ Add validation                         │
│                         │                                           │
├─────────────────────────┴───────────────────────────────────────────┤
│  [j/k] Navigate  [Enter] Open  [e] Edit  [c] Create  [/] Search  [?]│
└─────────────────────────────────────────────────────────────────────┘
```

### Panel Specifications

**Left Panel (Ticket List)**
- Scrollable list of tickets (FormattedID + Name truncated)
- Visual indicator for selected item
- Type icons/colors (US=blue, DE=red, TA=green)
- Keyboard: j/k or ↑/↓ to navigate, Enter to select

**Right Panel (Ticket Details)**
- Full ticket information for selected item
- Sections: Header, Metadata, Description, Related Items
- Scrollable for long content

**Bottom Bar (Command Bar)**
- Context-sensitive based on current focus/selection
- Shows available keyboard shortcuts
- Updates when context changes (e.g., different commands in edit mode)

---

## Iterative Build Plan

### Iteration 1: Project Skeleton & Static List - COMPLETE

**Goal**: Display a hardcoded list of tickets, navigate with keyboard

**Detailed Guide**: See [ITERATION_1.md](./ITERATION_1.md) for step-by-step implementation.

**Tasks**:
- [x] Initialize project structure (src layout) and pyproject.toml
- [x] Create `Ticket` dataclass model with type prefix detection
- [x] Create sample data module with 8 hardcoded tickets
- [x] Build `TicketList` widget extending Textual's ListView
- [x] Implement vim navigation (j/k/g/G) and arrow keys
- [x] Add visual highlight and ticket-type color coding (US=green, DE=red, TA=yellow, TC=blue)
- [x] Create CSS stylesheet for styling
- [x] Write unit tests for model and widget
- [x] Write snapshot tests for visual regression

**Deliverable**: App displays static ticket list, full keyboard navigation works

**Test Coverage**:
- Unit: Ticket model (display_text, type_prefix, immutability, equality)
- Unit: Widget navigation (j/k, arrows, g/G jump to top/bottom)
- Unit: TicketHighlighted message posted on cursor move
- Snapshot: Initial render with first item selected
- Snapshot: Selection moved down twice
- Snapshot: Selection at bottom (G key)
- Snapshot: Different terminal size (60x15)

**Key Files Created**:
```
src/rally_tui/
├── app.py              # Main RallyTUI application
├── app.tcss            # CSS stylesheet
├── models/
│   ├── ticket.py       # Ticket dataclass
│   └── sample_data.py  # 8 hardcoded tickets
└── widgets/
    └── ticket_list.py  # TicketList widget (extends ListView)
tests/
├── conftest.py         # Fixtures
├── test_ticket_model.py
├── test_ticket_list.py
└── test_snapshots.py
```

**Key Bindings**:
| Key | Action |
|-----|--------|
| j / ↓ | Move down |
| k / ↑ | Move up |
| g | Jump to top |
| G | Jump to bottom |
| Enter | Select (logs only in Iteration 1) |
| q | Quit |

---

### Iteration 2: Details Panel (Right Side) - COMPLETE

**Goal**: Show ticket details when a ticket is selected in a two-panel layout

**Detailed Guide**: See [ITERATION_2.md](./ITERATION_2.md) for step-by-step implementation.

**Tasks**:
- [x] Create `TicketDetail` widget (extends VerticalScroll)
- [x] Add new fields to Ticket model (description, owner, iteration, points)
- [x] Update sample data with all new fields
- [x] Implement two-panel layout with Horizontal container
- [x] Use reactive property for ticket updates (`watch_ticket`)
- [x] Display ticket fields (ID, Name, Type, State, Owner, Iteration, Points, Description)
- [x] Handle empty/null states ("Unassigned", "Unscheduled", "—" for no points)
- [x] Update CSS for two-panel layout (35% / 1fr split)
- [x] Write unit tests for TicketDetail widget (13 tests)
- [x] Update snapshot tests for new layout (3 new + 4 updated = 7 total)

**Deliverable**: Two-panel layout where selecting a ticket updates the right panel

**Detail Panel Fields**:
| Field | Display | Empty State |
|-------|---------|-------------|
| Owner | `ticket.owner` | "Unassigned" |
| Iteration | `ticket.iteration` | "Unscheduled" |
| Points | `ticket.points` | "—" |
| State | `ticket.state` | (required) |
| Description | `ticket.description` | (empty) |

**Test Coverage** (16 new tests):
- Unit: Detail shows first ticket on mount
- Unit: Detail updates on navigation
- Unit: Detail shows ticket name, state, owner, description
- Unit: "Unassigned" shown when owner is None
- Unit: Iteration displayed correctly
- Unit: "Unscheduled" shown when iteration is None
- Unit: Points displayed correctly
- Unit: "—" shown when points is None
- Snapshot: Two-panel layout with detail visible
- Snapshot: Detail after navigation
- Snapshot: Defect type in detail panel

**Key Files**:
```
src/rally_tui/
├── app.py              # Horizontal container, on_mount
├── app.tcss            # Two-panel CSS layout
├── models/
│   ├── ticket.py       # Add description, iteration, points fields
│   └── sample_data.py  # Add all new field values
└── widgets/
    ├── __init__.py     # Export TicketDetail
    └── ticket_detail.py # New widget
tests/
└── test_ticket_detail.py
```

**Key Concepts**:
- Horizontal container for side-by-side layout
- Reactive properties with `watch_` methods
- CSS fractional units (`1fr`) for flexible sizing
- Null-safe field display with sensible defaults

---

### Iteration 3: Command Bar (Bottom) ✅ COMPLETE

**Goal**: Context-sensitive command hints at bottom

**Detailed Guide**: See [ITERATION_3.md](./ITERATION_3.md) for step-by-step implementation.

**Tasks**:
- [x] Create `CommandBar` widget (extends Static with DEFAULT_CSS)
- [x] Define command sets for different contexts (list vs detail)
- [x] Update commands based on focused widget (via action_switch_panel)
- [x] Make TicketDetail focusable (`can_focus = True`)
- [x] Add Tab key binding with priority=True to switch focus between panels
- [x] Add CommandBar to app layout
- [x] Write unit tests for CommandBar (13 tests)
- [x] Update snapshot tests for command bar (7 tests updated)

**Implementation Notes**:
- Used `_current_ctx` instead of `_context` to avoid Textual internal conflict
- Tab binding requires `priority=True` to override default focus cycling
- 54 total tests passing

**Deliverable**: Bottom bar shows relevant commands, updates on Tab press, Tab switches panels

**Command Contexts**:
| Context | Commands Shown |
|---------|---------------|
| list | `[j/k] Navigate  [g/G] Jump  [Enter] Select  [Tab] Switch Panel  [q] Quit` |
| detail | `[Tab] Switch Panel  [q] Quit` |

**Test Coverage**:
- Unit: Initial context is list
- Unit: List context shows navigation commands
- Unit: Tab switches focus and updates context
- Unit: Detail context shows different commands
- Unit: Focus starts on list
- Unit: Tab switches to detail
- Unit: Tab switches back to list
- Unit: set_context updates display
- Snapshot: Command bar with list context
- Snapshot: Command bar with detail context

**Key Files**:
```
src/rally_tui/widgets/
└── command_bar.py      # New CommandBar widget

src/rally_tui/
├── app.py              # Use CommandBar, add Tab binding, watch focus
├── app.tcss            # Command bar styling
└── widgets/
    ├── __init__.py     # Export CommandBar
    └── ticket_detail.py # Add can_focus = True

tests/
└── test_command_bar.py # New tests
```

**Key Concepts**:
- Custom widget with `DEFAULT_CSS` for bundled styling
- `watch_focused` watcher for reactive focus tracking
- `can_focus = True` to make widgets focusable
- `widget.focus()` for programmatic focus management

---

### Iteration 4: Layout Polish & Status Bar ✅ COMPLETE

**Goal**: Visual polish and status bar for workspace/project info

**Detailed Guide**: See [ITERATION_4.md](./ITERATION_4.md) for step-by-step implementation.

**Tasks**:
- [x] Create `StatusBar` widget (extends Static)
- [x] Display workspace/project info (placeholders until Rally integration)
- [x] Add connection status indicator (Offline placeholder)
- [x] Add border titles to panels ("Tickets", "Details")
- [x] Enhance CSS styling for visual polish
- [x] Write unit tests for StatusBar widget (17 tests)
- [x] Update snapshot tests for new layout (7 updated)

**Implementation Notes**:
- StatusBar uses `display_content` property for test assertions
- Panel titles set via `border_title` attribute in `on_mount`
- CSS uses `border-title-align: center` for centered titles
- 73 total tests passing

**Deliverable**: StatusBar showing workspace/project info, polished panel titles

**Test Coverage**:
- Unit: StatusBar renders with default values
- Unit: StatusBar displays workspace/project names
- Unit: StatusBar handles empty values gracefully
- Unit: Panel titles are set correctly
- Snapshot: Full app layout with StatusBar
- Snapshot: Different terminal sizes

**Key Files**:
```
src/rally_tui/widgets/
└── status_bar.py      # New StatusBar widget

src/rally_tui/
├── app.py             # Add StatusBar, set panel titles
├── app.tcss           # Status bar styling
└── widgets/
    └── __init__.py    # Export StatusBar

tests/
└── test_status_bar.py # New tests
```

**Key Concepts**:
- `border_title` attribute for panel titles
- Placeholder values for pre-Rally-integration state
- Reactive properties for future workspace/project updates

---

### Iteration 5: Service Layer & Dependency Injection ✅ COMPLETE

**Goal**: Clean service layer with dependency injection for testability

**Detailed Guide**: See [ITERATION_5.md](./ITERATION_5.md) for step-by-step implementation.

**Tasks**:
- [x] Create `RallyClientProtocol` (Protocol class for structural subtyping)
- [x] Implement `MockRallyClient` with fixture data
- [x] Create services module with proper exports
- [x] Modify `RallyTUI` to accept injectable client
- [x] Add factory fixtures for test data generation
- [x] Write service layer tests
- [x] Update existing tests if needed

**Implementation Notes**:
- MockRallyClient defaults to SAMPLE_TICKETS for backward compatibility
- RallyClientProtocol uses Python's `Protocol` for structural subtyping
- Client injection pattern: `RallyTUI(client=optional_client)`
- 100 total tests passing (73 from Iteration 4 + 27 new service tests)

**Deliverable**: App uses injectable client, tests can inject custom clients

**Test Coverage**:
- Unit: MockRallyClient.get_tickets() returns all tickets
- Unit: MockRallyClient.get_tickets(query) filters correctly
- Unit: MockRallyClient.get_ticket(id) returns correct ticket
- Unit: MockRallyClient workspace/project properties
- Integration: RallyTUI renders with injected client
- Integration: StatusBar shows client's workspace/project

**Key Files**:
```
src/rally_tui/services/
├── __init__.py         # Module exports
├── protocol.py         # RallyClientProtocol definition
└── mock_client.py      # MockRallyClient implementation

src/rally_tui/
└── app.py              # Accept client parameter

tests/
├── conftest.py         # Add factory fixtures
└── test_services.py    # Service layer tests
```

**Key Concepts**:
- Python `Protocol` for structural subtyping (duck typing with type hints)
- Dependency injection pattern for testability
- Factory fixtures in pytest for test data generation
- Default to MockRallyClient with SAMPLE_TICKETS for backward compatibility

---

### Iteration 6: Real Rally Integration ✅ COMPLETE

**Goal**: Connect to actual Rally API with proper configuration and error handling

**Detailed Guide**: See [ITERATION_6.md](./ITERATION_6.md) for step-by-step implementation.

**Tasks**:
- [x] Add configuration with pydantic-settings (RallyConfig)
- [x] Implement `RallyClient` using pyral
- [x] Map pyral responses to internal `Ticket` model
- [x] Update StatusBar with connection status (Connected/Offline)
- [x] Update app to accept config and fall back gracefully
- [x] Write tests for RallyClient mapping and configuration
- [x] Update documentation
- [x] Add default filter for current iteration and current user

**Implementation Notes**:
- RallyConfig loads from RALLY_* environment variables
- RallyClient maps HierarchicalRequirement → UserStory, handles nested objects
- App falls back to MockRallyClient on connection failure
- **Default filter**: When connected, tickets are filtered to show only items in the current iteration owned by the API key's user
- RallyClient fetches current user via `getUserInfo()` and current iteration via date-range query
- 177 total tests passing (161 from Iteration 7 + 16 new default filter tests)

**Deliverable**: App connects to Rally when configured, falls back to mock data when offline

**Test Coverage**:
- Unit: RallyConfig default values and environment loading
- Unit: Entity-to-Ticket mapping (all field types)
- Unit: Prefix-to-entity-type detection
- Unit: StatusBar connection status display
- Unit: Current user and iteration fetching
- Unit: Default query building (both, either, or neither user/iteration)
- Integration: App with and without configuration

**Key Files**:
```
src/rally_tui/
├── config.py               # RallyConfig with pydantic-settings
├── services/
│   ├── rally_client.py     # Real Rally API client
│   └── __init__.py         # Export RallyClient
├── widgets/
│   └── status_bar.py       # Add connected parameter
└── app.py                  # Accept config, show status

tests/
├── test_rally_client.py    # Mapping and detection tests
└── test_config.py          # Configuration tests
```

**Key Concepts**:
- pydantic-settings for environment variable loading with RALLY_ prefix
- Graceful fallback to MockRallyClient when not configured
- pyral entity mapping (HierarchicalRequirement → UserStory, etc.)
- Connection status indicator in StatusBar
- Default query: `(Iteration.Name = "current") AND (Owner.DisplayName = "user")`
- `current_user` property from `getUserInfo()` API
- `current_iteration` property from date-range query on Iteration entity

---

### Iteration 7: Search & Filtering ✅ COMPLETE

**Goal**: Filter ticket list with search input and real-time filtering

**Detailed Guide**: See [ITERATION_7.md](./ITERATION_7.md) for step-by-step implementation.

**Tasks**:
- [x] Create `SearchInput` widget (extends Input)
- [x] Add filter logic to `TicketList` (filter_tickets method)
- [x] Add filter info to `StatusBar` (Filtered: X/Y)
- [x] Add search context to `CommandBar`
- [x] Add `/` key binding to activate search
- [x] Add `Esc` to clear search and return to list
- [x] Add `Enter` to confirm search and focus list
- [x] Write tests for all new functionality
- [x] Update documentation

**Implementation Notes**:
- SearchInput uses Textual's Input widget with custom messages
- Filter is case-insensitive, searches formatted_id, name, owner, state
- TicketList maintains `_all_tickets` for unfiltered list
- StatusBar shows "Filtered: X/Y" when filter is active
- 161 total tests passing (134 from Iteration 6 + 27 new)

**Deliverable**: User can press `/` to search, type to filter in real-time, Esc to clear

**Test Coverage**:
- Unit: SearchInput widget messages (SearchChanged, SearchSubmitted, SearchCleared)
- Unit: TicketList.filter_tickets() with various queries
- Unit: TicketList case-insensitive matching
- Unit: TicketList.clear_filter() restores all tickets
- Unit: StatusBar.set_filter_info() and clear_filter_info()
- Unit: CommandBar search context
- Integration: App search activation and filtering
- Snapshot: Updated layouts with search input placement

**Key Files**:
```
src/rally_tui/widgets/
└── search_input.py     # New SearchInput widget

src/rally_tui/
├── app.py              # Search bindings and handlers
├── app.tcss            # Search input styling, list-container
└── widgets/
    ├── __init__.py     # Export SearchInput
    ├── ticket_list.py  # Add filter_tickets method
    ├── status_bar.py   # Add filter info display
    └── command_bar.py  # Add search context

tests/
├── test_search_input.py  # New tests (9 tests)
├── test_ticket_list.py   # Add filter tests (11 new)
├── test_status_bar.py    # Add filter info tests (5 new)
└── test_command_bar.py   # Add search context tests (2 new)
```

**Key Bindings**:
| Key | Context | Action |
|-----|---------|--------|
| `/` | list | Activate search input |
| `Esc` | search | Clear search, return to list |
| `Enter` | search | Confirm search, focus list |

**Key Concepts**:
- Vertical container to group TicketList and SearchInput
- Custom messages for widget communication (SearchChanged, SearchSubmitted, SearchCleared)
- Rich markup escaping (`\\[/\\]` for `/` key display)
- Conditional display with `display = False/True`

---

### Iteration 8: CRUD Operations

**Goal**: Create, edit, update tickets from TUI

**Tasks**:
- [ ] Edit mode for ticket details (e key)
- [ ] Form widgets for editable fields
- [ ] Save changes to Rally (Enter)
- [ ] Cancel edits (Esc)
- [ ] Create new ticket dialog (c key)
- [ ] Delete with confirmation (d key)
- [ ] Optimistic UI updates

**Deliverable**: Full CRUD operations from within TUI

**Test Coverage**:
- Snapshot: Edit mode appearance
- Snapshot: Create dialog
- Unit: Form validation
- Integration: Mock client receives correct update calls

---

### Future Iterations

- **Iteration 9**: Iteration/Release scoping and filtering
- **Iteration 10**: Bulk operations (multi-select with Space)
- **Iteration 11**: Attachment viewing/adding
- **Iteration 12**: Custom fields support
- **Iteration 13**: Caching and offline mode
- **Iteration 14**: Configurable keybindings

---

## Testing Strategy

### Test Types

| Type | Tool | Purpose |
|------|------|---------|
| Snapshot | pytest-textual-snapshot | Visual regression for UI |
| Unit | pytest | Widget logic, data transforms |
| Integration | pytest + mock client | Full app flows |
| E2E | Manual / pytest | Real Rally (sparingly) |

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rally_tui

# Update snapshots after intentional UI changes
pytest --snapshot-update

# Run only snapshot tests
pytest -k snapshot
```

### Snapshot Test Example

```python
# tests/test_ticket_list.py
import pytest
from rally_tui.app import RallyTUI
from rally_tui.services.mock_client import MockRallyClient

@pytest.fixture
def mock_tickets():
    return [
        Ticket("US1234", "User login feature", "UserStory", "In Progress", ...),
        Ticket("DE456", "Fix null pointer", "Defect", "Open", ...),
    ]

def test_ticket_list_initial_render(snap_compare, mock_tickets):
    client = MockRallyClient(tickets=mock_tickets)
    app = RallyTUI(client=client)
    assert snap_compare(app)

def test_ticket_list_navigation(snap_compare, mock_tickets):
    client = MockRallyClient(tickets=mock_tickets)
    app = RallyTUI(client=client)
    assert snap_compare(app, press=["j", "j"])  # Move down twice
```

---

## Dependencies

```toml
# pyproject.toml
[project]
name = "rally-tui"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "textual>=0.40.0",
    "pyral>=1.6.0",
    "pydantic-settings>=2.0.0",
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
rally = "rally_tui.app:main"
```

---

## Notes

- See `docs/API.md` for Rally WSAPI reference
- Textual docs: https://textual.textualize.io/
- pytest-textual-snapshot: https://github.com/Textualize/pytest-textual-snapshot
