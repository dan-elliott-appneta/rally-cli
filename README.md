# Rally TUI

A terminal user interface (TUI) for browsing and managing Rally (Broadcom) work items.

## Features

- Browse Rally tickets in a navigable list
- View ticket details in a split-pane layout
- Keyboard-driven interface with vim-style navigation
- Color-coded ticket types (User Stories, Defects, Tasks, Test Cases)
- **State indicators**: Visual workflow state with symbols (`.` not started, `+` in progress, `-` done, `✓` accepted)
- **Sorting options**: Sort by most recent (default), state flow, owner, or parent (press `o` to cycle)
- **Splash screen**: ASCII art "RALLY TUI" greeting on startup
- **Theme support**: Full Textual theme support (catppuccin, nord, dracula, etc.) via command palette, persisted between sessions
- **Copy URL**: Press `y` to copy Rally ticket URL to clipboard
- **Set Points**: Press `p` to set story points on selected ticket
- **Set State**: Press `s` to change ticket state (Defined, In Progress, Completed, etc.)
- **Parent Requirement**: Must select a parent Feature before moving to "In Progress" state
- **Quick Create**: Press `w` to create a new workitem (User Story or Defect)
- **Toggle Notes**: Press `n` to toggle between description and notes view
- **Sprint Filter**: Press `i` to filter tickets by iteration/sprint
- **My Items Filter**: Press `u` to toggle showing only your tickets
- **Team Breakdown**: Press `b` to view ticket count and points breakdown by owner for a sprint
- **Wide View**: Press `v` to toggle wide view mode showing owner, points, and parent columns
- **User settings**: Preferences saved to `~/.config/rally-tui/config.json`
- **Settings UI**: Press `F2` to open settings screen and configure theme, log level, and parent options
- **Keybindings UI**: Press `F3` to view/edit keyboard shortcuts with Vim and Emacs presets
- **File logging**: Logs to `~/.config/rally-tui/rally-tui.log` with configurable log level
- **Default filter**: When connected, shows only tickets in the current iteration owned by you
- **Discussions**: View ticket discussions and add comments
- **Attachments**: Press `a` to view, download, or upload ticket attachments (includes embedded images from description/notes)
- **Local caching**: Tickets cached to `~/.cache/rally-tui/` for performance and offline access
- **Cache refresh**: Press `r` to manually refresh the ticket cache
- **Loading indicator**: Visual feedback in status bar when fetching tickets from API
- **Async API client**: High-performance httpx-based async Rally client with concurrent operations
- **Project scoping**: All queries are automatically scoped to your project to prevent cross-project data leakage
- **CI pipeline**: GitHub Actions workflow with tests, linting, type checking, and coverage reports

## Status

**Iteration 14 Complete** - Local Caching + Async API Integration.

- **NEW**: Vim motions (j/k/g/G) work on all screens (discussions, attachments, iteration picker, state picker, bulk actions)
- **NEW**: Press `F3` to open keybindings configuration screen
- **NEW**: Vim and Emacs keybinding profiles
- **NEW**: Custom keybinding overrides
- **NEW**: Click rows to edit individual bindings
- **NEW**: Conflict detection for duplicate key assignments
- **NEW**: Profile selector (Vim, Emacs, Custom)
- **NEW**: Reset button to restore defaults
- Multi-select tickets with `Space` key (toggle selection)
- Select all tickets with `Ctrl+A` (toggle select all/deselect all)
- Press `m` to open bulk actions menu on selected tickets
- Bulk operations: Set Parent, Set State, Set Iteration, Set Points, Yank (copy URLs)
- Press `F2` to open ConfigScreen for editing settings
- Configure theme, log level, and parent options from the TUI
- Settings saved immediately with Ctrl+S or Save button
- Ticket must have a parent Feature before moving to "In Progress" state
- ParentScreen modal for selecting parent (3 configurable options + custom ID entry)
- Configurable parent options via `~/.config/rally-tui/config.json`
- Filter by iteration/sprint with `i` key
- Toggle "My Items" filter with `u` key to show only your tickets
- Filter to Backlog (unscheduled items) from iteration picker
- Status bar shows active filters (Sprint: X, My Items)
- State indicators show workflow progress with colored symbols
- Sort by most recent (default), state flow, owner, or parent
- Theme preference persisted to user config file
- Copy ticket URL to clipboard with `y` key
- Set story points with `p` key
- Create tickets with `w` key (User Story or Defect, auto-assigns to you and current iteration)
- View ticket discussions with `d` key
- Add comments with `c` key from discussion screen
- HTML content converted to readable plain text
- Search/filter tickets with `/` key (vim-style)
- Real-time filtering as you type
- Case-insensitive search across ID, name, owner, state
- Search query and filter count displayed in status bar (Search: query X/Y)
- Escape clears filter, Enter confirms and returns to list
- Connect to Rally API using pyral
- Environment variable configuration (RALLY_APIKEY, RALLY_WORKSPACE, etc.)
- Automatic fallback to offline mode with sample data
- Connection status indicator (Connected as {username}/Offline)
- Two-panel layout with ticket list and detail view
- Tab to switch between panels
- Context-sensitive keyboard shortcuts
- Default filter to current iteration and current user when connected
- Toggle between description and notes with `n` key
- File-based logging with configurable log level
- 864 tests passing (including 74 async tests)

Next: Iteration 15 (Custom fields support).

See [docs/PLAN.md](docs/PLAN.md) for the full roadmap.

## Requirements

- Python 3.11+
- A modern terminal with color support

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd rally-cli

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Usage

### Check Version

```bash
rally-tui --version
# Output: rally-tui 0.7.9
```

### Running with Rally API

```bash
# Set environment variables
export RALLY_APIKEY=your_api_key_here
export RALLY_WORKSPACE="Your Workspace"
export RALLY_PROJECT="Your Project"

# Run the TUI
rally-tui
```

### Running in Offline Mode

```bash
# Without RALLY_APIKEY, the app runs with sample data
rally-tui
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RALLY_SERVER` | Rally server hostname | `rally1.rallydev.com` |
| `RALLY_APIKEY` | Rally API key (required for API access) | (none) |
| `RALLY_WORKSPACE` | Workspace name | (from API) |
| `RALLY_PROJECT` | Project name | (from API) |

### Keyboard Navigation

| Key | Context | Action |
|-----|---------|--------|
| Ctrl+P | any | Open command palette |
| j / ↓ | list | Move down |
| k / ↑ | list | Move up |
| g | list | Jump to top |
| G | list | Jump to bottom |
| Space | list | Toggle selection on current ticket |
| Ctrl+A | list | Select all / Deselect all tickets |
| m | list | Open bulk actions menu |
| / | list | Search/filter tickets |
| Enter | list/search | Select item (or confirm search) |
| Esc | any | Clear filter / Go back |
| Tab | list/detail | Switch panel |
| t | any | Toggle dark/light theme |
| y | list/detail | Copy ticket URL to clipboard |
| s | list/detail | Set ticket state |
| p | list/detail | Set story points |
| n | list/detail | Toggle description/notes |
| d | list/detail | Open discussions |
| a | list/detail | View/download/upload attachments |
| i | list/detail | Filter by iteration/sprint |
| u | list/detail | Toggle My Items filter |
| o | list | Cycle sort mode (Recent/State/Owner/Parent) |
| b | list | Team breakdown (requires sprint filter) |
| v | list | Toggle wide view mode |
| r | list/detail | Refresh ticket cache |
| w | list/detail | New workitem |
| F2 | any | Open settings |
| F3 | any | Open keybindings |
| c | discussion | Add comment |
| Ctrl+S | comment/settings | Submit/Save |
| q | any | Quit |

### User Settings

Settings are stored in `~/.config/rally-tui/config.json`:

```json
{
  "theme": "dark",
  "theme_name": "catppuccin-mocha",
  "log_level": "INFO",
  "parent_options": ["F12345", "F12346", "F12347"],
  "keybinding_profile": "vim",
  "keybindings": {
    "navigation.down": "j",
    "navigation.up": "k"
  },
  "cache_enabled": true,
  "cache_ttl_minutes": 5,
  "cache_auto_refresh": true
}
```

**Important**: The `parent_options` array must be configured with valid Feature IDs from your Rally workspace. These are shown when selecting a parent for a ticket before moving to "In Progress" state. If not configured, you can still enter a custom Feature ID manually.

**Keybinding Profiles**: `vim` (default), `emacs`, or `custom`. Press F3 to view and edit keybindings.
- Vim profile: j/k navigation, g/G jump, / search
- Emacs profile: Ctrl+n/Ctrl+p navigation, Ctrl+a/Ctrl+e jump

**Cache Settings**:
- `cache_enabled`: Enable/disable local caching (default: true)
- `cache_ttl_minutes`: Cache time-to-live in minutes (default: 5)
- `cache_auto_refresh`: Automatically refresh stale cache in background (default: true)

Cache files are stored in `~/.cache/rally-tui/` and are automatically refreshed when stale. Press `r` to manually refresh.

Available themes: `textual-dark`, `textual-light`, `catppuccin-mocha`, `catppuccin-latte`, `nord`, `gruvbox`, `dracula`, `tokyo-night`, `monokai`, `flexoki`, `solarized-light`

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

Logs are written to `~/.config/rally-tui/rally-tui.log` with automatic rotation (5MB max, 3 backups).

## Development

### Project Structure

```
rally-cli/
├── pyproject.toml           # Project config and dependencies
├── src/rally_tui/           # Main application code
│   ├── app.py               # Textual application entry point
│   ├── app.tcss             # CSS stylesheet
│   ├── config.py            # Rally API config (pydantic-settings)
│   ├── user_settings.py     # User preferences (~/.config/rally-tui/)
│   ├── models/
│   │   ├── ticket.py        # Ticket dataclass
│   │   ├── discussion.py    # Discussion dataclass
│   │   ├── iteration.py     # Iteration dataclass
│   │   ├── attachment.py    # Attachment dataclass
│   │   └── sample_data.py   # Sample data for offline mode
│   ├── screens/
│   │   ├── splash_screen.py      # SplashScreen (startup)
│   │   ├── discussion_screen.py  # DiscussionScreen
│   │   ├── comment_screen.py     # CommentScreen
│   │   ├── points_screen.py      # PointsScreen (set story points)
│   │   ├── state_screen.py       # StateScreen (change ticket state)
│   │   ├── iteration_screen.py   # IterationScreen (filter by sprint)
│   │   ├── parent_screen.py      # ParentScreen (select parent Feature)
│   │   ├── config_screen.py      # ConfigScreen (edit settings)
│   │   ├── keybindings_screen.py # KeybindingsScreen (edit shortcuts)
│   │   ├── bulk_actions_screen.py # BulkActionsScreen (multi-select operations)
│   │   ├── quick_ticket_screen.py # QuickTicketScreen (create tickets)
│   │   └── attachments_screen.py  # AttachmentsScreen (view/download/upload)
│   ├── widgets/
│   │   ├── ticket_list.py   # TicketList widget (left panel, state sorting)
│   │   ├── ticket_detail.py # TicketDetail widget (right panel)
│   │   ├── status_bar.py    # StatusBar widget (rally-tui banner, project, status)
│   │   └── search_input.py  # SearchInput widget (search mode)
│   ├── utils/               # Utility functions
│   │   ├── html_to_text.py  # HTML to plain text converter
│   │   ├── logging.py       # File-based logging configuration
│   │   └── keybindings.py   # Keybinding profiles and utilities
│   └── services/            # Rally API client layer
│       ├── protocol.py      # RallyClientProtocol interface
│       ├── rally_client.py  # Real Rally API client (sync, pyral)
│       ├── async_rally_client.py  # Async Rally API client (httpx)
│       ├── rally_api.py     # Rally WSAPI constants and helpers
│       ├── mock_client.py   # MockRallyClient for testing
│       ├── async_mock_client.py   # AsyncMockRallyClient for testing
│       ├── cache_manager.py # Local file caching for tickets
│       ├── caching_client.py      # CachingRallyClient wrapper (sync)
│       └── async_caching_client.py # AsyncCachingRallyClient wrapper
├── tests/
│   ├── conftest.py               # Pytest fixtures
│   ├── test_ticket_model.py      # Model unit tests
│   ├── test_discussion_model.py  # Discussion model tests
│   ├── test_iteration_model.py   # Iteration model tests
│   ├── test_ticket_list.py       # TicketList widget tests
│   ├── test_ticket_detail.py     # TicketDetail widget tests
│   ├── test_splash_screen.py     # SplashScreen tests
│   ├── test_discussion_screen.py # DiscussionScreen tests
│   ├── test_comment_screen.py    # CommentScreen tests
│   ├── test_points_screen.py     # PointsScreen tests
│   ├── test_state_screen.py      # StateScreen tests
│   ├── test_iteration_screen.py  # IterationScreen tests
│   ├── test_parent_screen.py     # ParentScreen tests
│   ├── test_config_screen.py     # ConfigScreen tests
│   ├── test_bulk_actions_screen.py # BulkActionsScreen tests
│   ├── test_quick_ticket_screen.py # QuickTicketScreen tests
│   ├── test_attachments_screen.py  # AttachmentsScreen tests
│   ├── test_attachment_model.py    # Attachment model tests
│   ├── test_filter_integration.py # Filter integration tests
│   ├── test_status_bar.py        # StatusBar widget tests
│   ├── test_search_input.py      # SearchInput widget tests
│   ├── test_services.py          # Service layer tests
│   ├── test_mock_client_discussions.py  # MockClient discussion tests
│   ├── test_config.py            # Configuration tests
│   ├── test_user_settings.py     # User settings tests
│   ├── test_rally_client.py      # RallyClient tests
│   ├── test_html_to_text.py      # HTML conversion tests
│   ├── test_logging.py           # Logging module tests
│   ├── test_keybindings.py       # Keybinding utilities tests
│   ├── test_keybindings_screen.py # KeybindingsScreen tests
│   ├── test_cache_manager.py     # CacheManager tests
│   ├── test_caching_client.py    # CachingRallyClient tests
│   ├── test_rally_api.py         # Rally API helpers tests
│   ├── test_async_mock_client.py # AsyncMockRallyClient tests
│   ├── test_app_async_integration.py # App async integration tests
│   └── test_snapshots.py         # Visual regression tests
└── docs/
    ├── API.md               # Rally WSAPI reference
    ├── PLAN.md              # Development roadmap
    └── ITERATION_*.md       # Implementation guides (1-14)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rally_tui

# Update snapshot baselines
pytest --snapshot-update
```

### Continuous Integration

The project uses GitHub Actions for CI. On every PR:
- **Tests**: Run across Python 3.11, 3.12, 3.13
- **Lint**: Ruff check and format verification
- **Type Check**: Mypy static type analysis
- **Coverage**: Reports uploaded to Codecov

All checks must pass before merging.

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Documentation

- [USER.md](docs/USER.md) - **User Manual** - Complete guide to using Rally TUI
- [API.md](docs/API.md) - Rally WSAPI Python developer guide
- [PLAN.md](docs/PLAN.md) - Development roadmap and architecture
- [ITERATION_1.md](docs/ITERATION_1.md) - Iteration 1 implementation guide (complete)
- [ITERATION_2.md](docs/ITERATION_2.md) - Iteration 2 implementation guide (complete)
- [ITERATION_3.md](docs/ITERATION_3.md) - Iteration 3 implementation guide (complete)
- [ITERATION_4.md](docs/ITERATION_4.md) - Iteration 4 implementation guide (complete)
- [ITERATION_5.md](docs/ITERATION_5.md) - Iteration 5 implementation guide (complete)
- [ITERATION_6.md](docs/ITERATION_6.md) - Iteration 6 implementation guide (complete)
- [ITERATION_8.md](docs/ITERATION_8.md) - Iteration 8 implementation guide (Discussions & Comments)
- [ITERATION_9.md](docs/ITERATION_9.md) - Iteration 9 implementation guide (Configurable Keybindings)
- [ITERATION_10.md](docs/ITERATION_10.md) - Iteration 10 implementation guide (Iteration & User Filtering)
- [ITERATION_12.md](docs/ITERATION_12.md) - Iteration 12 implementation guide (Bulk Operations)
- [ITERATION_13.md](docs/ITERATION_13.md) - Iteration 13 implementation guide (Attachments)
- [ITERATION_14.md](docs/ITERATION_14.md) - Iteration 14 implementation guide (Local Caching)

## Technology Stack

- **[Textual](https://textual.textualize.io/)** - Modern Python TUI framework
- **[pyral](https://pyral.readthedocs.io/)** - Rally REST API toolkit (sync)
- **[httpx](https://www.python-httpx.org/)** - Async HTTP client for Rally API
- **[tenacity](https://tenacity.readthedocs.io/)** - Retry logic for API calls
- **[pytest-textual-snapshot](https://github.com/Textualize/pytest-textual-snapshot)** - Visual regression testing

## Versioning

This project uses [Semantic Versioning](https://semver.org/):
- Version is defined in `pyproject.toml`
- Accessible as `rally_tui.__version__` in code
- Displayed with `rally-tui --version`
- Shown on splash screen at startup

Version format: `MAJOR.MINOR.PATCH`
- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## License

MIT
