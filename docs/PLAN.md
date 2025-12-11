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
├── src/
│   └── rally_tui/
│       ├── __init__.py
│       ├── app.py              # Main Textual application
│       ├── screens/
│       │   └── main.py         # Main screen with 3-panel layout
│       ├── widgets/
│       │   ├── __init__.py
│       │   ├── ticket_list.py  # Left panel - scrollable ticket list
│       │   ├── ticket_detail.py # Right panel - ticket details view
│       │   └── command_bar.py  # Bottom panel - context commands
│       ├── models/
│       │   ├── __init__.py
│       │   └── ticket.py       # Ticket data models (decoupled from pyral)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── rally_client.py # Rally API wrapper (injectable)
│       │   └── mock_client.py  # Mock client for testing
│       └── config.py           # Configuration management
├── tests/
│   ├── conftest.py             # Fixtures, mock Rally client
│   ├── test_ticket_list.py
│   ├── test_ticket_detail.py
│   ├── test_command_bar.py
│   ├── test_integration.py
│   └── snapshots/              # SVG snapshots for visual tests
└── docs/
    ├── API.md
    └── PLAN.md
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

### Iteration 2: Details Panel (Right Side)

**Goal**: Show ticket details when a ticket is selected in a two-panel layout

**Detailed Guide**: See [ITERATION_2.md](./ITERATION_2.md) for step-by-step implementation.

**Tasks**:
- [ ] Create `TicketDetail` widget (extends VerticalScroll)
- [ ] Add new fields to Ticket model (description, owner, iteration, points)
- [ ] Update sample data with all new fields
- [ ] Implement two-panel layout with Horizontal container
- [ ] Use reactive property for ticket updates (`watch_ticket`)
- [ ] Display ticket fields (ID, Name, Type, State, Owner, Iteration, Points, Description)
- [ ] Handle empty/null states ("Unassigned", "Unscheduled", "—" for no points)
- [ ] Update CSS for two-panel layout (35% / 1fr split)
- [ ] Write unit tests for TicketDetail widget (13 tests)
- [ ] Update snapshot tests for new layout (3 tests)

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

### Iteration 3: Command Bar (Bottom)

**Goal**: Context-sensitive command hints at bottom

**Tasks**:
- [ ] Create `CommandBar` widget
- [ ] Define command sets for different contexts
- [ ] Update commands based on focused widget
- [ ] Style as fixed footer

**Deliverable**: Bottom bar shows relevant commands, updates on focus change

**Test Coverage**:
- Snapshot: Command bar with list-context commands
- Snapshot: Command bar with detail-context commands
- Unit: Focus change updates command set

```python
# Context-aware command bar
class CommandBar(Static):
    CONTEXTS = {
        "list": "[j/k] Navigate  [Enter] Select  [/] Search  [c] Create",
        "detail": "[e] Edit  [Esc] Back  [Tab] Next field",
    }

    def set_context(self, context: str):
        self.update(self.CONTEXTS.get(context, ""))
```

---

### Iteration 4: Layout & Styling

**Goal**: Proper 3-panel layout with CSS styling

**Tasks**:
- [ ] Create main screen with CSS grid/dock layout
- [ ] Left panel: fixed width or percentage
- [ ] Right panel: flexible width
- [ ] Bottom bar: docked to bottom
- [ ] Add header bar with workspace/project info
- [ ] Color coding for ticket types
- [ ] Focus indicators (border highlight)

**Deliverable**: Polished layout matching the design mockup

**Test Coverage**:
- Snapshot: Full app layout at different terminal sizes
- Snapshot: Color coding for different ticket types

```css
/* rally_tui.tcss */
TicketList {
    width: 30%;
    min-width: 25;
    border: solid $primary;
}

TicketDetail {
    width: 70%;
    border: solid $secondary;
}

CommandBar {
    dock: bottom;
    height: 1;
    background: $surface;
}
```

---

### Iteration 5: Ticket Data Model & Mock Service

**Goal**: Clean data layer with testable mock

**Tasks**:
- [ ] Define `Ticket` dataclass with all needed fields
- [ ] Create `RallyClientProtocol` (abstract interface)
- [ ] Implement `MockRallyClient` with fixture data
- [ ] Wire mock client into app for testing
- [ ] Add factory fixtures for test data generation

**Deliverable**: App uses injectable client, tests use mock

**Test Coverage**:
- Unit: Mock client returns expected data
- Integration: App renders mock data correctly

```python
# models/ticket.py
@dataclass
class Ticket:
    formatted_id: str
    name: str
    type: Literal["UserStory", "Defect", "Task"]
    state: str
    owner: str | None
    description: str
    story_points: int | None
    iteration: str | None

# services/rally_client.py
class RallyClientProtocol(Protocol):
    def get_tickets(self, query: str | None = None) -> list[Ticket]: ...
    def get_ticket(self, formatted_id: str) -> Ticket | None: ...
```

---

### Iteration 6: Real Rally Integration

**Goal**: Connect to actual Rally API

**Tasks**:
- [ ] Implement `RallyClient` using pyral
- [ ] Configuration loading (API key, workspace, project)
- [ ] Map pyral responses to internal `Ticket` model
- [ ] Add loading states to widgets
- [ ] Handle API errors gracefully
- [ ] Add connection status indicator

**Deliverable**: App fetches and displays real Rally data

**Test Coverage**:
- Unit: pyral response → Ticket mapping
- Integration: Full flow with mock (no real API in tests)

```python
# services/rally_client.py
class RallyClient:
    def __init__(self, config: RallyConfig):
        self._rally = Rally(
            config.server,
            apikey=config.api_key,
            workspace=config.workspace,
            project=config.project
        )

    def get_tickets(self, query: str | None = None) -> list[Ticket]:
        response = self._rally.get('Artifact', fetch=True, query=query)
        return [self._to_ticket(item) for item in response]
```

---

### Iteration 7: Search & Filtering

**Goal**: Filter ticket list with search

**Tasks**:
- [ ] Add search input (activated with `/`)
- [ ] Filter list as user types
- [ ] Highlight matching text in list
- [ ] Clear search with Esc
- [ ] Persist last search

**Deliverable**: User can search/filter the ticket list

**Test Coverage**:
- Snapshot: Search input visible
- Snapshot: Filtered list results
- Unit: Filter logic correctness

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
