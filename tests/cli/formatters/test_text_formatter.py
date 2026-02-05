"""Tests for text formatter."""

import pytest

from rally_tui.cli.formatters.base import CLIResult
from rally_tui.cli.formatters.text import TextFormatter
from rally_tui.models import Ticket


@pytest.fixture
def formatter():
    """Create a TextFormatter instance."""
    return TextFormatter()


@pytest.fixture
def sample_tickets():
    """Create sample tickets for testing."""
    return [
        Ticket(
            formatted_id="US12345",
            name="User login feature",
            ticket_type="UserStory",
            state="In-Progress",
            owner="John Doe",
            description="Implement OAuth2 login",
            notes="",
            iteration="Sprint 2024.01",
            points=5,
            object_id="123456789",
            parent_id="F59625",
        ),
        Ticket(
            formatted_id="DE67890",
            name="Fix API timeout",
            ticket_type="Defect",
            state="Completed",
            owner="Jane Smith",
            description="API times out on large requests",
            notes="",
            iteration="Sprint 2024.01",
            points=3,
            object_id="987654321",
            parent_id=None,
        ),
        Ticket(
            formatted_id="TA11111",
            name="Write unit tests",
            ticket_type="Task",
            state="Defined",
            owner=None,
            description="Add test coverage",
            notes="",
            iteration=None,
            points=None,
            object_id="111111111",
            parent_id=None,
        ),
    ]


class TestTextFormatterTickets:
    """Tests for formatting ticket lists."""

    def test_format_empty_tickets(self, formatter):
        """Test formatting empty ticket list."""
        result = CLIResult(success=True, data=[])
        output = formatter.format_tickets(result)
        assert output == "No tickets found."

    def test_format_single_ticket(self, formatter, sample_tickets):
        """Test formatting a single ticket."""
        result = CLIResult(success=True, data=[sample_tickets[0]])
        output = formatter.format_tickets(result)

        # Check header exists
        assert "ID" in output
        assert "Type" in output
        assert "State" in output
        assert "Owner" in output

        # Check ticket data exists
        assert "US12345" in output
        assert "Story" in output  # Abbreviated type
        assert "In-Progress" in output
        assert "John Doe" in output

    def test_format_multiple_tickets(self, formatter, sample_tickets):
        """Test formatting multiple tickets."""
        result = CLIResult(success=True, data=sample_tickets)
        output = formatter.format_tickets(result)

        # Check all tickets present
        assert "US12345" in output
        assert "DE67890" in output
        assert "TA11111" in output

    def test_format_with_custom_fields(self, formatter, sample_tickets):
        """Test formatting with custom field selection."""
        result = CLIResult(success=True, data=sample_tickets)
        output = formatter.format_tickets(result, fields=["formatted_id", "name", "state"])

        # Check selected fields
        assert "US12345" in output
        assert "User login feature" in output
        assert "In-Progress" in output

        # Check excluded fields not in column headers
        lines = output.split("\n")
        header = lines[0]
        assert "Owner" not in header
        assert "Points" not in header

    def test_format_handles_none_values(self, formatter, sample_tickets):
        """Test that None values are displayed as '-'."""
        result = CLIResult(success=True, data=[sample_tickets[2]])  # Task with no owner
        output = formatter.format_tickets(result)

        # None owner should show as '-'
        assert "-" in output

    def test_format_error(self, formatter):
        """Test formatting error result."""
        result = CLIResult(success=False, data=None, error="Connection failed")
        output = formatter.format_tickets(result)
        assert "Error: Connection failed" in output


class TestTextFormatterComment:
    """Tests for formatting comment confirmations."""

    def test_format_comment_from_dict(self, formatter):
        """Test formatting comment from dictionary."""
        result = CLIResult(
            success=True,
            data={
                "artifact_id": "US12345",
                "user": "John Doe",
                "created_at": "2024-01-25 14:30:00",
                "text": "Updated the implementation",
            },
        )
        output = formatter.format_comment(result)

        assert "Comment added to US12345" in output
        assert "User: John Doe" in output
        assert "Text: Updated the implementation" in output

    def test_format_comment_error(self, formatter):
        """Test formatting comment error."""
        result = CLIResult(success=False, data=None, error="Ticket not found")
        output = formatter.format_comment(result)
        assert "Error: Ticket not found" in output


class TestTextFormatterTypeAbbreviations:
    """Tests for ticket type abbreviations."""

    def test_userstory_abbreviated(self, formatter):
        """Test UserStory is abbreviated to Story."""
        ticket = Ticket(
            formatted_id="US1",
            name="Test",
            ticket_type="UserStory",
            state="Open",
        )
        result = CLIResult(success=True, data=[ticket])
        output = formatter.format_tickets(result)
        assert "Story" in output
        assert "UserStory" not in output

    def test_defect_not_abbreviated(self, formatter):
        """Test Defect is not abbreviated."""
        ticket = Ticket(
            formatted_id="DE1",
            name="Test",
            ticket_type="Defect",
            state="Open",
        )
        result = CLIResult(success=True, data=[ticket])
        output = formatter.format_tickets(result)
        assert "Defect" in output


class TestTextFormatterTruncation:
    """Tests for text truncation."""

    def test_long_title_truncated(self, formatter):
        """Test that long titles are truncated."""
        long_name = "A" * 100
        ticket = Ticket(
            formatted_id="US1",
            name=long_name,
            ticket_type="UserStory",
            state="Open",
        )
        result = CLIResult(success=True, data=[ticket])
        output = formatter.format_tickets(result, fields=["formatted_id", "name"])

        # Title should be truncated (default max is 40)
        lines = output.split("\n")
        data_line = lines[2]  # Skip header and separator
        assert "..." in data_line
        assert len(long_name) > len(data_line)
