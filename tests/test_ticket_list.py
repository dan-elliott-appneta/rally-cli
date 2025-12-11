"""Tests for the TicketList widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.widgets import TicketList


class TestTicketListWidget:
    """Tests for TicketList widget behavior."""

    async def test_initial_render(self) -> None:
        """List should render all provided tickets."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            items = list(app.query("TicketListItem"))
            assert len(items) == 8  # SAMPLE_TICKETS has 8 items

    async def test_first_item_highlighted_by_default(self) -> None:
        """First item should be highlighted on start."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()  # Allow UI to settle
            ticket_list = app.query_one(TicketList)
            assert ticket_list.index == 0

    async def test_keyboard_navigation_j(self) -> None:
        """Pressing j should move selection down."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()  # Allow UI to settle
            ticket_list = app.query_one(TicketList)
            assert ticket_list.index == 0

            await pilot.press("j")
            assert ticket_list.index == 1

    async def test_keyboard_navigation_k(self) -> None:
        """Pressing k should move selection up."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()  # Allow UI to settle
            ticket_list = app.query_one(TicketList)

            await pilot.press("j", "j")
            assert ticket_list.index == 2

            await pilot.press("k")
            assert ticket_list.index == 1

    async def test_keyboard_navigation_down_arrow(self) -> None:
        """Down arrow should move selection down."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()  # Allow UI to settle
            ticket_list = app.query_one(TicketList)

            await pilot.press("down")
            assert ticket_list.index == 1

    async def test_keyboard_navigation_up_arrow(self) -> None:
        """Up arrow should move selection up."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()  # Allow UI to settle
            ticket_list = app.query_one(TicketList)

            await pilot.press("down", "down")
            await pilot.press("up")
            assert ticket_list.index == 1

    async def test_vim_go_to_top(self) -> None:
        """Pressing g should jump to first item."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()  # Allow UI to settle
            ticket_list = app.query_one(TicketList)

            await pilot.press("j", "j", "j")
            assert ticket_list.index == 3

            await pilot.press("g")
            assert ticket_list.index == 0

    async def test_vim_go_to_bottom(self) -> None:
        """Pressing G should jump to last item."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("G")
            assert ticket_list.index == 7  # Last of 8 items

    async def test_navigation_wraps_at_top(self) -> None:
        """Pressing k at top should stay at top."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()  # Allow UI to settle
            ticket_list = app.query_one(TicketList)
            assert ticket_list.index == 0

            await pilot.press("k")
            assert ticket_list.index == 0

    async def test_navigation_wraps_at_bottom(self) -> None:
        """Pressing j at bottom should stay at bottom."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("G")  # Go to bottom
            bottom_index = ticket_list.index

            await pilot.press("j")
            assert ticket_list.index == bottom_index

    async def test_quit_binding(self) -> None:
        """Pressing q should quit the app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.press("q")
            assert app._exit


class TestTicketListFilter:
    """Tests for TicketList filter functionality."""

    @pytest.fixture
    def sample_tickets(self) -> list[Ticket]:
        """Create sample tickets for filter tests."""
        return [
            Ticket(
                formatted_id="US1001",
                name="User login feature",
                ticket_type="UserStory",
                state="In Progress",
                owner="John Smith",
            ),
            Ticket(
                formatted_id="US1002",
                name="Password reset",
                ticket_type="UserStory",
                state="Defined",
                owner="Jane Doe",
            ),
            Ticket(
                formatted_id="DE501",
                name="Fix login bug",
                ticket_type="Defect",
                state="Open",
                owner="John Smith",
            ),
            Ticket(
                formatted_id="TA201",
                name="Write unit tests",
                ticket_type="Task",
                state="Completed",
                owner=None,
            ),
        ]

    async def test_filter_by_id(self, sample_tickets: list[Ticket]) -> None:
        """Filter should match ticket ID."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("US1001")
            assert ticket_list.filtered_count == 1
            assert ticket_list._tickets[0].formatted_id == "US1001"

    async def test_filter_by_name(self, sample_tickets: list[Ticket]) -> None:
        """Filter should match ticket name."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("login")
            assert ticket_list.filtered_count == 2  # "User login feature" and "Fix login bug"

    async def test_filter_by_owner(self, sample_tickets: list[Ticket]) -> None:
        """Filter should match owner name."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("john")
            assert ticket_list.filtered_count == 2  # Both John Smith tickets

    async def test_filter_by_state(self, sample_tickets: list[Ticket]) -> None:
        """Filter should match state."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("progress")
            assert ticket_list.filtered_count == 1

    async def test_filter_case_insensitive(self, sample_tickets: list[Ticket]) -> None:
        """Filter should be case-insensitive."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            ticket_list.filter_tickets("LOGIN")
            assert ticket_list.filtered_count == 2

            ticket_list.filter_tickets("Login")
            assert ticket_list.filtered_count == 2

            ticket_list.filter_tickets("login")
            assert ticket_list.filtered_count == 2

    async def test_filter_empty_shows_all(self, sample_tickets: list[Ticket]) -> None:
        """Empty filter should show all tickets."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("login")  # Apply filter first
            assert ticket_list.filtered_count == 2

            ticket_list.filter_tickets("")  # Clear filter
            assert ticket_list.filtered_count == 4

    async def test_clear_filter(self, sample_tickets: list[Ticket]) -> None:
        """clear_filter should restore all tickets."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            ticket_list.filter_tickets("DE501")
            assert ticket_list.filtered_count == 1

            ticket_list.clear_filter()
            assert ticket_list.filtered_count == 4
            assert ticket_list.filter_query == ""

    async def test_filter_no_match(self, sample_tickets: list[Ticket]) -> None:
        """Filter with no matches should show empty list."""
        from textual.app import App, ComposeResult

        # Use a simpler test app that doesn't have ticket highlight handler
        class FilterTestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield TicketList(sample_tickets, id="ticket-list")

        app = FilterTestApp()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("xyz123")
            assert ticket_list.filtered_count == 0

    async def test_filter_counts(self, sample_tickets: list[Ticket]) -> None:
        """filtered_count and total_count should be accurate."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            assert ticket_list.total_count == 4
            assert ticket_list.filtered_count == 4

            ticket_list.filter_tickets("US")
            assert ticket_list.total_count == 4
            assert ticket_list.filtered_count == 2

    async def test_filter_query_property(self, sample_tickets: list[Ticket]) -> None:
        """filter_query should return current query."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            assert ticket_list.filter_query == ""

            ticket_list.filter_tickets("test")
            assert ticket_list.filter_query == "test"

    async def test_filter_with_none_owner(self, sample_tickets: list[Ticket]) -> None:
        """Filter should handle None owner gracefully."""
        from textual.app import App, ComposeResult

        # Use a simpler test app that doesn't have ticket highlight handler
        class FilterTestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield TicketList(sample_tickets, id="ticket-list")

        app = FilterTestApp()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            # Should not crash when owner is None
            ticket_list.filter_tickets("none")
            assert ticket_list.filtered_count == 0  # "None" shouldn't match None value
