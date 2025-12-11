"""Unit tests for the Ticket model."""

import pytest

from rally_tui.models import Ticket


class TestTicket:
    """Tests for the Ticket dataclass."""

    def test_display_text(self, single_ticket: Ticket) -> None:
        """Display text should combine ID and name."""
        assert single_ticket.display_text == "US999 Single test ticket"

    def test_type_prefix_user_story(self) -> None:
        """User story prefix should be US."""
        ticket = Ticket("US1234", "Test", "UserStory", "Open")
        assert ticket.type_prefix == "US"

    def test_type_prefix_defect(self) -> None:
        """Defect prefix should be DE."""
        ticket = Ticket("DE456", "Test", "Defect", "Open")
        assert ticket.type_prefix == "DE"

    def test_type_prefix_task(self) -> None:
        """Task prefix should be TA."""
        ticket = Ticket("TA789", "Test", "Task", "Open")
        assert ticket.type_prefix == "TA"

    def test_type_prefix_test_case(self) -> None:
        """Test case prefix should be TC."""
        ticket = Ticket("TC101", "Test", "TestCase", "Open")
        assert ticket.type_prefix == "TC"

    def test_ticket_immutability(self, single_ticket: Ticket) -> None:
        """Tickets should be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            single_ticket.name = "Changed"  # type: ignore[misc]

    def test_ticket_equality(self) -> None:
        """Two tickets with same data should be equal."""
        t1 = Ticket("US1", "Test", "UserStory", "Open", "Owner")
        t2 = Ticket("US1", "Test", "UserStory", "Open", "Owner")
        assert t1 == t2

    def test_ticket_inequality(self) -> None:
        """Tickets with different data should not be equal."""
        t1 = Ticket("US1", "Test", "UserStory", "Open", "Owner")
        t2 = Ticket("US2", "Test", "UserStory", "Open", "Owner")
        assert t1 != t2

    def test_ticket_optional_owner(self) -> None:
        """Owner should be optional and default to None."""
        ticket = Ticket("US1", "Test", "UserStory", "Open")
        assert ticket.owner is None

    def test_ticket_with_owner(self) -> None:
        """Owner should be stored when provided."""
        ticket = Ticket("US1", "Test", "UserStory", "Open", "John Doe")
        assert ticket.owner == "John Doe"
