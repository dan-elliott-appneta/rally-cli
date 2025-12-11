# Iteration 5: Service Layer & Dependency Injection

## Overview

Iteration 5 introduces a clean service layer architecture that decouples the UI from data sources. This enables:

1. **Testability** - App can be tested with mock data without hitting real APIs
2. **Flexibility** - Easy to swap between mock and real Rally clients
3. **Separation of Concerns** - UI code doesn't know about data fetching details

The key pattern is **dependency injection**: the app receives a client that implements a protocol, rather than creating its own data source.

## Pre-Implementation Checklist

Before starting, verify:
- [x] Iteration 4 complete with 73 tests passing
- [x] Ticket model exists with all needed fields
- [x] Sample data exists in `sample_data.py`
- [x] App currently imports `SAMPLE_TICKETS` directly

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         RallyTUI App                            │
│                              │                                  │
│                              ▼                                  │
│                    RallyClientProtocol                          │
│                         (Protocol)                              │
│                              │                                  │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                  │
│      MockRallyClient                  RallyClient               │
│     (for testing)               (real API - Iteration 6)        │
└─────────────────────────────────────────────────────────────────┘
```

## Tasks

### Step 1: Create RallyClientProtocol

Define the interface that all Rally clients must implement using Python's `Protocol` for structural subtyping.

**File**: `src/rally_tui/services/protocol.py`

```python
from typing import Protocol
from rally_tui.models import Ticket

class RallyClientProtocol(Protocol):
    """Protocol defining the Rally client interface."""

    @property
    def workspace(self) -> str:
        """Get the current workspace name."""
        ...

    @property
    def project(self) -> str:
        """Get the current project name."""
        ...

    def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets, optionally filtered by query."""
        ...

    def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by its formatted ID."""
        ...
```

### Step 2: Create MockRallyClient

Implement the protocol with in-memory data for testing.

**File**: `src/rally_tui/services/mock_client.py`

```python
from rally_tui.models import Ticket
from rally_tui.models.sample_data import SAMPLE_TICKETS

class MockRallyClient:
    """Mock Rally client for testing."""

    def __init__(
        self,
        tickets: list[Ticket] | None = None,
        workspace: str = "Mock Workspace",
        project: str = "Mock Project",
    ) -> None:
        self._tickets = tickets if tickets is not None else list(SAMPLE_TICKETS)
        self._workspace = workspace
        self._project = project

    @property
    def workspace(self) -> str:
        return self._workspace

    @property
    def project(self) -> str:
        return self._project

    def get_tickets(self, query: str | None = None) -> list[Ticket]:
        if query is None:
            return self._tickets
        # Simple case-insensitive filter on name
        query_lower = query.lower()
        return [t for t in self._tickets if query_lower in t.name.lower()]

    def get_ticket(self, formatted_id: str) -> Ticket | None:
        for ticket in self._tickets:
            if ticket.formatted_id == formatted_id:
                return ticket
        return None
```

### Step 3: Create Services Module

Set up the services package with proper exports.

**File**: `src/rally_tui/services/__init__.py`

```python
from .mock_client import MockRallyClient
from .protocol import RallyClientProtocol

__all__ = ["MockRallyClient", "RallyClientProtocol"]
```

### Step 4: Modify RallyTUI to Accept Client

Update the app to accept an injectable client instead of using hardcoded sample data.

**Changes to `app.py`**:

```python
class RallyTUI(App[None]):
    def __init__(
        self,
        client: RallyClientProtocol | None = None,
    ) -> None:
        super().__init__()
        # Default to MockRallyClient if no client provided
        self._client = client or MockRallyClient()

    def compose(self) -> ComposeResult:
        yield Header()
        yield StatusBar(
            workspace=self._client.workspace,
            project=self._client.project,
            id="status-bar",
        )
        tickets = self._client.get_tickets()
        with Horizontal(id="main-container"):
            yield TicketList(tickets, id="ticket-list")
            yield TicketDetail(id="ticket-detail")
        yield CommandBar(id="command-bar")

    def on_mount(self) -> None:
        # Set first ticket in detail panel
        tickets = self._client.get_tickets()
        if tickets:
            detail = self.query_one(TicketDetail)
            detail.ticket = tickets[0]
        # ... rest of on_mount
```

### Step 5: Add Ticket Factory Fixtures

Create pytest fixtures for generating test data.

**File**: `tests/conftest.py` (additions)

```python
import pytest
from rally_tui.models import Ticket
from rally_tui.services import MockRallyClient

@pytest.fixture
def sample_ticket() -> Ticket:
    """A single sample ticket for testing."""
    return Ticket(
        formatted_id="US999",
        name="Test Ticket",
        ticket_type="UserStory",
        state="Defined",
        owner="Test User",
        description="A test ticket for unit tests.",
        iteration="Test Sprint",
        points=5,
    )

@pytest.fixture
def sample_tickets() -> list[Ticket]:
    """A list of sample tickets for testing."""
    return [
        Ticket(
            formatted_id="US001",
            name="First Story",
            ticket_type="UserStory",
            state="In Progress",
            owner="Alice",
            description="First test story.",
            iteration="Sprint 1",
            points=3,
        ),
        Ticket(
            formatted_id="DE001",
            name="First Defect",
            ticket_type="Defect",
            state="Open",
            owner="Bob",
            description="First test defect.",
            iteration="Sprint 1",
            points=2,
        ),
    ]

@pytest.fixture
def mock_client(sample_tickets: list[Ticket]) -> MockRallyClient:
    """A MockRallyClient with sample tickets."""
    return MockRallyClient(
        tickets=sample_tickets,
        workspace="Test Workspace",
        project="Test Project",
    )
```

### Step 6: Write Service Layer Tests

Create tests for MockRallyClient and protocol compliance.

**File**: `tests/test_services.py`

Tests to write:
- MockRallyClient returns all tickets
- MockRallyClient filters tickets by query
- MockRallyClient returns None for unknown ticket
- MockRallyClient returns ticket by ID
- MockRallyClient has workspace property
- MockRallyClient has project property
- MockRallyClient accepts custom tickets
- MockRallyClient defaults to SAMPLE_TICKETS

### Step 7: Update Existing Tests

Update existing tests to use the new client injection pattern.

- Tests can now inject custom MockRallyClient with specific data
- Snapshot tests should continue to work with default client

## Implementation Order

1. **Commit 1**: Create services module with protocol and exports
2. **Commit 2**: Create MockRallyClient implementation
3. **Commit 3**: Add service layer tests
4. **Commit 4**: Modify RallyTUI to accept injectable client
5. **Commit 5**: Add factory fixtures to conftest.py
6. **Commit 6**: Update existing tests if needed
7. **Commit 7**: Update documentation

## Test Coverage Goals

| Test Type | Description |
|-----------|-------------|
| Unit | MockRallyClient.get_tickets() returns all tickets |
| Unit | MockRallyClient.get_tickets(query) filters correctly |
| Unit | MockRallyClient.get_ticket(id) returns correct ticket |
| Unit | MockRallyClient.get_ticket(unknown) returns None |
| Unit | MockRallyClient.workspace property |
| Unit | MockRallyClient.project property |
| Unit | MockRallyClient with custom tickets |
| Integration | RallyTUI renders with injected client |
| Integration | StatusBar shows client's workspace/project |

## Files to Create/Modify

### New Files
- `src/rally_tui/services/__init__.py`
- `src/rally_tui/services/protocol.py`
- `src/rally_tui/services/mock_client.py`
- `tests/test_services.py`

### Modified Files
- `src/rally_tui/app.py` - Accept client parameter
- `tests/conftest.py` - Add factory fixtures

## Key Concepts

### Protocol (Structural Subtyping)

Python's `Protocol` class enables duck typing with type hints:

```python
from typing import Protocol

class RallyClientProtocol(Protocol):
    def get_tickets(self) -> list[Ticket]: ...

# Any class with get_tickets method matches the protocol
# No explicit inheritance needed
```

### Dependency Injection

Instead of:
```python
class RallyTUI(App):
    def compose(self):
        tickets = SAMPLE_TICKETS  # Hardcoded dependency
```

We use:
```python
class RallyTUI(App):
    def __init__(self, client: RallyClientProtocol | None = None):
        self._client = client or MockRallyClient()

    def compose(self):
        tickets = self._client.get_tickets()  # Injected dependency
```

### Factory Fixtures

Pytest fixtures can depend on other fixtures:

```python
@pytest.fixture
def sample_tickets() -> list[Ticket]:
    return [...]

@pytest.fixture
def mock_client(sample_tickets) -> MockRallyClient:
    return MockRallyClient(tickets=sample_tickets)
```

## Success Criteria

- [ ] RallyClientProtocol defined with all needed methods
- [ ] MockRallyClient implements the protocol
- [ ] RallyTUI accepts optional client parameter
- [ ] Default behavior unchanged (uses MockRallyClient with SAMPLE_TICKETS)
- [ ] Tests can inject custom clients
- [ ] StatusBar shows client's workspace/project
- [ ] All tests pass (target: 85+ tests)
- [ ] Documentation updated

## Notes

- The `MockRallyClient` defaults to `SAMPLE_TICKETS` to maintain backward compatibility
- The real `RallyClient` (Iteration 6) will also implement `RallyClientProtocol`
- This pattern makes it easy to test error handling by creating mock clients that raise exceptions
- The query filtering in MockRallyClient is simplified; real Rally queries are more complex
