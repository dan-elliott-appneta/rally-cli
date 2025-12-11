# Iteration 6: Real Rally Integration

## Goal

Connect the TUI to the actual Rally API using pyral, with proper configuration management, error handling, and connection status indication.

## Prerequisites

- Iteration 5 completed (service layer with dependency injection)
- pyral package available (already in dependencies)
- Rally API key for testing (optional - app works offline with MockRallyClient)

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        RallyTUI                               │
│  ┌─────────────────┐                                         │
│  │  StatusBar      │  Shows: Workspace | Project | Connected │
│  └─────────────────┘                                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  RallyClientProtocol                                   │  │
│  │  ├── workspace: str                                    │  │
│  │  ├── project: str                                      │  │
│  │  ├── get_tickets(query?) -> list[Ticket]               │  │
│  │  └── get_ticket(id) -> Ticket | None                   │  │
│  └────────────────────────────────────────────────────────┘  │
│           ▲                              ▲                    │
│           │                              │                    │
│  ┌────────┴────────┐          ┌─────────┴─────────┐         │
│  │  MockRallyClient │          │   RallyClient     │         │
│  │  (in-memory)     │          │   (pyral API)     │         │
│  └──────────────────┘          └───────────────────┘         │
│                                         │                     │
│                                         ▼                     │
│                                 ┌───────────────┐            │
│                                 │ RallyConfig   │            │
│                                 │ (pydantic)    │            │
│                                 └───────────────┘            │
│                                         │                     │
│                      ┌──────────────────┼──────────────────┐ │
│                      ▼                  ▼                  ▼ │
│              Environment         Config File       CLI Args  │
│              Variables           (.rally.cfg)               │
└──────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Add Configuration with pydantic-settings

Create a configuration class that loads from environment variables and optional config file.

**File: `src/rally_tui/config.py`**

```python
"""Rally TUI Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class RallyConfig(BaseSettings):
    """Rally API configuration.

    Loads settings from environment variables with RALLY_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="RALLY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server: str = "rally1.rallydev.com"
    apikey: str = ""
    workspace: str = ""
    project: str = ""

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.apikey)
```

**Environment Variables:**
| Variable | Description | Default |
|----------|-------------|---------|
| `RALLY_SERVER` | Rally server hostname | `rally1.rallydev.com` |
| `RALLY_APIKEY` | Rally API key | (empty) |
| `RALLY_WORKSPACE` | Workspace name | (empty) |
| `RALLY_PROJECT` | Project name | (empty) |

### Step 2: Implement RallyClient

Create the real Rally client that connects to the API using pyral.

**File: `src/rally_tui/services/rally_client.py`**

```python
"""Rally API client implementation."""

from typing import TYPE_CHECKING

from pyral import Rally

from rally_tui.config import RallyConfig
from rally_tui.models import Ticket

if TYPE_CHECKING:
    from pyral.entity import RallyEntity


class RallyClient:
    """Rally API client using pyral.

    Implements RallyClientProtocol for seamless integration with the app.
    """

    def __init__(self, config: RallyConfig) -> None:
        """Initialize the Rally client.

        Args:
            config: Rally configuration with API key and connection details.
        """
        self._config = config
        self._rally = Rally(
            config.server,
            apikey=config.apikey,
            workspace=config.workspace or None,
            project=config.project or None,
        )
        # Cache workspace/project names from connection
        self._workspace = config.workspace or self._rally.getWorkspace().Name
        self._project = config.project or self._rally.getProject().Name

    @property
    def workspace(self) -> str:
        """Get the workspace name."""
        return self._workspace

    @property
    def project(self) -> str:
        """Get the project name."""
        return self._project

    def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets from Rally.

        Args:
            query: Optional Rally query string.

        Returns:
            List of tickets matching the query.
        """
        # Fetch both User Stories and Defects
        tickets: list[Ticket] = []

        for entity_type in ["HierarchicalRequirement", "Defect", "Task"]:
            response = self._rally.get(
                entity_type,
                fetch="FormattedID,Name,ScheduleState,Owner,Description,Iteration,PlanEstimate",
                query=query,
                pagesize=200,
            )

            for item in response:
                tickets.append(self._to_ticket(item, entity_type))

        return tickets

    def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by formatted ID.

        Args:
            formatted_id: The ticket's formatted ID (e.g., "US1234").

        Returns:
            The ticket if found, None otherwise.
        """
        # Determine entity type from prefix
        entity_type = self._get_entity_type(formatted_id)

        response = self._rally.get(
            entity_type,
            fetch="FormattedID,Name,ScheduleState,Owner,Description,Iteration,PlanEstimate",
            query=f'FormattedID = "{formatted_id}"',
        )

        try:
            item = response.next()
            return self._to_ticket(item, entity_type)
        except StopIteration:
            return None

    def _to_ticket(self, item: "RallyEntity", entity_type: str) -> Ticket:
        """Convert a pyral entity to our Ticket model.

        Args:
            item: The pyral entity object.
            entity_type: The Rally entity type name.

        Returns:
            A Ticket instance.
        """
        # Map entity type to our TicketType
        type_map = {
            "HierarchicalRequirement": "UserStory",
            "Defect": "Defect",
            "Task": "Task",
            "TestCase": "TestCase",
        }
        ticket_type = type_map.get(entity_type, "UserStory")

        # Extract owner name (Owner is a nested object)
        owner = None
        if hasattr(item, "Owner") and item.Owner:
            owner = getattr(item.Owner, "Name", None) or getattr(item.Owner, "_refObjectName", None)

        # Extract iteration name
        iteration = None
        if hasattr(item, "Iteration") and item.Iteration:
            iteration = getattr(item.Iteration, "Name", None) or getattr(item.Iteration, "_refObjectName", None)

        # Extract points (PlanEstimate)
        points = None
        if hasattr(item, "PlanEstimate") and item.PlanEstimate is not None:
            points = int(item.PlanEstimate)

        # Get state - use ScheduleState for stories, State for defects
        state = getattr(item, "ScheduleState", None) or getattr(item, "State", "Unknown")

        return Ticket(
            formatted_id=item.FormattedID,
            name=item.Name,
            ticket_type=ticket_type,
            state=state,
            owner=owner,
            description=getattr(item, "Description", "") or "",
            iteration=iteration,
            points=points,
        )

    def _get_entity_type(self, formatted_id: str) -> str:
        """Determine Rally entity type from formatted ID prefix.

        Args:
            formatted_id: The ticket's formatted ID.

        Returns:
            The Rally entity type name.
        """
        prefix = ""
        for char in formatted_id:
            if char.isdigit():
                break
            prefix += char

        prefix_map = {
            "US": "HierarchicalRequirement",
            "DE": "Defect",
            "TA": "Task",
            "TC": "TestCase",
        }
        return prefix_map.get(prefix.upper(), "HierarchicalRequirement")
```

### Step 3: Update Services Module Exports

**File: `src/rally_tui/services/__init__.py`**

```python
"""Rally TUI Services - Data access layer."""

from .mock_client import MockRallyClient
from .protocol import RallyClientProtocol
from .rally_client import RallyClient

__all__ = ["MockRallyClient", "RallyClient", "RallyClientProtocol"]
```

### Step 4: Update StatusBar with Connection Status

Modify StatusBar to show "Connected" or "Offline" based on client type.

**Changes to `src/rally_tui/widgets/status_bar.py`:**

```python
def __init__(
    self,
    workspace: str = "Not Connected",
    project: str = "",
    connected: bool = False,  # NEW parameter
    *,
    id: str | None = None,
    classes: str | None = None,
) -> None:
    # ... existing code ...
    self._connected = connected

def _update_display(self) -> None:
    """Update the status bar content."""
    parts = [f"Workspace: {self._workspace}"]
    if self._project:
        parts.append(f"Project: {self._project}")
    # Show connection status
    status = "Connected" if self._connected else "Offline"
    parts.append(status)
    self._display_content = " | ".join(parts)
    self.update(self._display_content)

def set_connected(self, connected: bool) -> None:
    """Update connection status."""
    self._connected = connected
    self._update_display()
```

### Step 5: Update App to Use Configuration

**Changes to `src/rally_tui/app.py`:**

```python
from rally_tui.config import RallyConfig
from rally_tui.services import MockRallyClient, RallyClient, RallyClientProtocol

class RallyTUI(App[None]):
    def __init__(
        self,
        client: RallyClientProtocol | None = None,
        config: RallyConfig | None = None,
    ) -> None:
        super().__init__()

        if client is not None:
            self._client = client
            self._connected = isinstance(client, RallyClient)
        elif config is not None and config.is_configured:
            try:
                self._client = RallyClient(config)
                self._connected = True
            except Exception:
                self._client = MockRallyClient()
                self._connected = False
        else:
            self._client = MockRallyClient()
            self._connected = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield StatusBar(
            workspace=self._client.workspace,
            project=self._client.project,
            connected=self._connected,  # NEW
            id="status-bar",
        )
        # ... rest unchanged ...
```

### Step 6: Update Main Entry Point

**Changes to `src/rally_tui/app.py` main function:**

```python
def main() -> None:
    """Entry point for the application."""
    from rally_tui.config import RallyConfig

    config = RallyConfig()
    app = RallyTUI(config=config)
    app.run()
```

## Testing Strategy

### Unit Tests for RallyClient

Since we don't want to hit the real API in tests, we'll test:
1. The `_to_ticket` mapping logic with mock pyral entities
2. The `_get_entity_type` prefix detection
3. Configuration loading

**File: `tests/test_rally_client.py`**

```python
"""Tests for RallyClient mapping and configuration."""

import pytest
from unittest.mock import MagicMock, patch

from rally_tui.config import RallyConfig
from rally_tui.services.rally_client import RallyClient


class MockRallyEntity:
    """Mock pyral entity for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestRallyClientMapping:
    """Tests for entity-to-ticket mapping."""

    def test_map_user_story(self):
        """User story maps correctly."""
        entity = MockRallyEntity(
            FormattedID="US1234",
            Name="User story name",
            ScheduleState="In-Progress",
            Owner=MockRallyEntity(Name="John Doe"),
            Description="Story description",
            Iteration=MockRallyEntity(Name="Sprint 5"),
            PlanEstimate=5.0,
        )

        # Create client with mocked Rally connection
        with patch("rally_tui.services.rally_client.Rally"):
            config = RallyConfig(apikey="test_key")
            client = RallyClient.__new__(RallyClient)
            client._config = config

            ticket = client._to_ticket(entity, "HierarchicalRequirement")

            assert ticket.formatted_id == "US1234"
            assert ticket.name == "User story name"
            assert ticket.ticket_type == "UserStory"
            assert ticket.state == "In-Progress"
            assert ticket.owner == "John Doe"
            assert ticket.description == "Story description"
            assert ticket.iteration == "Sprint 5"
            assert ticket.points == 5

    def test_map_defect(self):
        """Defect maps correctly."""
        entity = MockRallyEntity(
            FormattedID="DE456",
            Name="Bug name",
            ScheduleState="Open",
            Owner=None,
            Description="",
            Iteration=None,
            PlanEstimate=None,
        )

        with patch("rally_tui.services.rally_client.Rally"):
            config = RallyConfig(apikey="test_key")
            client = RallyClient.__new__(RallyClient)
            client._config = config

            ticket = client._to_ticket(entity, "Defect")

            assert ticket.formatted_id == "DE456"
            assert ticket.ticket_type == "Defect"
            assert ticket.owner is None
            assert ticket.points is None


class TestEntityTypeDetection:
    """Tests for prefix-to-entity-type mapping."""

    @pytest.mark.parametrize("formatted_id,expected", [
        ("US1234", "HierarchicalRequirement"),
        ("DE456", "Defect"),
        ("TA789", "Task"),
        ("TC101", "TestCase"),
        ("us1234", "HierarchicalRequirement"),  # lowercase
    ])
    def test_get_entity_type(self, formatted_id, expected):
        """Formatted ID prefix maps to correct entity type."""
        with patch("rally_tui.services.rally_client.Rally"):
            config = RallyConfig(apikey="test_key")
            client = RallyClient.__new__(RallyClient)
            client._config = config

            result = client._get_entity_type(formatted_id)
            assert result == expected
```

### Integration Tests

Tests that verify the app works with real configuration (but still using mock client).

**File: `tests/test_config.py`**

```python
"""Tests for configuration loading."""

import os
import pytest
from rally_tui.config import RallyConfig


class TestRallyConfig:
    """Tests for RallyConfig."""

    def test_default_values(self):
        """Default configuration has expected values."""
        config = RallyConfig()
        assert config.server == "rally1.rallydev.com"
        assert config.apikey == ""
        assert not config.is_configured

    def test_is_configured_with_apikey(self):
        """Config is considered configured when API key is set."""
        config = RallyConfig(apikey="test_key")
        assert config.is_configured

    def test_loads_from_environment(self, monkeypatch):
        """Config loads from environment variables."""
        monkeypatch.setenv("RALLY_APIKEY", "env_api_key")
        monkeypatch.setenv("RALLY_WORKSPACE", "Test Workspace")
        monkeypatch.setenv("RALLY_PROJECT", "Test Project")

        config = RallyConfig()
        assert config.apikey == "env_api_key"
        assert config.workspace == "Test Workspace"
        assert config.project == "Test Project"
        assert config.is_configured
```

## Key Files Modified/Created

| File | Action | Description |
|------|--------|-------------|
| `src/rally_tui/config.py` | Create | Configuration with pydantic-settings |
| `src/rally_tui/services/rally_client.py` | Create | Real Rally API client |
| `src/rally_tui/services/__init__.py` | Modify | Export RallyClient |
| `src/rally_tui/widgets/status_bar.py` | Modify | Add `connected` parameter |
| `src/rally_tui/app.py` | Modify | Accept config, show connection status |
| `tests/test_rally_client.py` | Create | Tests for mapping logic |
| `tests/test_config.py` | Create | Tests for configuration |

## Error Handling

The app handles Rally connection errors gracefully:

1. **Invalid API Key**: Falls back to MockRallyClient, shows "Offline"
2. **Network Error**: Falls back to MockRallyClient, shows "Offline"
3. **Invalid Workspace/Project**: Falls back to MockRallyClient, shows "Offline"

Future iterations could add:
- Toast notifications for errors
- Retry logic with exponential backoff
- Connection refresh button

## Testing Commands

```bash
# Run all tests
pytest

# Run only new tests
pytest tests/test_rally_client.py tests/test_config.py

# Test with real Rally (requires RALLY_APIKEY env var)
RALLY_APIKEY=your_key RALLY_WORKSPACE="Your Workspace" rally-tui
```

## Deliverables

- [ ] RallyConfig class with environment variable loading
- [ ] RallyClient implementing RallyClientProtocol
- [ ] Entity-to-Ticket mapping with all fields
- [ ] StatusBar showing connection status
- [ ] App falls back gracefully when not configured
- [ ] Unit tests for mapping logic
- [ ] Configuration tests
- [ ] Updated documentation

## Notes

- pyral uses `HierarchicalRequirement` for User Stories (not `UserStory`)
- Rally API returns nested objects for Owner, Iteration, etc.
- `ScheduleState` is used for stories/tasks, `State` for defects
- `PlanEstimate` is the Rally field name for story points
- The app works fully offline when no API key is configured
