# Rally TUI

A terminal user interface (TUI) for browsing and managing Rally (Broadcom) work items.

## Features

- Browse Rally tickets in a navigable list
- View ticket details in a split-pane layout
- Keyboard-driven interface with vim-style navigation
- Color-coded ticket types (User Stories, Defects, Tasks, Test Cases)

## Status

**Iteration 6 Complete** - Real Rally API integration.

- Connect to Rally API using pyral
- Environment variable configuration (RALLY_APIKEY, RALLY_WORKSPACE, etc.)
- Automatic fallback to offline mode with sample data
- Connection status indicator (Connected/Offline)
- Two-panel layout with ticket list and detail view
- Tab to switch between panels
- Context-sensitive keyboard shortcuts
- 134 tests passing

Next: Iteration 7 (Search & Filtering).

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

| Key | Action |
|-----|--------|
| j / ↓ | Move down |
| k / ↑ | Move up |
| g | Jump to top |
| G | Jump to bottom |
| Enter | Select item |
| Tab | Switch panel |
| q | Quit |

## Development

### Project Structure

```
rally-cli/
├── pyproject.toml           # Project config and dependencies
├── src/rally_tui/           # Main application code
│   ├── app.py               # Textual application entry point
│   ├── app.tcss             # CSS stylesheet
│   ├── models/
│   │   ├── ticket.py        # Ticket dataclass
│   │   └── sample_data.py   # Hardcoded test data
│   ├── widgets/
│   │   ├── ticket_list.py   # TicketList widget (left panel)
│   │   ├── ticket_detail.py # TicketDetail widget (right panel)
│   │   ├── command_bar.py   # CommandBar widget (bottom)
│   │   └── status_bar.py    # StatusBar widget (top)
│   ├── config.py            # Configuration (pydantic-settings)
│   └── services/            # Rally API client layer
│       ├── protocol.py      # RallyClientProtocol interface
│       ├── rally_client.py  # Real Rally API client
│       └── mock_client.py   # MockRallyClient for testing
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_ticket_model.py  # Model unit tests
│   ├── test_ticket_list.py   # TicketList widget tests
│   ├── test_ticket_detail.py # TicketDetail widget tests
│   ├── test_command_bar.py   # CommandBar widget tests
│   ├── test_status_bar.py    # StatusBar widget tests
│   ├── test_services.py      # Service layer tests
│   ├── test_config.py        # Configuration tests
│   ├── test_rally_client.py  # RallyClient tests
│   └── test_snapshots.py     # Visual regression tests
└── docs/
    ├── API.md               # Rally WSAPI reference
    ├── PLAN.md              # Development roadmap
    └── ITERATION_*.md       # Implementation guides (1-6)
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

## Technology Stack

- **[Textual](https://textual.textualize.io/)** - Modern Python TUI framework
- **[pyral](https://pyral.readthedocs.io/)** - Rally REST API toolkit
- **[pytest-textual-snapshot](https://github.com/Textualize/pytest-textual-snapshot)** - Visual regression testing

## License

MIT
