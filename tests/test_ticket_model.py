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

    def test_ticket_optional_parent_id(self) -> None:
        """Parent ID should be optional and default to None."""
        ticket = Ticket("US1", "Test", "UserStory", "Open")
        assert ticket.parent_id is None

    def test_ticket_with_parent_id(self) -> None:
        """Parent ID should be stored when provided."""
        ticket = Ticket("US1", "Test", "UserStory", "Open", parent_id="F59625")
        assert ticket.parent_id == "F59625"


class TestTicketRallyUrl:
    """Tests for the rally_url method."""

    def test_rally_url_user_story(self) -> None:
        """User story URL should use userstory path."""
        ticket = Ticket("US1234", "Test", "UserStory", "Open", object_id="12345")
        url = ticket.rally_url()
        assert url == "https://rally1.rallydev.com/#/detail/userstory/12345"

    def test_rally_url_defect(self) -> None:
        """Defect URL should use defect path."""
        ticket = Ticket("DE456", "Test", "Defect", "Open", object_id="67890")
        url = ticket.rally_url()
        assert url == "https://rally1.rallydev.com/#/detail/defect/67890"

    def test_rally_url_task(self) -> None:
        """Task URL should use task path."""
        ticket = Ticket("TA789", "Test", "Task", "Open", object_id="11111")
        url = ticket.rally_url()
        assert url == "https://rally1.rallydev.com/#/detail/task/11111"

    def test_rally_url_testcase(self) -> None:
        """Test case URL should use testcase path."""
        ticket = Ticket("TC101", "Test", "TestCase", "Open", object_id="22222")
        url = ticket.rally_url()
        assert url == "https://rally1.rallydev.com/#/detail/testcase/22222"

    def test_rally_url_custom_server(self) -> None:
        """URL should use custom server when provided."""
        ticket = Ticket("US1", "Test", "UserStory", "Open", object_id="12345")
        url = ticket.rally_url(server="custom.rally.com")
        assert url == "https://custom.rally.com/#/detail/userstory/12345"

    def test_rally_url_no_object_id(self) -> None:
        """URL should be None when object_id is missing."""
        ticket = Ticket("US1", "Test", "UserStory", "Open")
        url = ticket.rally_url()
        assert url is None
