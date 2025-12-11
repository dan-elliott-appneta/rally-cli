"""Tests for the TicketDetail widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.widgets import TicketDetail


class TestTicketDetailWidget:
    """Tests for TicketDetail widget behavior.

    Note: Tickets are sorted by state order:
    - Defined (US1235, TC101, US1237) - indices 0, 1, 2
    - Open (DE456, DE457) - indices 3, 4
    - In Progress (US1234, TA789) - indices 5, 6
    - Completed (US1236) - index 7
    """

    async def test_initial_state_shows_first_ticket(self) -> None:
        """Detail panel should show first ticket on mount (sorted by state)."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            # First ticket after sorting by state is US1235 (Defined)
            assert detail.ticket.formatted_id == "US1235"

    async def test_detail_updates_on_navigation(self) -> None:
        """Detail panel should update when navigating list."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)

            # Move to second item (TC101)
            await pilot.press("j")
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "TC101"

    async def test_detail_shows_ticket_name(self) -> None:
        """Detail panel should display ticket name in header."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            header = app.query_one("#detail-header")
            rendered = str(header.render())
            # First ticket is US1235 (Password reset functionality)
            assert "Password reset functionality" in rendered

    async def test_detail_shows_ticket_state(self) -> None:
        """Detail panel should display ticket state."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            # First ticket is US1235 with state "Defined"
            assert "Defined" in rendered

    async def test_detail_shows_owner(self) -> None:
        """Detail panel should display owner name."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            # First ticket US1235 has owner Jane Doe
            assert "Jane Doe" in rendered

    async def test_detail_shows_unassigned_for_no_owner(self) -> None:
        """Detail panel should show 'Unassigned' when owner is None."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to DE457 which has no owner (index 4)
            for _ in range(4):
                await pilot.press("j")

            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            assert detail.ticket.owner is None

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Unassigned" in rendered

    async def test_detail_shows_description(self) -> None:
        """Detail panel should display ticket description."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            description = app.query_one("#detail-description")
            rendered = str(description.render())
            # First ticket is US1235 about password reset
            assert "reset my password" in rendered

    async def test_detail_shows_iteration(self) -> None:
        """Detail panel should display iteration name."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            # First ticket US1235 is in Sprint 6
            assert "Sprint 6" in rendered

    async def test_detail_shows_points(self) -> None:
        """Detail panel should display story points."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            # First ticket US1235 has 5 points
            assert "Points: 5" in rendered

    async def test_detail_shows_unscheduled_for_no_iteration(self) -> None:
        """Detail panel should show 'Unscheduled' when iteration is None."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to DE457 which has no iteration (index 4)
            for _ in range(4):
                await pilot.press("j")

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Unscheduled" in rendered

    async def test_detail_shows_dash_for_no_points(self) -> None:
        """Detail panel should show '—' when points is None."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to TA789 which has no points (index 6)
            for _ in range(6):
                await pilot.press("j")

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Points: —" in rendered

    async def test_detail_shows_formatted_id_in_header(self) -> None:
        """Detail panel header should include formatted ID."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            header = app.query_one("#detail-header")
            rendered = str(header.render())
            # First ticket is US1235
            assert "US1235" in rendered

    async def test_detail_navigation_to_defect(self) -> None:
        """Detail panel should update correctly when navigating to defect."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to first defect DE456 (index 3)
            for _ in range(3):
                await pilot.press("j")

            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "DE456"
            assert detail.ticket.ticket_type == "Defect"


class TestPanelTitles:
    """Tests for panel border titles."""

    async def test_ticket_list_has_title(self) -> None:
        """Ticket list panel should have 'Tickets' as border title."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one("#ticket-list")
            assert ticket_list.border_title == "Tickets"

    async def test_ticket_detail_has_title(self) -> None:
        """Ticket detail panel should have 'Details' as border title."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            ticket_detail = app.query_one("#ticket-detail")
            assert ticket_detail.border_title == "Details"
