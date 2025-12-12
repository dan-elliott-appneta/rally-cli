"""Tests for the TicketList widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.widgets import SortMode, TicketList
from rally_tui.widgets.ticket_list import (
    sort_tickets,
    sort_tickets_by_created,
    sort_tickets_by_owner,
    sort_tickets_by_state,
)


class TestTicketListWidget:
    """Tests for TicketList widget behavior."""

    async def test_initial_render(self) -> None:
        """List should render all provided tickets."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            app.query_one(TicketList)
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
                state="In-Progress",
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
        async with app.run_test():
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("US1001")
            assert ticket_list.filtered_count == 1
            assert ticket_list._tickets[0].formatted_id == "US1001"

    async def test_filter_by_name(self, sample_tickets: list[Ticket]) -> None:
        """Filter should match ticket name."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test():
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("login")
            assert ticket_list.filtered_count == 2  # "User login feature" and "Fix login bug"

    async def test_filter_by_owner(self, sample_tickets: list[Ticket]) -> None:
        """Filter should match owner name."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test():
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("john")
            assert ticket_list.filtered_count == 2  # Both John Smith tickets

    async def test_filter_by_state(self, sample_tickets: list[Ticket]) -> None:
        """Filter should match state."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test():
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("progress")
            assert ticket_list.filtered_count == 1

    async def test_filter_case_insensitive(self, sample_tickets: list[Ticket]) -> None:
        """Filter should be case-insensitive."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
            ticket_list = app.query_one(TicketList)
            ticket_list.filter_tickets("xyz123")
            assert ticket_list.filtered_count == 0

    async def test_filter_counts(self, sample_tickets: list[Ticket]) -> None:
        """filtered_count and total_count should be accurate."""
        from rally_tui.services import MockRallyClient

        client = MockRallyClient(tickets=sample_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
            ticket_list = app.query_one(TicketList)
            # Should not crash when owner is None
            ticket_list.filter_tickets("none")
            assert ticket_list.filtered_count == 0  # "None" shouldn't match None value


class TestTicketListSorting:
    """Tests for ticket list sorting functionality."""

    @pytest.fixture
    def sort_tickets_fixture(self) -> list[Ticket]:
        """Create sample tickets for sort tests."""
        return [
            Ticket(
                formatted_id="US1005",
                name="Fifth story",
                ticket_type="HierarchicalRequirement",
                state="In-Progress",
                owner="Alice",
            ),
            Ticket(
                formatted_id="US1001",
                name="First story",
                ticket_type="HierarchicalRequirement",
                state="Defined",
                owner="Charlie",
            ),
            Ticket(
                formatted_id="US1003",
                name="Third story",
                ticket_type="HierarchicalRequirement",
                state="Completed",
                owner=None,
            ),
            Ticket(
                formatted_id="DE502",
                name="Second defect",
                ticket_type="Defect",
                state="Open",
                owner="Bob",
            ),
            Ticket(
                formatted_id="US1002",
                name="Second story",
                ticket_type="HierarchicalRequirement",
                state="Defined",
                owner=None,
            ),
        ]

    def test_sort_by_state(self, sort_tickets_fixture: list[Ticket]) -> None:
        """Sorting by state should order by workflow."""
        sorted_list = sort_tickets_by_state(sort_tickets_fixture)
        states = [t.state for t in sorted_list]
        # Defined < Open < In-Progress < Completed
        assert states == ["Defined", "Defined", "Open", "In-Progress", "Completed"]

    def test_sort_by_created(self, sort_tickets_fixture: list[Ticket]) -> None:
        """Sorting by created should order by ID (newest first)."""
        sorted_list = sort_tickets_by_created(sort_tickets_fixture)
        ids = [t.formatted_id for t in sorted_list]
        # Higher ID = newer, should be first
        assert ids == ["US1005", "US1003", "US1002", "US1001", "DE502"]

    def test_sort_by_owner(self, sort_tickets_fixture: list[Ticket]) -> None:
        """Sorting by owner should put unassigned first, then alphabetical."""
        sorted_list = sort_tickets_by_owner(sort_tickets_fixture)
        owners = [t.owner for t in sorted_list]
        # None first (2 tickets), then alphabetical
        assert owners == [None, None, "Alice", "Bob", "Charlie"]

    def test_sort_tickets_function_state(self, sort_tickets_fixture: list[Ticket]) -> None:
        """sort_tickets with STATE mode should use state sorting."""
        sorted_list = sort_tickets(sort_tickets_fixture, SortMode.STATE)
        states = [t.state for t in sorted_list]
        assert states == ["Defined", "Defined", "Open", "In-Progress", "Completed"]

    def test_sort_tickets_function_created(self, sort_tickets_fixture: list[Ticket]) -> None:
        """sort_tickets with CREATED mode should use created sorting."""
        sorted_list = sort_tickets(sort_tickets_fixture, SortMode.CREATED)
        ids = [t.formatted_id for t in sorted_list]
        assert ids == ["US1005", "US1003", "US1002", "US1001", "DE502"]

    def test_sort_tickets_function_owner(self, sort_tickets_fixture: list[Ticket]) -> None:
        """sort_tickets with OWNER mode should use owner sorting."""
        sorted_list = sort_tickets(sort_tickets_fixture, SortMode.OWNER)
        owners = [t.owner for t in sorted_list]
        assert owners == [None, None, "Alice", "Bob", "Charlie"]

    def test_default_sort_mode_is_state(self) -> None:
        """TicketList should default to STATE sort mode."""
        ticket_list = TicketList([])
        assert ticket_list.sort_mode == SortMode.STATE

    def test_custom_sort_mode_on_init(self, sort_tickets_fixture: list[Ticket]) -> None:
        """TicketList should accept custom sort mode on init."""
        ticket_list = TicketList(sort_tickets_fixture, sort_mode=SortMode.OWNER)
        assert ticket_list.sort_mode == SortMode.OWNER

    async def test_sort_mode_change_in_app(self) -> None:
        """Pressing 'o' should cycle through sort modes."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            assert ticket_list.sort_mode == SortMode.STATE

            # First press: STATE -> CREATED
            await pilot.press("o")
            assert ticket_list.sort_mode == SortMode.CREATED

            # Second press: CREATED -> OWNER
            await pilot.press("o")
            assert ticket_list.sort_mode == SortMode.OWNER

            # Third press: OWNER -> STATE
            await pilot.press("o")
            assert ticket_list.sort_mode == SortMode.STATE

    async def test_sort_mode_persists_with_filter(self) -> None:
        """Sort mode should be preserved when filtering."""
        from rally_tui.services import MockRallyClient

        tickets = [
            Ticket(
                formatted_id="US1005",
                name="Login feature",
                ticket_type="HierarchicalRequirement",
                state="In-Progress",
                owner="Alice",
            ),
            Ticket(
                formatted_id="US1001",
                name="Logout feature",
                ticket_type="HierarchicalRequirement",
                state="Defined",
                owner="Bob",
            ),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Change to CREATED sort
            await pilot.press("o")
            assert ticket_list.sort_mode == SortMode.CREATED

            # Apply filter
            ticket_list.filter_tickets("Log")
            assert ticket_list.filtered_count == 2
            assert ticket_list.sort_mode == SortMode.CREATED

    async def test_set_sort_mode_method(self, sort_tickets_fixture: list[Ticket]) -> None:
        """set_sort_mode should change mode and re-sort."""
        from textual.app import App, ComposeResult

        class SortTestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield TicketList(sort_tickets_fixture, id="ticket-list")

        app = SortTestApp()
        async with app.run_test():
            ticket_list = app.query_one(TicketList)
            assert ticket_list.sort_mode == SortMode.STATE

            ticket_list.set_sort_mode(SortMode.OWNER)
            assert ticket_list.sort_mode == SortMode.OWNER

    def test_set_sort_mode_same_mode_no_op(self) -> None:
        """set_sort_mode with same mode on unmounted widget should be a no-op."""
        ticket_list = TicketList([], sort_mode=SortMode.STATE)
        # This should not raise - same mode returns early before calling clear()
        ticket_list.set_sort_mode(SortMode.STATE)
        assert ticket_list.sort_mode == SortMode.STATE


class TestTicketListSelection:
    """Tests for TicketList multi-select functionality."""

    async def test_initial_selection_empty(self) -> None:
        """Selection should be empty initially."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            ticket_list = app.query_one(TicketList)
            assert ticket_list.selection_count == 0
            assert len(ticket_list.selected_tickets) == 0

    async def test_space_toggles_selection(self) -> None:
        """Pressing space should toggle selection on current item."""
        from rally_tui.services import MockRallyClient

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Initially no selection
            assert ticket_list.selection_count == 0

            # Select first ticket
            await pilot.press("space")
            await pilot.pause()
            assert ticket_list.selection_count == 1

            # Deselect first ticket
            await pilot.press("space")
            await pilot.pause()
            assert ticket_list.selection_count == 0

    async def test_space_selects_multiple(self) -> None:
        """Pressing space on different items selects multiple."""
        from rally_tui.services import MockRallyClient

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
            Ticket("US3", "Story 3", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Select first
            await pilot.press("space")
            await pilot.pause()

            # Move down and select second
            await pilot.press("j")
            await pilot.press("space")
            await pilot.pause()

            assert ticket_list.selection_count == 2

    async def test_ctrl_a_selects_all(self) -> None:
        """Ctrl+A should select all tickets."""
        from rally_tui.services import MockRallyClient

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
            Ticket("US3", "Story 3", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            await pilot.press("ctrl+a")
            await pilot.pause()

            assert ticket_list.selection_count == 3

    async def test_ctrl_a_deselects_if_all_selected(self) -> None:
        """Ctrl+A when all selected should deselect all."""
        from rally_tui.services import MockRallyClient

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Select all
            await pilot.press("ctrl+a")
            await pilot.pause()
            assert ticket_list.selection_count == 2

            # Deselect all
            await pilot.press("ctrl+a")
            await pilot.pause()
            assert ticket_list.selection_count == 0

    async def test_clear_selection(self) -> None:
        """clear_selection should clear all selections."""
        from rally_tui.services import MockRallyClient

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Select all
            await pilot.press("ctrl+a")
            await pilot.pause()
            assert ticket_list.selection_count == 2

            # Clear selection
            ticket_list.clear_selection()
            await pilot.pause()
            assert ticket_list.selection_count == 0

    async def test_selected_tickets_property(self) -> None:
        """selected_tickets should return list of selected Ticket objects."""
        from rally_tui.services import MockRallyClient

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Select first ticket
            await pilot.press("space")
            await pilot.pause()

            selected = ticket_list.selected_tickets
            assert len(selected) == 1
            assert selected[0].formatted_id == "US1"

    async def test_selection_message_posted(self) -> None:
        """SelectionChanged message should be posted when selection changes."""
        from rally_tui.services import MockRallyClient
        from rally_tui.widgets import StatusBar

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Select ticket
            await pilot.press("space")
            await pilot.pause()

            # Status bar should show selection count
            status_bar = app.query_one(StatusBar)
            assert status_bar.selection_count == 1


class TestTicketListBulkUpdate:
    """Tests for TicketList bulk update functionality."""

    async def test_update_tickets_updates_multiple(self) -> None:
        """update_tickets should update multiple tickets at once."""
        from rally_tui.services import MockRallyClient
        from rally_tui.widgets.ticket_list import TicketListItem

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
            Ticket("US3", "Story 3", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Update two tickets at once
            updated = [
                Ticket("US1", "Story 1", "UserStory", "Completed"),
                Ticket("US2", "Story 2", "UserStory", "Completed"),
            ]
            ticket_list.update_tickets(updated)
            await pilot.pause()

            # Check internal state
            states = {t.formatted_id: t.state for t in ticket_list._all_tickets}
            assert states["US1"] == "Completed"
            assert states["US2"] == "Completed"
            assert states["US3"] == "Defined"

            # Check UI items
            items = list(ticket_list.query(TicketListItem))
            assert len(items) == 3  # Should still have 3 items
            ui_states = {item.ticket.formatted_id: item.ticket.state for item in items}
            assert ui_states["US1"] == "Completed"
            assert ui_states["US2"] == "Completed"
            assert ui_states["US3"] == "Defined"

    async def test_update_tickets_preserves_selection(self) -> None:
        """update_tickets should preserve selection state."""
        from rally_tui.services import MockRallyClient

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Select first ticket
            await pilot.press("space")
            await pilot.pause()
            assert ticket_list.selection_count == 1

            # Update both tickets
            updated = [
                Ticket("US1", "Story 1", "UserStory", "Completed"),
                Ticket("US2", "Story 2", "UserStory", "Completed"),
            ]
            ticket_list.update_tickets(updated)
            await pilot.pause()

            # Selection should be preserved
            assert "US1" in ticket_list._selected_ids

    async def test_update_tickets_empty_list(self) -> None:
        """update_tickets with empty list should do nothing."""
        from rally_tui.services import MockRallyClient
        from rally_tui.widgets.ticket_list import TicketListItem

        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Update with empty list
            ticket_list.update_tickets([])
            await pilot.pause()

            # Should still have original ticket
            items = list(ticket_list.query(TicketListItem))
            assert len(items) == 1
            assert items[0].ticket.state == "Defined"
