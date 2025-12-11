"""Tests for the Discussion model."""

from datetime import datetime

import pytest

from rally_tui.models import Discussion


class TestDiscussion:
    """Tests for Discussion dataclass."""

    def test_discussion_creation(self) -> None:
        """Discussion should be created with all required fields."""
        discussion = Discussion(
            object_id="12345",
            text="This is a comment",
            user="John Smith",
            created_at=datetime(2024, 1, 15, 10, 30),
            artifact_id="US1234",
        )
        assert discussion.object_id == "12345"
        assert discussion.text == "This is a comment"
        assert discussion.user == "John Smith"
        assert discussion.artifact_id == "US1234"

    def test_discussion_immutability(self) -> None:
        """Discussion should be immutable (frozen dataclass)."""
        discussion = Discussion(
            object_id="12345",
            text="Original text",
            user="John Smith",
            created_at=datetime(2024, 1, 15, 10, 30),
            artifact_id="US1234",
        )
        with pytest.raises(AttributeError):
            discussion.text = "Modified text"  # type: ignore[misc]

    def test_discussion_equality(self) -> None:
        """Discussions with same values should be equal."""
        dt = datetime(2024, 1, 15, 10, 30)
        d1 = Discussion(
            object_id="12345",
            text="Comment",
            user="John",
            created_at=dt,
            artifact_id="US1234",
        )
        d2 = Discussion(
            object_id="12345",
            text="Comment",
            user="John",
            created_at=dt,
            artifact_id="US1234",
        )
        assert d1 == d2

    def test_discussion_inequality(self) -> None:
        """Discussions with different values should not be equal."""
        dt = datetime(2024, 1, 15, 10, 30)
        d1 = Discussion(
            object_id="12345",
            text="Comment 1",
            user="John",
            created_at=dt,
            artifact_id="US1234",
        )
        d2 = Discussion(
            object_id="12346",
            text="Comment 2",
            user="Jane",
            created_at=dt,
            artifact_id="US1234",
        )
        assert d1 != d2


class TestDiscussionFormattedDate:
    """Tests for formatted_date property."""

    def test_formatted_date_morning(self) -> None:
        """Morning time should show AM."""
        discussion = Discussion(
            object_id="1",
            text="Test",
            user="User",
            created_at=datetime(2024, 1, 15, 10, 30),
            artifact_id="US1",
        )
        assert discussion.formatted_date == "Jan 15, 2024 10:30 AM"

    def test_formatted_date_afternoon(self) -> None:
        """Afternoon time should show PM."""
        discussion = Discussion(
            object_id="1",
            text="Test",
            user="User",
            created_at=datetime(2024, 1, 15, 14, 45),
            artifact_id="US1",
        )
        assert discussion.formatted_date == "Jan 15, 2024 02:45 PM"

    def test_formatted_date_midnight(self) -> None:
        """Midnight should show 12:00 AM."""
        discussion = Discussion(
            object_id="1",
            text="Test",
            user="User",
            created_at=datetime(2024, 1, 15, 0, 0),
            artifact_id="US1",
        )
        assert discussion.formatted_date == "Jan 15, 2024 12:00 AM"

    def test_formatted_date_noon(self) -> None:
        """Noon should show 12:00 PM."""
        discussion = Discussion(
            object_id="1",
            text="Test",
            user="User",
            created_at=datetime(2024, 1, 15, 12, 0),
            artifact_id="US1",
        )
        assert discussion.formatted_date == "Jan 15, 2024 12:00 PM"


class TestDiscussionDisplayHeader:
    """Tests for display_header property."""

    def test_display_header_format(self) -> None:
        """Display header should show 'User - Date'."""
        discussion = Discussion(
            object_id="1",
            text="Test",
            user="John Smith",
            created_at=datetime(2024, 1, 15, 10, 30),
            artifact_id="US1",
        )
        assert discussion.display_header == "John Smith - Jan 15, 2024 10:30 AM"

    def test_display_header_different_user(self) -> None:
        """Display header should reflect the user name."""
        discussion = Discussion(
            object_id="1",
            text="Test",
            user="Jane Doe",
            created_at=datetime(2024, 6, 20, 15, 0),
            artifact_id="US1",
        )
        assert discussion.display_header == "Jane Doe - Jun 20, 2024 03:00 PM"
