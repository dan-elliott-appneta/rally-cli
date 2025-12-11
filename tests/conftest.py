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
            state="In Progress",
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
