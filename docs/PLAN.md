# Rally CLI - Project Plan

## Overview

A Python TUI (Text User Interface) application for interacting with Rally (Broadcom) via the WSAPI. The interface features a two-panel layout: ticket list (left), ticket details (right), with a Footer showing keyboard shortcuts.

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
├── TESTING.md                  # Testing guide
├── src/
│   └── rally_tui/
│       ├── __init__.py
│       ├── app.py              # Main Textual application
│       ├── app.tcss            # CSS stylesheet
│       ├── config.py           # Configuration (pydantic-settings)
│       ├── user_settings.py    # User preferences (~/.config/rally-tui/)
│       ├── widgets/
│       │   ├── __init__.py
│       │   ├── ticket_list.py  # Left panel - state sorting, filtering
│       │   ├── ticket_detail.py # Right panel - ticket details view
│       │   ├── status_bar.py   # Top bar - workspace/project/status
│       │   └── search_input.py # Search input for filtering
│       ├── models/
│       │   ├── __init__.py
│       │   ├── ticket.py       # Ticket data models (decoupled from pyral)
│       │   ├── discussion.py   # Discussion dataclass
│       │   └── sample_data.py  # Sample tickets for offline mode
│       ├── screens/
│       │   ├── __init__.py
│       │   ├── splash_screen.py      # ASCII art startup screen
│       │   ├── discussion_screen.py  # Ticket discussions view
│       │   ├── comment_screen.py     # Add new comment
│       │   ├── points_screen.py      # Set story points
│       │   └── quick_ticket_screen.py # Quick ticket creation
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── html_to_text.py # HTML to plain text converter
│       │   └── logging.py      # File logging with rotation
│       └── services/
│           ├── __init__.py
│           ├── protocol.py     # RallyClientProtocol interface
│           ├── rally_client.py # Real Rally API client (pyral)
│           └── mock_client.py  # Mock client for testing/offline
├── tests/                      # 397 tests
│   ├── conftest.py             # Fixtures, mock Rally client
│   ├── test_ticket_model.py
│   ├── test_discussion_model.py
│   ├── test_ticket_list.py
│   ├── test_ticket_detail.py
│   ├── test_status_bar.py
│   ├── test_search_input.py
│   ├── test_splash_screen.py
│   ├── test_discussion_screen.py
│   ├── test_comment_screen.py
│   ├── test_points_screen.py
│   ├── test_state_screen.py
│   ├── test_quick_ticket_screen.py
│   ├── test_services.py
│   ├── test_mock_client_discussions.py
│   ├── test_config.py
│   ├── test_user_settings.py
│   ├── test_rally_client.py
│   ├── test_html_to_text.py
│   ├── test_logging.py
│   ├── test_snapshots.py
│   └── __snapshots__/          # SVG snapshots for visual tests
└── docs/
    ├── API.md                  # Rally WSAPI reference
    ├── PLAN.md                 # This file
    └── ITERATION_*.md          # Implementation guides (1-8)
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
- [x] Add HTML-to-text conversion for ticket descriptions

**Implementation Notes**:
- RallyConfig loads from RALLY_* environment variables
- RallyClient maps HierarchicalRequirement → UserStory, handles nested objects
- App falls back to MockRallyClient on connection failure
- **Default filter**: When connected, tickets are filtered to show only items in the current iteration owned by the API key's user
- RallyClient fetches current user via User entity query, current iteration via date-range query
- **HTML conversion**: Rally descriptions are HTML - converted to readable plain text for terminal display
- 200 total tests passing

**Deliverable**: App connects to Rally when configured, falls back to mock data when offline

**Test Coverage**:
- Unit: RallyConfig default values and environment loading
- Unit: Entity-to-Ticket mapping (all field types)
- Unit: Prefix-to-entity-type detection
- Unit: StatusBar connection status display
- Unit: Current user and iteration fetching
- Unit: Default query building (both, either, or neither user/iteration)
- Unit: HTML-to-text conversion (23 tests) - tags, entities, whitespace, Rally examples
- Integration: App with and without configuration

**Key Files**:
```
src/rally_tui/
├── config.py               # RallyConfig with pydantic-settings
├── services/
│   ├── rally_client.py     # Real Rally API client
│   └── __init__.py         # Export RallyClient
├── utils/
│   ├── __init__.py         # Export html_to_text
│   └── html_to_text.py     # HTML to plain text converter
├── widgets/
│   ├── status_bar.py       # Add connected parameter
│   └── ticket_detail.py    # Uses html_to_text for descriptions
└── app.py                  # Accept config, show status

tests/
├── test_rally_client.py    # Mapping and detection tests
├── test_config.py          # Configuration tests
└── test_html_to_text.py    # HTML conversion tests (23 tests)
```

**Key Concepts**:
- pydantic-settings for environment variable loading with RALLY_ prefix
- Graceful fallback to MockRallyClient when not configured
- pyral entity mapping (HierarchicalRequirement → UserStory, etc.)
- Connection status indicator in StatusBar
- Default query: `((Iteration.Name = "current") AND (Owner.DisplayName = "user"))`
- `current_user` property from User entity query (returns API key owner)
- `current_iteration` property from date-range query on Iteration entity
- HTML-to-text conversion using Python's built-in `html.parser` module

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

### Iteration 8: Discussions & Comments ✅ COMPLETE

**Goal**: View ticket discussions and add comments from TUI

**Detailed Guide**: See [ITERATION_8.md](./ITERATION_8.md) for step-by-step implementation.

**Tasks**:
- [x] Create `Discussion` model for conversation posts
- [x] Add `get_discussions(ticket)` and `add_comment()` to RallyClientProtocol
- [x] Implement Rally API calls for ConversationPost entities
- [x] Create `DiscussionScreen` (Textual Screen with scrollable comments)
- [x] Add `d` key binding to open discussions from ticket list/detail
- [x] Display comment author, timestamp, and text (HTML converted)
- [x] Create `CommentScreen` for adding new comments
- [x] Add `c` key binding in discussion view to compose comment
- [x] Implement `add_comment()` in RallyClient (creates ConversationPost)
- [x] Update MockRallyClient with discussion support
- [x] Add discussions and comment contexts to CommandBar
- [x] Write 39 tests for discussion functionality (10 model + 13 client + 16 screen)

**Implementation Notes**:
- DiscussionScreen uses Textual's Screen class for modal-like navigation
- Discussion model includes formatted_date and display_header properties
- HTML text converted to plain text using existing html_to_text utility
- 239 total tests passing

**Deliverable**: User can press `d` to view ticket discussions, `c` to add a comment

**UI Layout**:
```
┌─────────────────────────────────────────────────────────────────────┐
│  Rally TUI - Workspace: MyWorkspace | Project: MyProject           │
├─────────────────────────────────────────────────────────────────────┤
│  DISCUSSIONS - US1234                                               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ John Smith • 2024-01-15 10:30 AM                            │   │
│  │ I've started working on the login form. Will have a PR      │   │
│  │ ready by end of day.                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Jane Doe • 2024-01-15 2:45 PM                               │   │
│  │ Looks good! Don't forget to add input validation.           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  [c] Add Comment  [Esc] Back to Details  [q] Quit                   │
└─────────────────────────────────────────────────────────────────────┘
```

**Test Coverage**:
- Unit: Discussion model properties
- Unit: DiscussionView renders comments correctly
- Unit: CommentInput message handling
- Unit: RallyClient.get_discussions() mapping
- Unit: RallyClient.add_comment() API call
- Integration: Navigation to discussions and back
- Snapshot: Discussion view with multiple comments
- Snapshot: Comment input dialog

**Key Files**:
```
src/rally_tui/
├── models/
│   ├── discussion.py       # Discussion dataclass
│   └── sample_data.py      # SAMPLE_DISCUSSIONS for offline mode
├── screens/
│   ├── discussion_screen.py  # DiscussionScreen + DiscussionItem
│   └── comment_screen.py     # CommentScreen with TextArea
├── services/
│   ├── protocol.py         # Add get_discussions, add_comment
│   ├── rally_client.py     # Implement discussion API calls
│   └── mock_client.py      # Mock discussion data
└── widgets/
    └── command_bar.py      # Add discussion/comment contexts

tests/
├── test_discussion_model.py     # 10 tests
├── test_mock_client_discussions.py  # 13 tests
├── test_discussion_screen.py    # 8 tests
└── test_comment_screen.py       # 8 tests
```

**Key Bindings**:
| Key | Context | Action |
|-----|---------|--------|
| `d` | list/detail | Open discussions for selected ticket |
| `c` | discussion | Open comment input |
| `Ctrl+S` | comment | Submit comment |
| `Esc` | discussion/comment | Return to previous view |

**Key Concepts**:
- Rally ConversationPost entity for discussions
- Textual Screen class for modal-like discussion view
- HTML-to-text conversion for comment bodies using existing utility
- Timestamp formatting with strftime ("%b %d, %Y %I:%M %p")
- Automatic refresh after posting comment
- Discussion model with formatted_date and display_header properties

---

### Iteration 8+: UI Polish & Additional Features ✅ COMPLETE

**Goal**: Additional features for improved UX - splash screen, themes, logging, quick actions

**Tasks**:
- [x] Create `SplashScreen` with ASCII art "RALLY TUI" on startup
- [x] Add state-based ticket sorting (Ideas at top, Accepted at bottom)
- [x] Add state indicators with colored symbols (`.` not started, `+` in progress, `-` done, `✓` accepted)
- [x] Full Textual theme support (catppuccin, nord, dracula, etc.) via command palette
- [x] Create `UserSettings` for persistent preferences (~/.config/rally-tui/config.json)
- [x] Theme persistence between sessions (stores full theme_name like "catppuccin-mocha")
- [x] Add `y` key binding to copy Rally ticket URL to clipboard
- [x] Add notes field to Ticket model with toggle (`n` key) between description/notes
- [x] Create `PointsScreen` for setting story points (`p` key)
- [x] Implement `update_points()` in RallyClient and MockRallyClient
- [x] Add file-based logging with rotation (~/.config/rally-tui/rally-tui.log)
- [x] Configurable log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) in user settings
- [x] Create `QuickTicketScreen` for rapid ticket creation (`c` key)
- [x] Implement `create_ticket()` in RallyClient and MockRallyClient
- [x] Auto-assign current iteration and current user to new tickets
- [x] Fix Rich MarkupError by escaping special characters in descriptions
- [x] Create `StateScreen` for changing ticket state (`s` key)
- [x] Implement `update_state()` in RallyClient and MockRallyClient
- [x] Write tests for all new functionality

**Implementation Notes**:
- SplashScreen auto-dismisses on any keypress
- State sorting uses STATE_ORDER dict for workflow ordering
- UserSettings uses Pydantic for JSON serialization
- Logging uses Python's logging module with RotatingFileHandler
- QuickTicketScreen prompts for title, type (User Story/Defect), and description
- 321 total tests passing

**Deliverable**: Polished TUI with splash, themes, logging, URL copy, points setting, quick ticket creation

**Key Files**:
```
src/rally_tui/
├── user_settings.py           # UserSettings class for persistent prefs
├── screens/
│   ├── splash_screen.py       # ASCII art startup screen
│   ├── points_screen.py       # Story points input screen
│   └── quick_ticket_screen.py # Quick ticket creation screen
├── widgets/
│   └── ticket_list.py         # State sorting, STATE_ORDER, symbols, colors
├── utils/
│   └── logging.py             # File-based logging setup
└── services/
    ├── protocol.py            # Add update_points, create_ticket
    ├── rally_client.py        # Implement update_points, create_ticket
    └── mock_client.py         # Mock implementations

tests/
├── test_splash_screen.py      # Splash screen tests
├── test_points_screen.py      # Points screen tests
├── test_quick_ticket_screen.py # Quick ticket screen tests (16 tests)
├── test_user_settings.py      # User settings tests
└── test_logging.py            # Logging module tests
```

**Key Bindings**:
| Key | Context | Action |
|-----|---------|--------|
| `t` | any | Toggle dark/light theme |
| `y` | list/detail | Copy Rally ticket URL to clipboard |
| `p` | list/detail | Set story points for selected ticket |
| `n` | list/detail | Toggle description/notes view |
| `s` | list/detail | Change ticket state |
| `w` | list/detail | Create new ticket (User Story or Defect) |

**Key Concepts**:
- Textual theme system with `self.theme` property and `watch_theme` watcher
- UserSettings persists theme_name for full theme restoration
- STATE_ORDER dict for workflow-based sorting
- Ticket.rally_url() method constructs Rally detail URLs
- RotatingFileHandler for log rotation (5MB max, 3 backups)
- QuickTicketData dataclass for form result passing

---

### Iteration 9: Configurable Keybindings

**Goal**: Allow users to customize keyboard shortcuts

**Tasks**:
- [ ] Create keybindings schema in UserSettings
- [ ] Load custom keybindings from config file
- [ ] KeybindingsScreen for viewing/editing bindings
- [ ] Default bindings with override support
- [ ] Vim/Emacs preset profiles

**Deliverable**: Users can customize keyboard shortcuts via config or UI

**Test Coverage**:
- Unit: Keybinding loading and defaults
- Unit: Override precedence
- Integration: Custom bindings work in app

---

### Iteration 10: Iteration & User Filtering + Sorting ✅ COMPLETE

**Goal**: Navigate between iterations, toggle user filter, and sort ticket list

**Detailed Guide**: See [ITERATION_10.md](./ITERATION_10.md) for step-by-step implementation.

**Tasks**:
- [x] Create `Iteration` model with name, dates, is_current, short_name
- [x] Add `get_iterations()` method to RallyClientProtocol
- [x] Create `IterationScreen` modal for iteration selection
- [x] Add `i` key binding to open iteration picker
- [x] Add `u` key binding to toggle My/All tickets filter
- [x] Update StatusBar to show current iteration and user filter
- [x] Add Backlog view (unscheduled items) via `b` key in IterationScreen
- [x] Update MockRallyClient with sample iterations
- [x] Add `SortMode` enum with STATE, CREATED, OWNER options
- [x] Add `o` key binding to cycle through sort modes
- [x] Update StatusBar to show current sort mode
- [x] Add sorting functions for each mode
- [x] Write tests for all new functionality (85+ new tests)

**Implementation Notes**:
- IterationScreen shows recent iterations with number key shortcuts (1-5)
- Special options: 0 for All, b for Backlog
- Status bar displays "Sprint: X" and "My Items" when filters active
- Combined filters work together (e.g., "My backlog items")
- Current sprint always appears as button 1 in iteration picker
- **Sorting**: Three sort modes cycle via 'o' key:
  - **State Flow**: Defined → In Progress → Completed (default)
  - **Recently Created**: Newest tickets first (by FormattedID)
  - **Owner**: Unassigned first, then alphabetical by owner name
- StatusBar shows "Sort: Recent" or "Sort: Owner" when not default
- 397 total tests passing

**Deliverable**: User can switch iterations, toggle between My/All tickets, view backlog, sort tickets

**Key Bindings**:
| Key | Action |
|-----|--------|
| `i` | Open iteration picker |
| `u` | Toggle My/All tickets |
| `o` | Cycle sort mode (State → Recent → Owner) |
| `0` | Show all iterations (in picker) |
| `b` | Show backlog only (in picker) |

**Key Files**:
```
src/rally_tui/
├── models/
│   └── iteration.py         # Iteration dataclass
├── screens/
│   └── iteration_screen.py  # IterationScreen modal
├── widgets/
│   └── status_bar.py        # Add filter display methods
├── services/
│   ├── protocol.py          # Add get_iterations()
│   └── mock_client.py       # Sample iteration generation
└── app.py                   # Filter state and key bindings

tests/
├── test_iteration_model.py      # 13 tests
├── test_iteration_screen.py     # 23 tests
├── test_filter_integration.py   # 11 tests
├── test_services.py             # 7 new iteration tests
└── test_status_bar.py           # 13 new filter tests
```

**Test Coverage**:
- Unit: Iteration model (is_current, formatted_dates, short_name)
- Unit: IterationScreen selection and highlighting
- Unit: StatusBar filter display
- Integration: Filter state management
- Integration: Combined filters
- Snapshot: Updated footer with new bindings

---

### Iteration 11: Parent Selection Feature

**Goal**: Require parent Feature assignment when moving tickets to "In Progress" state

**Tasks**:
- [ ] Add `parent_id` field to Ticket model
- [ ] Add `parent_options` property to UserSettings (default: F59625, F59627, F59628)
- [ ] Add `get_feature()` and `set_parent()` methods to RallyClientProtocol
- [ ] Implement `get_feature()` and `set_parent()` in RallyClient
- [ ] Implement `get_feature()` and `set_parent()` in MockRallyClient
- [ ] Create `ParentScreen` modal for parent selection
- [ ] Modify `_handle_state_result()` to intercept "In Progress" transitions
- [ ] Update `_to_ticket()` to include parent_id from PortfolioItem
- [ ] Write comprehensive tests
- [ ] Update documentation
- [ ] Bump version to 0.3.0

**Implementation Notes**:
- **Parent Options**: User-configurable list of 3 Feature IDs stored in `~/.config/rally-tui/config.json`
- **ParentScreen UI**: Shows 3 configured parents with truncated titles (40 chars max) + 4th option for custom ID
- **Rally API**: Features are `PortfolioItem/Feature` entities; User Stories have `PortfolioItem` field
- **Flow**: When selecting "In Progress" and ticket has no parent, ParentScreen appears before state change
- **Number Keys**: 1-3 for configured parents, 4 for custom input, Esc to cancel

**UI Layout**:
```
┌─────────────────────────────────────────────┐
│ Select Parent Feature - US1234              │
├─────────────────────────────────────────────┤
│ Ticket must have a parent before moving     │
│ to In Progress.                             │
│                                             │
│ [1. F59625 - Feature Title Trunc...]        │
│ [2. F59627 - Another Feature Ti...]         │
│ [3. F59628 - Third Feature Name...]         │
│ [4. Enter custom ID...]                     │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ (Input field for custom ID)             │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Press 1-4 or click button, ESC to cancel    │
└─────────────────────────────────────────────┘
```

**Key Files**:
```
src/rally_tui/
├── models/
│   └── ticket.py           # Add parent_id field
├── user_settings.py        # Add parent_options property
├── screens/
│   ├── __init__.py         # Export ParentScreen
│   └── parent_screen.py    # New ParentScreen modal
├── services/
│   ├── protocol.py         # Add get_feature, set_parent
│   ├── rally_client.py     # Implement get_feature, set_parent
│   └── mock_client.py      # Mock implementations
└── app.py                  # Modify _handle_state_result

tests/
├── test_ticket_model.py      # Add parent_id tests
├── test_user_settings.py     # Add parent_options tests
├── test_parent_screen.py     # New test file
├── test_services.py          # Add get_feature/set_parent tests
└── test_app.py               # Add parent selection flow tests
```

**Test Coverage**:
- Unit: Ticket model with parent_id field
- Unit: UserSettings parent_options get/set/default
- Unit: ParentScreen renders 4 options
- Unit: ParentScreen number key bindings (1-4)
- Unit: ParentScreen custom input mode
- Unit: get_feature() returns (id, name) tuple
- Unit: set_parent() updates ticket parent
- Integration: State change to "In Progress" shows ParentScreen
- Integration: State change skips ParentScreen when has parent
- Integration: Full flow: parent selection → state change

**Commit Plan**:
1. `feat: add parent_id field to Ticket model`
2. `feat: add parent_options to UserSettings`
3. `feat: add get_feature and set_parent to protocol`
4. `feat: implement get_feature and set_parent in clients`
5. `feat: create ParentScreen modal`
6. `feat: require parent when moving to In Progress`
7. `test: add comprehensive tests for parent selection`
8. `docs: update README with parent selection feature`
9. `chore: bump version to 0.3.0`

---

### Future Iterations

- **Iteration 12**: Bulk operations (multi-select with Space)
- **Iteration 13**: Attachment viewing/adding
- **Iteration 14**: Custom fields support
- **Iteration 15**: Caching and offline mode
- **Iteration 16**: CRUD Operations (edit tickets, delete with confirmation)

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
requires-python = ">=3.11"
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
