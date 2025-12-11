# Rally TUI

A terminal user interface (TUI) for browsing and managing Rally (Broadcom) work items.

## Features

- Browse Rally tickets in a navigable list
- View ticket details in a split-pane layout
- Keyboard-driven interface with vim-style navigation
- Color-coded ticket types (User Stories, Defects, Tasks, Test Cases)

## Status

**In Development** - Currently implementing Iteration 1 (project skeleton and static ticket list).

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
| q | Quit |

## Development

### Project Structure

```
rally-cli/
├── src/rally_tui/      # Main application code
│   ├── app.py          # Textual application
│   ├── models/         # Data models
│   ├── widgets/        # TUI widgets
│   ├── services/       # Rally API client
│   └── screens/        # Application screens
├── tests/              # Test suite
└── docs/               # Documentation
    ├── API.md          # Rally WSAPI reference
    ├── PLAN.md         # Development roadmap
    └── ITERATION_1.md  # Current iteration guide
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
- [ITERATION_1.md](docs/ITERATION_1.md) - Current iteration implementation guide

## Technology Stack

- **[Textual](https://textual.textualize.io/)** - Modern Python TUI framework
- **[pyral](https://pyral.readthedocs.io/)** - Rally REST API toolkit
- **[pytest-textual-snapshot](https://github.com/Textualize/pytest-textual-snapshot)** - Visual regression testing

## License

MIT
