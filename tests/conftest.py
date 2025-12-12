"""Pytest configuration and fixtures for Rally TUI tests."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rally_tui.models import Ticket
from rally_tui.services import MockRallyClient


# Environment-specific snapshot directories
def pytest_configure(config):
    """Configure snapshot directory based on environment."""
    if os.environ.get("CI"):
        # Use CI-specific snapshots when running in GitHub Actions
        snapshot_dir = Path(__file__).parent / "__snapshots_ci__"
    else:
        # Use local snapshots for development
        snapshot_dir = Path(__file__).parent / "__snapshots__"

    # Set the snapshot directory for pytest-textual-snapshot
    os.environ["TEXTUAL_SNAPSHOT_DIR"] = str(snapshot_dir)


@pytest.fixture
def sample_tickets() -> list[Ticket]:
    """Provide a small set of tickets for testing."""
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
            owner=None,
            description="Test description for defect.",
            iteration="Sprint 1",
            points=2,
        ),
        Ticket(
            formatted_id="TA300",
            name="Test task",
            ticket_type="Task",
            state="In-Progress",
            owner="Another User",
            description="",
            iteration=None,
            points=None,
        ),
    ]


@pytest.fixture
def single_ticket() -> Ticket:
    """Provide a single ticket for unit tests."""
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


@pytest.fixture
def mock_client(sample_tickets: list[Ticket]) -> MockRallyClient:
    """Provide a MockRallyClient with sample tickets."""
    return MockRallyClient(
        tickets=sample_tickets,
        workspace="Test Workspace",
        project="Test Project",
    )


@pytest.fixture
def empty_client() -> MockRallyClient:
    """Provide a MockRallyClient with no tickets."""
    return MockRallyClient(
        tickets=[],
        workspace="Empty Workspace",
        project="Empty Project",
    )


@pytest.fixture
def mock_user_settings() -> MagicMock:
    """Provide mock UserSettings with parent_options and keybindings configured.

    This matches the DEFAULT_FEATURES in MockRallyClient and provides
    VIM keybindings for dynamic keybinding tests.
    """
    from rally_tui.utils.keybindings import VIM_KEYBINDINGS

    settings = MagicMock()
    settings.theme = "dark"
    settings.theme_name = "textual-dark"
    settings.parent_options = ["F59625", "F59627", "F59628"]
    settings.keybindings = dict(VIM_KEYBINDINGS)
    return settings
