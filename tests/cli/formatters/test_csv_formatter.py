"""Tests for CSV formatter."""

import csv
import io
from datetime import UTC, datetime

import pytest

from rally_tui.cli.formatters.base import CLIResult
from rally_tui.cli.formatters.csv import CSVFormatter
from rally_tui.models import Discussion, Ticket


@pytest.fixture
def formatter():
    """Create a CSVFormatter instance."""
    return CSVFormatter()


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
            description="API times out",
            notes="",
            iteration="Sprint 2024.01",
            points=3,
            object_id="987654321",
            parent_id=None,
        ),
    ]


@pytest.fixture
def sample_discussion():
    """Create a sample discussion for testing."""
    return Discussion(
        object_id="111111111",
        text="Updated the implementation",
        user="John Doe",
        created_at=datetime(2024, 1, 25, 14, 30, 0, tzinfo=UTC),
        artifact_id="US12345",
    )


class TestCSVFormatterTickets:
    """Tests for formatting ticket lists as CSV."""

    def test_format_empty_tickets(self, formatter):
        """Test formatting empty ticket list."""
        result = CLIResult(success=True, data=[])
        output = formatter.format_tickets(result)
        assert output == ""

    def test_format_single_ticket(self, formatter, sample_tickets):
        """Test formatting a single ticket."""
        result = CLIResult(success=True, data=[sample_tickets[0]])
        output = formatter.format_tickets(result)

        # Parse as CSV
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Check header row
        assert len(rows) == 2  # Header + 1 data row
        assert "formatted_id" in rows[0]
        assert "name" in rows[0]

        # Check data row
        assert "US12345" in rows[1]
        assert "User login feature" in rows[1]

    def test_format_multiple_tickets(self, formatter, sample_tickets):
        """Test formatting multiple tickets."""
        result = CLIResult(success=True, data=sample_tickets)
        output = formatter.format_tickets(result)

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Header + 2 data rows
        assert len(rows) == 3

    def test_format_with_custom_fields(self, formatter, sample_tickets):
        """Test formatting with custom field selection."""
        result = CLIResult(success=True, data=sample_tickets)
        output = formatter.format_tickets(result, fields=["formatted_id", "name", "state"])

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Check header has only selected fields
        header = rows[0]
        assert header == ["formatted_id", "name", "state"]

        # Check data
        assert rows[1][0] == "US12345"
        assert rows[1][1] == "User login feature"
        assert rows[1][2] == "In-Progress"

    def test_format_handles_none_values(self, formatter):
        """Test that None values are converted to empty strings."""
        ticket = Ticket(
            formatted_id="TA1",
            name="Test",
            ticket_type="Task",
            state="Open",
            owner=None,
            points=None,
        )
        result = CLIResult(success=True, data=[ticket])
        output = formatter.format_tickets(result, fields=["formatted_id", "owner", "points"])

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # None should be empty string
        assert rows[1][1] == ""  # owner
        assert rows[1][2] == ""  # points

    def test_format_handles_commas_in_values(self, formatter):
        """Test that commas in values are properly quoted."""
        ticket = Ticket(
            formatted_id="US1",
            name="Feature: login, logout, and signup",
            ticket_type="UserStory",
            state="Open",
        )
        result = CLIResult(success=True, data=[ticket])
        output = formatter.format_tickets(result, fields=["formatted_id", "name"])

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Should parse correctly despite comma in name
        assert rows[1][1] == "Feature: login, logout, and signup"

    def test_format_error(self, formatter):
        """Test formatting error result."""
        result = CLIResult(success=False, data=None, error="Connection failed")
        output = formatter.format_tickets(result)
        assert "Error: Connection failed" in output


class TestCSVFormatterComment:
    """Tests for formatting comment confirmations as CSV."""

    def test_format_comment_from_discussion(self, formatter, sample_discussion):
        """Test formatting comment from Discussion object."""
        result = CLIResult(success=True, data=sample_discussion)
        output = formatter.format_comment(result)

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Header + 1 data row
        assert len(rows) == 2
        assert rows[0] == ["artifact_id", "user", "created_at", "text"]
        assert rows[1][0] == "US12345"
        assert rows[1][1] == "John Doe"
        assert rows[1][3] == "Updated the implementation"

    def test_format_comment_from_dict(self, formatter):
        """Test formatting comment from dictionary."""
        result = CLIResult(
            success=True,
            data={
                "artifact_id": "US12345",
                "user": "John Doe",
                "created_at": "2024-01-25T14:30:00",
                "text": "Updated the implementation",
            },
        )
        output = formatter.format_comment(result)

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        assert rows[1][0] == "US12345"

    def test_format_comment_error(self, formatter):
        """Test formatting comment error."""
        result = CLIResult(success=False, data=None, error="Ticket not found")
        output = formatter.format_comment(result)
        assert "Error: Ticket not found" in output


class TestCSVValidity:
    """Tests to ensure CSV output is always valid."""

    def test_output_is_valid_csv(self, formatter, sample_tickets):
        """Test that output is always valid CSV."""
        result = CLIResult(success=True, data=sample_tickets)
        output = formatter.format_tickets(result)

        # Should not raise
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Each row should have same number of columns
        num_cols = len(rows[0])
        for row in rows:
            assert len(row) == num_cols

    def test_points_as_integer(self, formatter):
        """Test that integer points are not displayed with decimals."""
        ticket = Ticket(
            formatted_id="US1",
            name="Test",
            ticket_type="UserStory",
            state="Open",
            points=5.0,  # Float that equals integer
        )
        result = CLIResult(success=True, data=[ticket])
        output = formatter.format_tickets(result, fields=["formatted_id", "points"])

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Should be "5" not "5.0"
        assert rows[1][1] == "5"

    def test_points_as_float(self, formatter):
        """Test that float points are preserved."""
        ticket = Ticket(
            formatted_id="US1",
            name="Test",
            ticket_type="UserStory",
            state="Open",
            points=5.5,
        )
        result = CLIResult(success=True, data=[ticket])
        output = formatter.format_tickets(result, fields=["formatted_id", "points"])

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Should preserve decimal
        assert rows[1][1] == "5.5"
