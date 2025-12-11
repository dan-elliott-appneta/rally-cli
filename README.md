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
- **Theme toggle**: Switch between dark/light themes with `t` key (persisted)
- **Copy URL**: Press `y` to copy Rally ticket URL to clipboard
- **Set Points**: Press `p` to set story points on selected ticket
- **User settings**: Preferences saved to `~/.config/rally-tui/config.json`
- **Default filter**: When connected, shows only tickets in the current iteration owned by you
- **Discussions**: View ticket discussions and add comments

## Status

**Iteration 8+ Complete** - Discussions, Comments, and UI Polish.

- State indicators show workflow progress with colored symbols
- Tickets sorted by workflow state (earlier states at top)
- Theme preference persisted to user config file
- Copy ticket URL to clipboard with `y` key
- Set story points with `p` key
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
- 276 tests passing

Next: Iteration 9 (CRUD Operations).

See [docs/PLAN.md](docs/PLAN.md) for the full roadmap.

## Requirements

- Python 3.12+
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
| p | list/detail | Set story points |
| d | list/detail | Open discussions |
| c | discussion | Add comment |
| Ctrl+S | comment | Submit comment |
| q | any | Quit |

### User Settings

Settings are stored in `~/.config/rally-tui/config.json`:

```json
{
  "theme": "dark"
}
```

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
│   │   └── comment_screen.py     # CommentScreen
│   ├── widgets/
│   │   ├── ticket_list.py   # TicketList widget (left panel, state sorting)
│   │   ├── ticket_detail.py # TicketDetail widget (right panel)
│   │   ├── command_bar.py   # CommandBar widget (bottom)
│   │   ├── status_bar.py    # StatusBar widget (top)
│   │   └── search_input.py  # SearchInput widget (search mode)
│   ├── utils/               # Utility functions
│   │   └── html_to_text.py  # HTML to plain text converter
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
│   ├── test_command_bar.py       # CommandBar widget tests
│   ├── test_status_bar.py        # StatusBar widget tests
│   ├── test_search_input.py      # SearchInput widget tests
│   ├── test_services.py          # Service layer tests
│   ├── test_mock_client_discussions.py  # MockClient discussion tests
│   ├── test_config.py            # Configuration tests
│   ├── test_user_settings.py     # User settings tests
│   ├── test_rally_client.py      # RallyClient tests
│   ├── test_html_to_text.py      # HTML conversion tests
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
