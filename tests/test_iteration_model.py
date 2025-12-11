"""Tests for the Iteration model."""

from datetime import date

import pytest

from rally_tui.models import Iteration


class TestIterationCreation:
    """Tests for Iteration dataclass creation."""

    def test_create_iteration(self) -> None:
        """Can create an iteration with required fields."""
        iteration = Iteration(
            object_id="12345",
            name="Sprint 1",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
        )
        assert iteration.name == "Sprint 1"
        assert iteration.start_date == date(2024, 12, 2)
        assert iteration.end_date == date(2024, 12, 15)
        assert iteration.state == "Planning"  # default

    def test_create_iteration_with_state(self) -> None:
        """Can create an iteration with custom state."""
        iteration = Iteration(
            object_id="12345",
            name="Sprint 1",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
            state="Committed",
        )
        assert iteration.state == "Committed"

    def test_iteration_is_frozen(self) -> None:
        """Iteration should be immutable."""
        iteration = Iteration(
            object_id="12345",
            name="Sprint 1",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
        )
        with pytest.raises(AttributeError):
            iteration.name = "Sprint 2"  # type: ignore


class TestIterationIsCurrent:
    """Tests for is_current property."""

    def test_current_iteration(self) -> None:
        """Iteration containing today is current."""
        today = date.today()
        iteration = Iteration(
            object_id="12345",
            name="Current Sprint",
            start_date=today,
            end_date=today,
        )
        assert iteration.is_current is True

    def test_past_iteration(self) -> None:
        """Iteration in the past is not current."""
        iteration = Iteration(
            object_id="12345",
            name="Past Sprint",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 14),
        )
        assert iteration.is_current is False

    def test_future_iteration(self) -> None:
        """Iteration in the future is not current."""
        iteration = Iteration(
            object_id="12345",
            name="Future Sprint",
            start_date=date(2099, 1, 1),
            end_date=date(2099, 1, 14),
        )
        assert iteration.is_current is False


class TestIterationFormattedDates:
    """Tests for formatted_dates property."""

    def test_formatted_dates(self) -> None:
        """Dates should be formatted as 'Mon DD - Mon DD'."""
        iteration = Iteration(
            object_id="12345",
            name="Sprint 1",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
        )
        assert iteration.formatted_dates == "Dec 02 - Dec 15"

    def test_formatted_dates_cross_month(self) -> None:
        """Dates crossing months should show both months."""
        iteration = Iteration(
            object_id="12345",
            name="Sprint 1",
            start_date=date(2024, 11, 25),
            end_date=date(2024, 12, 8),
        )
        assert iteration.formatted_dates == "Nov 25 - Dec 08"


class TestIterationDisplayName:
    """Tests for display_name property."""

    def test_display_name(self) -> None:
        """Display name should include name and dates."""
        iteration = Iteration(
            object_id="12345",
            name="Sprint 1",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
        )
        assert iteration.display_name == "Sprint 1 (Dec 02 - Dec 15)"


class TestIterationShortName:
    """Tests for short_name property."""

    def test_short_name_with_sprint_pattern(self) -> None:
        """Should extract 'Sprint N' from long name."""
        iteration = Iteration(
            object_id="12345",
            name="FY26-Q1 PI Sprint 3",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
        )
        assert iteration.short_name == "Sprint 3"

    def test_short_name_simple(self) -> None:
        """Simple sprint name should return as-is."""
        iteration = Iteration(
            object_id="12345",
            name="Sprint 3",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
        )
        assert iteration.short_name == "Sprint 3"

    def test_short_name_no_sprint(self) -> None:
        """Name without 'Sprint' should return last part."""
        iteration = Iteration(
            object_id="12345",
            name="PI 2024-Q4 Iteration 5",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
        )
        assert iteration.short_name == "5"

    def test_short_name_single_word(self) -> None:
        """Single word name should return full name."""
        iteration = Iteration(
            object_id="12345",
            name="Backlog",
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 15),
        )
        assert iteration.short_name == "Backlog"
