"""Tests for JSON formatter."""

import json
from datetime import UTC, datetime

import pytest

from rally_tui.cli.formatters.base import CLIResult
from rally_tui.cli.formatters.json import JSONFormatter
from rally_tui.models import Discussion, Ticket


@pytest.fixture
def formatter():
    """Create a JSONFormatter instance."""
    return JSONFormatter()


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


class TestJSONFormatterTickets:
    """Tests for formatting ticket lists as JSON."""

    def test_format_empty_tickets(self, formatter):
        """Test formatting empty ticket list."""
        result = CLIResult(success=True, data=[])
        output = formatter.format_tickets(result)
        parsed = json.loads(output)

        assert parsed["success"] is True
        assert parsed["data"] == []
        assert parsed["error"] is None

    def test_format_single_ticket(self, formatter, sample_tickets):
        """Test formatting a single ticket."""
        result = CLIResult(success=True, data=[sample_tickets[0]])
        output = formatter.format_tickets(result)
        parsed = json.loads(output)

        assert parsed["success"] is True
        assert len(parsed["data"]) == 1

        ticket_data = parsed["data"][0]
        assert ticket_data["formatted_id"] == "US12345"
        assert ticket_data["name"] == "User login feature"
        assert ticket_data["ticket_type"] == "UserStory"
        assert ticket_data["state"] == "In-Progress"
        assert ticket_data["owner"] == "John Doe"
        assert ticket_data["points"] == 5

    def test_format_multiple_tickets(self, formatter, sample_tickets):
        """Test formatting multiple tickets."""
        result = CLIResult(success=True, data=sample_tickets)
        output = formatter.format_tickets(result)
        parsed = json.loads(output)

        assert parsed["success"] is True
        assert len(parsed["data"]) == 2

        ids = [t["formatted_id"] for t in parsed["data"]]
        assert "US12345" in ids
        assert "DE67890" in ids

    def test_format_includes_all_fields(self, formatter, sample_tickets):
        """Test that JSON includes all fields regardless of fields parameter."""
        result = CLIResult(success=True, data=[sample_tickets[0]])
        # Even with limited fields, JSON should include all
        output = formatter.format_tickets(result, fields=["formatted_id"])
        parsed = json.loads(output)

        ticket_data = parsed["data"][0]
        assert "formatted_id" in ticket_data
        assert "name" in ticket_data
        assert "ticket_type" in ticket_data
        assert "description" in ticket_data

    def test_format_error(self, formatter):
        """Test formatting error result."""
        result = CLIResult(success=False, data=None, error="Connection failed")
        output = formatter.format_tickets(result)
        parsed = json.loads(output)

        assert parsed["success"] is False
        assert parsed["error"] == "Connection failed"


class TestJSONFormatterComment:
    """Tests for formatting comment confirmations as JSON."""

    def test_format_comment_from_discussion(self, formatter, sample_discussion):
        """Test formatting comment from Discussion object."""
        result = CLIResult(success=True, data=sample_discussion)
        output = formatter.format_comment(result)
        parsed = json.loads(output)

        assert parsed["success"] is True
        assert parsed["data"]["artifact_id"] == "US12345"
        assert parsed["data"]["user"] == "John Doe"
        assert parsed["data"]["text"] == "Updated the implementation"
        assert "created_at" in parsed["data"]

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
        parsed = json.loads(output)

        assert parsed["success"] is True
        assert parsed["data"]["artifact_id"] == "US12345"

    def test_format_comment_error(self, formatter):
        """Test formatting comment error."""
        result = CLIResult(success=False, data=None, error="Ticket not found")
        output = formatter.format_comment(result)
        parsed = json.loads(output)

        assert parsed["success"] is False
        assert parsed["error"] == "Ticket not found"


class TestJSONFormatterError:
    """Tests for error formatting."""

    def test_format_error_structure(self, formatter):
        """Test error output structure."""
        result = CLIResult(success=False, data=None, error="API error occurred")
        output = formatter.format_error(result)
        parsed = json.loads(output)

        assert parsed["success"] is False
        assert parsed["data"] is None
        assert parsed["error"] == "API error occurred"


class TestJSONValidity:
    """Tests to ensure JSON output is always valid."""

    def test_output_is_valid_json(self, formatter, sample_tickets):
        """Test that output is always valid JSON."""
        result = CLIResult(success=True, data=sample_tickets)
        output = formatter.format_tickets(result)

        # Should not raise
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_special_characters_escaped(self, formatter):
        """Test that special characters are properly escaped."""
        ticket = Ticket(
            formatted_id="US1",
            name='Test with "quotes" and\nnewlines',
            ticket_type="UserStory",
            state="Open",
            description="Has <html> tags & special chars",
        )
        result = CLIResult(success=True, data=[ticket])
        output = formatter.format_tickets(result)

        # Should not raise
        parsed = json.loads(output)
        assert '"quotes"' in parsed["data"][0]["name"]
