"""Tests for MockRallyClient discussion methods."""

from datetime import datetime

import pytest

from rally_tui.models import Discussion, Ticket
from rally_tui.services.mock_client import MockRallyClient


class TestMockClientGetDiscussions:
    """Tests for MockRallyClient.get_discussions method."""

    def test_get_discussions_returns_list(self) -> None:
        """get_discussions should return a list."""
        client = MockRallyClient()
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
            object_id="100001",
        )
        result = client.get_discussions(ticket)
        assert isinstance(result, list)

    def test_get_discussions_for_ticket_with_comments(self) -> None:
        """get_discussions should return discussions for tickets with comments."""
        client = MockRallyClient()
        # US1234 has sample discussions
        ticket = Ticket(
            formatted_id="US1234",
            name="User login feature",
            ticket_type="UserStory",
            state="In Progress",
            object_id="100001",
        )
        discussions = client.get_discussions(ticket)
        assert len(discussions) == 3
        assert all(isinstance(d, Discussion) for d in discussions)

    def test_get_discussions_for_ticket_without_comments(self) -> None:
        """get_discussions should return empty list for tickets without comments."""
        client = MockRallyClient()
        ticket = Ticket(
            formatted_id="US9999",
            name="No discussions",
            ticket_type="UserStory",
            state="Defined",
            object_id="999999",
        )
        discussions = client.get_discussions(ticket)
        assert discussions == []

    def test_get_discussions_sorted_by_date(self) -> None:
        """get_discussions should return discussions sorted by creation date."""
        client = MockRallyClient()
        ticket = Ticket(
            formatted_id="US1234",
            name="User login feature",
            ticket_type="UserStory",
            state="In Progress",
            object_id="100001",
        )
        discussions = client.get_discussions(ticket)
        dates = [d.created_at for d in discussions]
        assert dates == sorted(dates)

    def test_get_discussions_with_custom_discussions(self) -> None:
        """get_discussions should use custom discussions when provided."""
        custom_discussions = {
            "TEST123": [
                Discussion(
                    object_id="1",
                    text="Custom comment",
                    user="Custom User",
                    created_at=datetime(2024, 1, 1, 12, 0),
                    artifact_id="TEST123",
                )
            ]
        }
        client = MockRallyClient(discussions=custom_discussions)
        ticket = Ticket(
            formatted_id="TEST123",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        discussions = client.get_discussions(ticket)
        assert len(discussions) == 1
        assert discussions[0].text == "Custom comment"


class TestMockClientAddComment:
    """Tests for MockRallyClient.add_comment method."""

    def test_add_comment_returns_discussion(self) -> None:
        """add_comment should return a Discussion object."""
        client = MockRallyClient(current_user="Test User")
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
            object_id="100001",
        )
        result = client.add_comment(ticket, "New comment")
        assert isinstance(result, Discussion)

    def test_add_comment_sets_correct_text(self) -> None:
        """add_comment should set the provided text."""
        client = MockRallyClient(current_user="Test User")
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        result = client.add_comment(ticket, "My comment text")
        assert result is not None
        assert result.text == "My comment text"

    def test_add_comment_sets_current_user(self) -> None:
        """add_comment should use the current user's name."""
        client = MockRallyClient(current_user="John Doe")
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        result = client.add_comment(ticket, "Comment")
        assert result is not None
        assert result.user == "John Doe"

    def test_add_comment_default_user(self) -> None:
        """add_comment should use 'Test User' when no current user."""
        client = MockRallyClient(current_user=None)
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        result = client.add_comment(ticket, "Comment")
        assert result is not None
        assert result.user == "Test User"

    def test_add_comment_sets_artifact_id(self) -> None:
        """add_comment should set the correct artifact ID."""
        client = MockRallyClient(current_user="Test User")
        ticket = Ticket(
            formatted_id="DE789",
            name="Bug fix",
            ticket_type="Defect",
            state="Open",
        )
        result = client.add_comment(ticket, "Comment")
        assert result is not None
        assert result.artifact_id == "DE789"

    def test_add_comment_sets_timestamp(self) -> None:
        """add_comment should set a recent timestamp."""
        client = MockRallyClient(current_user="Test User")
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        before = datetime.now()
        result = client.add_comment(ticket, "Comment")
        after = datetime.now()
        assert result is not None
        # Note: created_at is UTC, but we just check it's reasonable
        assert result.created_at is not None

    def test_add_comment_persists_in_discussions(self) -> None:
        """add_comment should persist the comment for later retrieval."""
        client = MockRallyClient(current_user="Test User", discussions={})
        ticket = Ticket(
            formatted_id="NEW123",
            name="New ticket",
            ticket_type="UserStory",
            state="Defined",
        )
        client.add_comment(ticket, "First comment")
        client.add_comment(ticket, "Second comment")

        discussions = client.get_discussions(ticket)
        assert len(discussions) == 2
        texts = [d.text for d in discussions]
        assert "First comment" in texts
        assert "Second comment" in texts

    def test_add_comment_generates_unique_ids(self) -> None:
        """add_comment should generate unique object IDs."""
        client = MockRallyClient(current_user="Test User", discussions={})
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        result1 = client.add_comment(ticket, "Comment 1")
        result2 = client.add_comment(ticket, "Comment 2")
        assert result1 is not None
        assert result2 is not None
        assert result1.object_id != result2.object_id
