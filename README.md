# Rally TUI

A terminal user interface (TUI) for browsing and managing Rally (Broadcom) work items.

## Features

- Browse Rally tickets in a navigable list
- View ticket details in a split-pane layout
- Keyboard-driven interface with vim-style navigation
- Color-coded ticket types (User Stories, Defects, Tasks, Test Cases)
- **State indicators**: Visual workflow state with symbols (`.` not started, `+` in progress, `-` done, `✓` accepted)
- **Sorted by workflow**: Tickets sorted by state progression (Ideas at top, Accepted at bottom)
- **Splash screen**: ASCII art "RALLY TUI" greeting on startup
- **Theme support**: Full Textual theme support (catppuccin, nord, dracula, etc.) via command palette, persisted between sessions
- **Copy URL**: Press `y` to copy Rally ticket URL to clipboard
- **Set Points**: Press `p` to set story points on selected ticket
- **Set State**: Press `s` to change ticket state (Defined, In Progress, Completed, etc.)
- **Quick Create**: Press `c` to create a new ticket (User Story or Defect)
- **Toggle Notes**: Press `n` to toggle between description and notes view
- **User settings**: Preferences saved to `~/.config/rally-tui/config.json`
- **File logging**: Logs to `~/.config/rally-tui/rally-tui.log` with configurable log level
- **Default filter**: When connected, shows only tickets in the current iteration owned by you
- **Discussions**: View ticket discussions and add comments

## Status

**Iteration 8+ Complete** - Discussions, Comments, and UI Polish.

- State indicators show workflow progress with colored symbols
- Tickets sorted by workflow state (earlier states at top)
- Theme preference persisted to user config file
- Copy ticket URL to clipboard with `y` key
- Set story points with `p` key
- Create tickets with `c` key (User Story or Defect, auto-assigns to you and current iteration)
- View ticket discussions with `d` key
- Add comments with `c` key from discussion screen
- HTML content converted to readable plain text
- Search/filter tickets with `/` key (vim-style)
- Real-time filtering as you type
- Case-insensitive search across ID, name, owner, state
- Filter count displayed in status bar (Filtered: X/Y)
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
- 320 tests passing

Next: Iteration 9 (CRUD Operations).

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
| w | list/detail | New workitem |
| c | discussion | Add comment |
| Ctrl+S | comment | Submit comment |
| q | any | Quit |

### User Settings

Settings are stored in `~/.config/rally-tui/config.json`:

```json
{
  "theme": "dark",
  "theme_name": "catppuccin-mocha",
  "log_level": "INFO"
}
```

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
│   │   └── sample_data.py   # Sample data for offline mode
│   ├── screens/
│   │   ├── splash_screen.py      # SplashScreen (startup)
│   │   ├── discussion_screen.py  # DiscussionScreen
│   │   ├── comment_screen.py     # CommentScreen
│   │   ├── points_screen.py      # PointsScreen (set story points)
│   │   ├── state_screen.py       # StateScreen (change ticket state)
│   │   └── quick_ticket_screen.py # QuickTicketScreen (create tickets)
│   ├── widgets/
│   │   ├── ticket_list.py   # TicketList widget (left panel, state sorting)
│   │   ├── ticket_detail.py # TicketDetail widget (right panel)
│   │   ├── status_bar.py    # StatusBar widget (rally-tui banner, project, status)
│   │   └── search_input.py  # SearchInput widget (search mode)
│   ├── utils/               # Utility functions
│   │   ├── html_to_text.py  # HTML to plain text converter
│   │   └── logging.py       # File-based logging configuration
│   └── services/            # Rally API client layer
│       ├── protocol.py      # RallyClientProtocol interface
│       ├── rally_client.py  # Real Rally API client
│       └── mock_client.py   # MockRallyClient for testing
├── tests/
│   ├── conftest.py               # Pytest fixtures
│   ├── test_ticket_model.py      # Model unit tests
│   ├── test_discussion_model.py  # Discussion model tests
│   ├── test_ticket_list.py       # TicketList widget tests
│   ├── test_ticket_detail.py     # TicketDetail widget tests
│   ├── test_splash_screen.py     # SplashScreen tests
│   ├── test_discussion_screen.py # DiscussionScreen tests
│   ├── test_comment_screen.py    # CommentScreen tests
│   ├── test_points_screen.py     # PointsScreen tests
│   ├── test_state_screen.py      # StateScreen tests
│   ├── test_quick_ticket_screen.py # QuickTicketScreen tests
│   ├── test_status_bar.py        # StatusBar widget tests
│   ├── test_search_input.py      # SearchInput widget tests
│   ├── test_services.py          # Service layer tests
│   ├── test_mock_client_discussions.py  # MockClient discussion tests
│   ├── test_config.py            # Configuration tests
│   ├── test_user_settings.py     # User settings tests
│   ├── test_rally_client.py      # RallyClient tests
│   ├── test_html_to_text.py      # HTML conversion tests
│   ├── test_logging.py           # Logging module tests
│   └── test_snapshots.py         # Visual regression tests
└── docs/
    ├── API.md               # Rally WSAPI reference
    ├── PLAN.md              # Development roadmap
    └── ITERATION_*.md       # Implementation guides (1-8)
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

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Documentation

- [API.md](docs/API.md) - Rally WSAPI Python developer guide
- [PLAN.md](docs/PLAN.md) - Development roadmap and architecture
- [ITERATION_1.md](docs/ITERATION_1.md) - Iteration 1 implementation guide (complete)
- [ITERATION_2.md](docs/ITERATION_2.md) - Iteration 2 implementation guide (complete)
- [ITERATION_3.md](docs/ITERATION_3.md) - Iteration 3 implementation guide (complete)
- [ITERATION_4.md](docs/ITERATION_4.md) - Iteration 4 implementation guide (complete)
- [ITERATION_5.md](docs/ITERATION_5.md) - Iteration 5 implementation guide (complete)
- [ITERATION_6.md](docs/ITERATION_6.md) - Iteration 6 implementation guide (complete)
- [ITERATION_8.md](docs/ITERATION_8.md) - Iteration 8 implementation guide (Discussions & Comments)

## Technology Stack

- **[Textual](https://textual.textualize.io/)** - Modern Python TUI framework
- **[pyral](https://pyral.readthedocs.io/)** - Rally REST API toolkit
- **[pytest-textual-snapshot](https://github.com/Textualize/pytest-textual-snapshot)** - Visual regression testing

## License

MIT
