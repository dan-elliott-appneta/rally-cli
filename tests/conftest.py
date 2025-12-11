"""Pytest configuration and fixtures for Rally TUI tests."""

import pytest

from rally_tui.models import Ticket


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
        ),
        Ticket(
            formatted_id="DE200",
            name="Test defect",
            ticket_type="Defect",
            state="Open",
            owner=None,
        ),
        Ticket(
            formatted_id="TA300",
            name="Test task",
            ticket_type="Task",
            state="In Progress",
            owner="Another User",
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
    )
