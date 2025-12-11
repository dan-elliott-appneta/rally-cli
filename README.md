# Rally TUI

A terminal user interface (TUI) for browsing and managing Rally (Broadcom) work items.

## Features

- Browse Rally tickets in a navigable list
- View ticket details in a split-pane layout
- Keyboard-driven interface with vim-style navigation
- Color-coded ticket types (User Stories, Defects, Tasks, Test Cases)

## Status

**Iteration 4 Complete** - Layout polish and status bar.

- Two-panel layout with ticket list and detail view
- Status bar showing workspace/project info
- Panel titles ("Tickets", "Details")
- Tab to switch between panels
- Context-sensitive keyboard shortcuts displayed at bottom
- 73 tests passing

Next: Iteration 5 (Ticket Data Model & Mock Service).

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

```bash
# Run the TUI
rally-tui
```

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
│   ├── services/            # Rally API client (future)
│   └── screens/             # Application screens (future)
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_ticket_model.py  # Model unit tests
│   ├── test_ticket_list.py   # TicketList widget tests
│   ├── test_ticket_detail.py # TicketDetail widget tests
│   ├── test_command_bar.py   # CommandBar widget tests
│   ├── test_status_bar.py    # StatusBar widget tests
│   └── test_snapshots.py     # Visual regression tests
└── docs/
    ├── API.md               # Rally WSAPI reference
    ├── PLAN.md              # Development roadmap
    ├── ITERATION_1.md       # Iteration 1 guide (complete)
    ├── ITERATION_2.md       # Iteration 2 guide (complete)
    ├── ITERATION_3.md       # Iteration 3 guide (complete)
    └── ITERATION_4.md       # Iteration 4 guide (complete)
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

## Technology Stack

- **[Textual](https://textual.textualize.io/)** - Modern Python TUI framework
- **[pyral](https://pyral.readthedocs.io/)** - Rally REST API toolkit
- **[pytest-textual-snapshot](https://github.com/Textualize/pytest-textual-snapshot)** - Visual regression testing

## License

MIT
