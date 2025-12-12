"""Tests for the TicketDetail widget."""

from rally_tui.app import RallyTUI
from rally_tui.widgets import TicketDetail


class TestTicketDetailWidget:
    """Tests for TicketDetail widget behavior.

    Note: Tickets are sorted by most recent (highest ID first):
    - US1237, US1236, US1235, US1234, TC101, TA789, DE457, DE456
    """

    async def test_initial_state_shows_first_ticket(self) -> None:
        """Detail panel should show first ticket on mount (sorted by most recent)."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            # First ticket after sorting by most recent is US1237
            assert detail.ticket.formatted_id == "US1237"

    async def test_detail_updates_on_navigation(self) -> None:
        """Detail panel should update when navigating list."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)

            # Move to second item (US1236)
            await pilot.press("j")
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "US1236"

    async def test_detail_shows_ticket_name(self) -> None:
        """Detail panel should display ticket name in header."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            header = app.query_one("#detail-header")
            rendered = str(header.render())
            # First ticket is US1237 (Implement dark mode toggle)
            assert "Implement dark mode toggle" in rendered

    async def test_detail_shows_ticket_state(self) -> None:
        """Detail panel should display ticket state."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            # First ticket is US1237 with state "Defined"
            assert "Defined" in rendered

    async def test_detail_shows_owner(self) -> None:
        """Detail panel should display owner name."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to US1236 which has owner Alice Chen (index 1)
            await pilot.press("j")

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Alice Chen" in rendered

    async def test_detail_shows_unassigned_for_no_owner(self) -> None:
        """Detail panel should show 'Unassigned' when owner is None."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            # First ticket US1237 has no owner
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
            # First ticket is US1237 about dark mode
            assert "switch between light and dark themes" in rendered

    async def test_detail_shows_iteration(self) -> None:
        """Detail panel should display iteration name."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to US1235 which is in Sprint 6 (index 2)
            await pilot.press("j")
            await pilot.press("j")

            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Sprint 6" in rendered

    async def test_detail_shows_points(self) -> None:
        """Detail panel should display story points."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            # First ticket US1237 has 8 points
            assert "Points: 8" in rendered

    async def test_detail_shows_unscheduled_for_no_iteration(self) -> None:
        """Detail panel should show 'Unscheduled' when iteration is None."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            # First ticket US1237 has no iteration (Backlog)
            metadata = app.query_one("#detail-metadata")
            rendered = str(metadata.render())
            assert "Unscheduled" in rendered

    async def test_detail_shows_dash_for_no_points(self) -> None:
        """Detail panel should show '—' when points is None."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to TA789 which has no points (index 5)
            for _ in range(5):
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
            # First ticket is US1237
            assert "US1237" in rendered

    async def test_detail_navigation_to_defect(self) -> None:
        """Detail panel should update correctly when navigating to defect."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to DE457 (index 5 in CREATED sort order)
            for _ in range(5):
                await pilot.press("j")

            detail = app.query_one(TicketDetail)
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "DE457"
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
            # First ticket is US1237 with notes about design spec
            await pilot.press("n")

            content = app.query_one("#detail-description")
            rendered = str(content.render())
            # US1237 has notes: "Design spec: Toggle should persist across sessions..."
            assert "Design spec" in rendered or "Toggle should persist" in rendered

    async def test_empty_notes_shows_message(self) -> None:
        """Empty notes should show 'No notes available' message."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to US1236 (index 1) which has empty notes
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
