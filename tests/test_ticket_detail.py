"""Tests for the TicketDetail widget."""

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
        async with app.run_test():
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
        async with app.run_test():
            header = app.query_one("#detail-header")
            rendered = str(header.render())
            # First ticket is US1235 (Password reset functionality)
            assert "Password reset functionality" in rendered

    async def test_detail_shows_ticket_state(self) -> None:
        """Detail panel should display ticket state."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            # First ticket is US1235 with state "Defined"
            assert "Defined" in rendered

    async def test_detail_shows_owner(self) -> None:
        """Detail panel should display owner name."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
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
        async with app.run_test():
            description = app.query_one("#detail-description")
            rendered = str(description.render())
            # First ticket is US1235 about password reset
            assert "reset my password" in rendered

    async def test_detail_shows_iteration(self) -> None:
        """Detail panel should display iteration name."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            # First ticket US1235 is in Sprint 6
            assert "Sprint 6" in rendered

    async def test_detail_shows_points(self) -> None:
        """Detail panel should display story points."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
            ticket_list = app.query_one("#ticket-list")
            assert ticket_list.border_title == "Tickets"

    async def test_ticket_detail_has_title(self) -> None:
        """Ticket detail panel should have 'Details' as border title."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            ticket_detail = app.query_one("#ticket-detail")
            assert ticket_detail.border_title == "Details"


class TestTicketDetailNotesToggle:
    """Tests for description/notes toggle in ticket detail."""

    async def test_default_view_is_description(self) -> None:
        """Detail panel should show description by default."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            detail = app.query_one(TicketDetail)
            assert detail.content_view == "description"
            label = app.query_one("#detail-description-label")
            assert "Description:" in str(label.render())

    async def test_toggle_shows_notes(self) -> None:
        """Pressing 'n' should toggle to notes view."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)

            # Press n to toggle to notes
            await pilot.press("n")

            assert detail.content_view == "notes"
            label = app.query_one("#detail-description-label")
            assert "Notes:" in str(label.render())

    async def test_toggle_back_to_description(self) -> None:
        """Pressing 'n' again should toggle back to description."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)

            # Toggle to notes then back
            await pilot.press("n")
            await pilot.press("n")

            assert detail.content_view == "description"
            label = app.query_one("#detail-description-label")
            assert "Description:" in str(label.render())

    async def test_notes_content_displayed(self) -> None:
        """Notes view should display ticket notes."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # First ticket is US1235 with notes about reset tokens
            await pilot.press("n")

            content = app.query_one("#detail-description")
            rendered = str(content.render())
            # US1235 has notes: "Implementation notes: Reset tokens..."
            assert "Reset tokens" in rendered or "Implementation notes" in rendered

    async def test_empty_notes_shows_message(self) -> None:
        """Empty notes should show 'No notes available' message."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to US1236 (index 7, Completed state) which has empty notes
            for _ in range(7):
                await pilot.press("j")

            # Toggle to notes
            await pilot.press("n")

            content = app.query_one("#detail-description")
            rendered = str(content.render())
            assert "No notes available" in rendered

    async def test_toggle_method_works(self) -> None:
        """toggle_content_view method should work correctly."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            detail = app.query_one(TicketDetail)

            assert detail.content_view == "description"
            detail.toggle_content_view()
            assert detail.content_view == "notes"
            detail.toggle_content_view()
            assert detail.content_view == "description"


class TestTicketDetailMarkupEscape:
    """Tests for Rich markup escaping in ticket detail."""

    async def test_content_with_brackets_is_escaped(self) -> None:
        """Content with brackets should be escaped to prevent Rich markup errors."""
        from rally_tui.models import Ticket

        app = RallyTUI(show_splash=False)
        async with app.run_test():
            detail = app.query_one(TicketDetail)

            # Set ticket with content containing Rich markup-like syntax
            ticket = Ticket(
                formatted_id="US9999",
                name="Test ticket",
                description="Install with [signed-by=/etc/apt/keyrings/docker.asc]",
                state="Defined",
                owner="Test User",
                ticket_type="HierarchicalRequirement",
            )
            detail.ticket = ticket

            # Should not raise MarkupError
            content = app.query_one("#detail-description")
            rendered = str(content.render())
            assert "signed-by" in rendered

    async def test_content_with_dollar_parens_is_escaped(self) -> None:
        """Content with $(command) syntax should be escaped."""
        from rally_tui.models import Ticket

        app = RallyTUI(show_splash=False)
        async with app.run_test():
            detail = app.query_one(TicketDetail)

            # Set ticket with shell-style command substitution
            ticket = Ticket(
                formatted_id="US9999",
                name="Test ticket",
                description="Run $(dpkg --print-architecture) to get arch",
                state="Defined",
                owner="Test User",
                ticket_type="HierarchicalRequirement",
            )
            detail.ticket = ticket

            # Should not raise MarkupError
            content = app.query_one("#detail-description")
            rendered = str(content.render())
            assert "dpkg" in rendered

    async def test_notes_with_markup_chars_is_escaped(self) -> None:
        """Notes with Rich markup-like characters should be escaped."""
        from rally_tui.models import Ticket

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()  # Allow initial ticket to load
            detail = app.query_one(TicketDetail)

            # Set ticket with notes containing markup-like syntax
            ticket = Ticket(
                formatted_id="US9999",
                name="Test ticket",
                description="Normal description",
                notes="Add [arch=$(dpkg)] to /etc/apt",
                state="Defined",
                owner="Test User",
                ticket_type="HierarchicalRequirement",
            )
            detail.ticket = ticket
            await pilot.pause()  # Allow UI to update with new ticket

            # Toggle to notes view
            await pilot.press("n")

            # Should not raise MarkupError
            content = app.query_one("#detail-description")
            rendered = str(content.render())
            assert "arch=" in rendered or "dpkg" in rendered
