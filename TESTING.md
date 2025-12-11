# Testing Guide

This document describes the testing strategy and practices for Rally TUI.

## Overview

Rally TUI uses a multi-layered testing approach:

| Test Type | Tool | Purpose |
|-----------|------|---------|
| Unit | pytest | Test individual functions and classes |
| Widget | pytest + Textual Pilot | Test widget behavior in isolation |
| Snapshot | pytest-textual-snapshot | Visual regression testing |
| Integration | pytest + mock client | Test full application flows |

## Quick Start

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_ticket_model.py

# Run tests matching a pattern
pytest -k "navigation"
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures (sample_tickets, single_ticket)
├── test_ticket_model.py           # Unit tests for Ticket dataclass
├── test_discussion_model.py       # Unit tests for Discussion dataclass
├── test_ticket_list.py            # Widget tests for TicketList (state sorting, filtering)
├── test_ticket_detail.py          # Widget tests for TicketDetail
├── test_command_bar.py            # Widget tests for CommandBar
├── test_status_bar.py             # Widget tests for StatusBar
├── test_search_input.py           # Widget tests for SearchInput
├── test_splash_screen.py          # Screen tests for SplashScreen
├── test_discussion_screen.py      # Screen tests for DiscussionScreen
├── test_comment_screen.py         # Screen tests for CommentScreen
├── test_points_screen.py          # Screen tests for PointsScreen
├── test_quick_ticket_screen.py    # Screen tests for QuickTicketScreen
├── test_services.py               # Service layer tests
├── test_mock_client_discussions.py # MockClient discussion tests
├── test_config.py                 # Configuration tests
├── test_user_settings.py          # User settings tests
├── test_rally_client.py           # RallyClient tests
├── test_html_to_text.py           # HTML conversion tests
├── test_logging.py                # Logging module tests
├── test_snapshots.py              # Visual regression tests
└── __snapshots__/                 # SVG snapshot baselines
    └── test_snapshots/
```

**Current Test Count: 321 tests**

## Unit Tests

Unit tests verify individual components work correctly in isolation.

### Example: Testing the Ticket Model

```python
# tests/test_ticket_model.py
from rally_tui.models import Ticket

def test_display_text():
    ticket = Ticket("US1234", "Login feature", "UserStory", "Open")
    assert ticket.display_text == "US1234 Login feature"

def test_type_prefix():
    ticket = Ticket("DE456", "Bug fix", "Defect", "Open")
    assert ticket.type_prefix == "DE"
```

## Widget Tests

Widget tests use Textual's `run_test()` method and the `Pilot` class to simulate user interactions.

### Example: Testing Keyboard Navigation

```python
# tests/test_ticket_list.py
from rally_tui.app import RallyTUI
from rally_tui.widgets import TicketList

async def test_keyboard_navigation():
    app = RallyTUI()
    async with app.run_test() as pilot:
        ticket_list = app.query_one(TicketList)

        # Initial state
        assert ticket_list.index == 0

        # Press 'j' to move down
        await pilot.press("j")
        assert ticket_list.index == 1

        # Press 'k' to move up
        await pilot.press("k")
        assert ticket_list.index == 0
```

### Pilot Methods

| Method | Description |
|--------|-------------|
| `pilot.press("key")` | Simulate key press |
| `pilot.click("#id")` | Click element by CSS selector |
| `pilot.pause()` | Wait for pending messages |

## Snapshot Tests

Snapshot tests capture SVG screenshots of the application and compare them against baselines.

### Running Snapshot Tests

```bash
# Run snapshot tests
pytest tests/test_snapshots.py

# Update baselines after intentional UI changes
pytest tests/test_snapshots.py --snapshot-update
```

### Example: Snapshot Test

```python
# tests/test_snapshots.py
def test_initial_render(snap_compare):
    from rally_tui.app import RallyTUI
    assert snap_compare(RallyTUI())

def test_after_navigation(snap_compare):
    from rally_tui.app import RallyTUI
    assert snap_compare(RallyTUI(), press=["j", "j"])

def test_small_terminal(snap_compare):
    from rally_tui.app import RallyTUI
    assert snap_compare(RallyTUI(), terminal_size=(60, 15))
```

### Snapshot Test Options

| Parameter | Description |
|-----------|-------------|
| `press=["j", "k"]` | Keys to press before screenshot |
| `terminal_size=(80, 24)` | Terminal dimensions |
| `run_before=async_func` | Async function to run before capture |

### First Run Behavior

Snapshot tests **fail on first run** because no baseline exists. This is expected. After verifying the output looks correct:

```bash
pytest --snapshot-update
```

### Reviewing Failed Snapshots

When a snapshot test fails, pytest generates an HTML report showing the diff. Review the changes:
- If the change is intentional, update the baseline with `--snapshot-update`
- If the change is a bug, fix the code

## Coverage

```bash
# Run with coverage report
pytest --cov=rally_tui --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Targets

| Component | Target |
|-----------|--------|
| Models | 100% |
| Widgets | 90%+ |
| Services | 90%+ |
| App | 80%+ |

## Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
@pytest.fixture
def sample_tickets() -> list[Ticket]:
    """Provides a list of test tickets with all fields."""
    return [
        Ticket(
            formatted_id="US100",
            name="Test story one",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            description="Test description for story one.",
            iteration="Sprint 1",
            points=3,
        ),
        Ticket(
            formatted_id="DE200",
            name="Test defect",
            ticket_type="Defect",
            state="Open",
            owner=None,  # Tests "Unassigned" display
            description="Test description for defect.",
            iteration="Sprint 1",
            points=2,
        ),
        Ticket(
            formatted_id="TA300",
            name="Test task",
            ticket_type="Task",
            state="In Progress",
            owner="Another User",
            description="",
            iteration=None,  # Tests "Unscheduled" display
            points=None,     # Tests "—" display
        ),
    ]

@pytest.fixture
def single_ticket() -> Ticket:
    """Provides a single ticket for unit tests."""
    return Ticket(
        formatted_id="US999",
        name="Single test ticket",
        ticket_type="UserStory",
        state="Completed",
        owner="Owner Name",
        description="This is a test description.",
        iteration="Sprint 2",
        points=5,
    )
```

## Async Testing

All widget and integration tests must be async. pytest-asyncio handles this automatically when configured:

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## Mock Rally Client

For integration tests, use the mock client to avoid real API calls:

```python
# Future: tests/test_integration.py
from rally_tui.services.mock_client import MockRallyClient

async def test_loading_tickets():
    mock_client = MockRallyClient(tickets=sample_tickets)
    app = RallyTUI(client=mock_client)
    async with app.run_test() as pilot:
        # Verify tickets loaded
        assert len(app.query("TicketListItem")) == len(sample_tickets)
```

## Continuous Integration

Tests run automatically on:
- Every push
- Every pull request

The CI pipeline:
1. Installs dependencies
2. Runs linting (ruff)
3. Runs type checking (mypy)
4. Runs all tests with coverage
5. Uploads coverage report

## Troubleshooting

### Snapshot tests fail unexpectedly

1. Check terminal capabilities - snapshots may differ across terminals
2. Review the diff report
3. If running in CI, ensure consistent terminal size

### Async tests hang

- Ensure `asyncio_mode = "auto"` is set in pyproject.toml
- Check for missing `await` statements
- Use `pilot.pause()` after actions that trigger async updates

### Coverage missing lines

- Ensure tests actually execute the code paths
- Check for conditional branches not covered
- Add specific tests for edge cases
