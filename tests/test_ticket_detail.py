"""Tests for the TicketDetail widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.widgets import TicketDetail


class TestTicketDetailWidget:
    """Tests for TicketDetail widget behavior."""

    async def test_initial_state_shows_first_ticket(self) -> None:
        """Detail panel should show first ticket on mount."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "US1234"

    async def test_detail_updates_on_navigation(self) -> None:
        """Detail panel should update when navigating list."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)

            # Move to second item
            await pilot.press("j")
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "US1235"

    async def test_detail_shows_ticket_name(self) -> None:
        """Detail panel should display ticket name in header."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            header = app.query_one("#detail-header")
            rendered = str(header.render())
            assert "User login feature" in rendered

    async def test_detail_shows_ticket_state(self) -> None:
        """Detail panel should display ticket state."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "In Progress" in rendered

    async def test_detail_shows_owner(self) -> None:
        """Detail panel should display owner name."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "John Smith" in rendered

    async def test_detail_shows_unassigned_for_no_owner(self) -> None:
        """Detail panel should show 'Unassigned' when owner is None."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            # Navigate to DE457 which has no owner (6th item, index 5)
            for _ in range(5):
                await pilot.press("j")

            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            assert detail.ticket.owner is None

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Unassigned" in rendered

    async def test_detail_shows_description(self) -> None:
        """Detail panel should display ticket description."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            description = app.query_one("#detail-description")
            rendered = str(description.render())
            assert "email and password" in rendered

    async def test_detail_shows_iteration(self) -> None:
        """Detail panel should display iteration name."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Sprint 5" in rendered

    async def test_detail_shows_points(self) -> None:
        """Detail panel should display story points."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Points: 3" in rendered

    async def test_detail_shows_unscheduled_for_no_iteration(self) -> None:
        """Detail panel should show 'Unscheduled' when iteration is None."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            # Navigate to DE457 which has no iteration (6th item, index 5)
            for _ in range(5):
                await pilot.press("j")

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Unscheduled" in rendered

    async def test_detail_shows_dash_for_no_points(self) -> None:
        """Detail panel should show '—' when points is None."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            # Navigate to TA789 which has no points (5th item, index 4)
            for _ in range(4):
                await pilot.press("j")

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Points: —" in rendered

    async def test_detail_shows_formatted_id_in_header(self) -> None:
        """Detail panel header should include formatted ID."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            header = app.query_one("#detail-header")
            rendered = str(header.render())
            assert "US1234" in rendered

    async def test_detail_navigation_to_defect(self) -> None:
        """Detail panel should update correctly when navigating to defect."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            # Navigate to first defect DE456 (3rd item, index 2)
            await pilot.press("j")
            await pilot.press("j")

            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "DE456"
            assert detail.ticket.ticket_type == "Defect"
