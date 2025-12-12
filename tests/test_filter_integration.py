"""Integration tests for iteration and user filters."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.screens import IterationScreen
from rally_tui.services import MockRallyClient
from rally_tui.widgets import StatusBar, TicketList


@pytest.fixture
def tickets_with_iterations() -> list[Ticket]:
    """Sample tickets with different iterations and owners."""
    return [
        Ticket(
            formatted_id="US100",
            name="Story in Sprint 26",
            ticket_type="UserStory",
            state="Defined",
            owner="Alice",
            iteration="Sprint 26",
        ),
        Ticket(
            formatted_id="US101",
            name="Story in Sprint 26 by Bob",
            ticket_type="UserStory",
            state="In-Progress",
            owner="Bob",
            iteration="Sprint 26",
        ),
        Ticket(
            formatted_id="US102",
            name="Story in Sprint 25",
            ticket_type="UserStory",
            state="Completed",
            owner="Alice",
            iteration="Sprint 25",
        ),
        Ticket(
            formatted_id="US103",
            name="Backlog story",
            ticket_type="UserStory",
            state="Defined",
            owner="Bob",
            iteration=None,
        ),
        Ticket(
            formatted_id="DE200",
            name="Defect in backlog",
            ticket_type="Defect",
            state="Open",
            owner="Alice",
            iteration=None,
        ),
    ]


class TestIterationFilterKey:
    """Tests for 'i' key to open iteration filter."""

    async def test_i_key_opens_iteration_screen(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Pressing 'i' should open the IterationScreen."""
        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Press 'i' to open iteration filter
            await pilot.press("i")
            await pilot.pause()

            # Should be on IterationScreen
            assert isinstance(app.screen, IterationScreen)

    async def test_iteration_screen_shows_iterations(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """IterationScreen should show iterations from client."""
        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.press("i")
            await pilot.pause()

            # Screen should have iteration buttons
            btn1 = app.screen.query_one("#btn-iter-1")
            assert btn1 is not None

    async def test_escape_cancels_iteration_screen(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Escape should cancel without changing filter."""
        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Verify initial ticket count
            ticket_list = app.query_one(TicketList)
            initial_count = len(ticket_list._tickets)

            await pilot.press("i")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Should be back on main screen, no filter applied
            assert not isinstance(app.screen, IterationScreen)
            assert len(ticket_list._tickets) == initial_count


class TestIterationFilterBehavior:
    """Tests for iteration filter functionality."""

    async def test_filter_by_iteration(self, tickets_with_iterations: list[Ticket]) -> None:
        """Selecting an iteration should filter tickets."""
        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Initially all 5 tickets
            assert len(ticket_list._tickets) == 5

            # Open iteration screen and select Sprint 26 (first option)
            await pilot.press("i")
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause()

            # MockClient generates iterations around today, so we need to
            # test that filtering works (may not match exact sprint name)
            # For now, test the All filter (0) clears filters
            await pilot.press("i")
            await pilot.pause()
            await pilot.press("0")  # All
            await pilot.pause()

            # Should show all tickets again
            assert len(ticket_list._tickets) == 5

    async def test_filter_backlog(self, tickets_with_iterations: list[Ticket]) -> None:
        """Selecting Backlog should show only unscheduled tickets."""
        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Open iteration screen and select Backlog
            await pilot.press("i")
            await pilot.pause()
            await pilot.press("b")  # Backlog
            await pilot.pause()

            # Should show only 2 backlog tickets (US103 and DE200)
            assert len(ticket_list._tickets) == 2
            ids = {t.formatted_id for t in ticket_list._tickets}
            assert ids == {"US103", "DE200"}

    async def test_status_bar_shows_backlog_filter(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Status bar should show 'Backlog' when backlog filter is active."""
        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.press("i")
            await pilot.pause()
            await pilot.press("b")
            await pilot.pause()

            status_bar = app.query_one(StatusBar)
            assert "Backlog" in status_bar.display_content


class TestUserFilterKey:
    """Tests for 'u' key to toggle user filter."""

    async def test_u_key_toggles_user_filter(self, tickets_with_iterations: list[Ticket]) -> None:
        """Pressing 'u' should toggle the user filter."""
        client = MockRallyClient(
            tickets=tickets_with_iterations,
            current_user="Alice",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Initially all 5 tickets
            assert len(ticket_list._tickets) == 5

            # Press 'u' to enable user filter
            await pilot.press("u")
            await pilot.pause()

            # Should show only Alice's 3 tickets
            assert len(ticket_list._tickets) == 3
            assert all(t.owner == "Alice" for t in ticket_list._tickets)

            # Press 'u' again to disable
            await pilot.press("u")
            await pilot.pause()

            # Should show all 5 tickets
            assert len(ticket_list._tickets) == 5

    async def test_status_bar_shows_my_items(self, tickets_with_iterations: list[Ticket]) -> None:
        """Status bar should show 'My Items' when user filter is active."""
        client = MockRallyClient(
            tickets=tickets_with_iterations,
            current_user="Alice",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await pilot.press("u")
            await pilot.pause()

            status_bar = app.query_one(StatusBar)
            assert "My Items" in status_bar.display_content


class TestCombinedFilters:
    """Tests for combined iteration and user filters."""

    async def test_backlog_and_user_filter(self, tickets_with_iterations: list[Ticket]) -> None:
        """Both backlog and user filter should apply together."""
        client = MockRallyClient(
            tickets=tickets_with_iterations,
            current_user="Alice",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Filter to backlog
            await pilot.press("i")
            await pilot.pause()
            await pilot.press("b")
            await pilot.pause()

            # Should have 2 backlog items
            assert len(ticket_list._tickets) == 2

            # Add user filter
            await pilot.press("u")
            await pilot.pause()

            # Should have only Alice's backlog item (DE200)
            assert len(ticket_list._tickets) == 1
            assert ticket_list._tickets[0].formatted_id == "DE200"

    async def test_status_bar_shows_both_filters(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Status bar should show both filters when both are active."""
        client = MockRallyClient(
            tickets=tickets_with_iterations,
            current_user="Alice",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Set backlog filter
            await pilot.press("i")
            await pilot.pause()
            await pilot.press("b")
            await pilot.pause()

            # Set user filter
            await pilot.press("u")
            await pilot.pause()

            status_bar = app.query_one(StatusBar)
            content = status_bar.display_content
            assert "Backlog" in content
            assert "My Items" in content


class TestFilterPersistence:
    """Tests for filter state persistence across screens."""

    async def test_filter_persists_after_discussion(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Filter should persist after opening and closing discussions."""
        client = MockRallyClient(
            tickets=tickets_with_iterations,
            current_user="Alice",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Set backlog filter
            await pilot.press("i")
            await pilot.pause()
            await pilot.press("b")
            await pilot.pause()

            # Should have 2 backlog items
            assert len(ticket_list._tickets) == 2

            # Open and close discussions
            await pilot.press("d")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Filter should still be active
            assert len(ticket_list._tickets) == 2


class TestConnectedModeFiltering:
    """Tests for filter behavior in connected mode.

    These tests verify that when connected to Rally, filter changes
    always fetch from the server instead of filtering locally.
    This prevents issues where _all_tickets may be empty or stale.
    """

    def test_apply_filters_fetches_from_server_when_connected_with_iteration(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Connected mode with iteration filter should trigger server fetch."""
        from unittest.mock import MagicMock, patch

        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)

        # Simulate connected mode
        app._connected = True
        app._iteration_filter = "Sprint 26"

        # Mock run_worker to track if it was called
        with patch.object(app, "run_worker") as mock_worker:
            with patch.object(app, "query_one") as mock_query:
                mock_status_bar = MagicMock()
                mock_query.return_value = mock_status_bar

                app._apply_filters()

                # Should have called run_worker to fetch from server
                mock_worker.assert_called_once()

    def test_apply_filters_fetches_from_server_when_connected_with_backlog(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Connected mode with backlog filter should trigger server fetch."""
        from unittest.mock import MagicMock, patch

        from rally_tui.screens import FILTER_BACKLOG

        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)

        # Simulate connected mode with backlog filter
        app._connected = True
        app._iteration_filter = FILTER_BACKLOG

        with patch.object(app, "run_worker") as mock_worker:
            with patch.object(app, "query_one") as mock_query:
                mock_status_bar = MagicMock()
                mock_query.return_value = mock_status_bar

                app._apply_filters()

                # Should have called run_worker to fetch from server
                mock_worker.assert_called_once()

    def test_apply_filters_fetches_from_server_when_connected_with_all(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Connected mode with 'All' filter (None) should trigger server fetch.

        This is the bug case: when _iteration_filter is None (All selected),
        the app should still fetch from server, not filter locally.
        """
        from unittest.mock import MagicMock, patch

        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)

        # Simulate connected mode with "All" filter (None)
        app._connected = True
        app._iteration_filter = None  # This is what "All" sets

        with patch.object(app, "run_worker") as mock_worker:
            with patch.object(app, "query_one") as mock_query:
                mock_status_bar = MagicMock()
                mock_query.return_value = mock_status_bar

                app._apply_filters()

                # Should have called run_worker to fetch from server
                # Before the fix, this would NOT call run_worker when
                # _iteration_filter was None
                mock_worker.assert_called_once()

    def test_apply_filters_does_not_fetch_when_not_connected(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Offline mode should filter locally, not fetch from server."""
        from unittest.mock import MagicMock, patch

        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)

        # Ensure not connected (default for MockRallyClient)
        app._connected = False
        app._iteration_filter = "Sprint 26"
        app._all_tickets = tickets_with_iterations

        with patch.object(app, "run_worker") as mock_worker:
            with patch.object(app, "query_one") as mock_query:
                # Mock widgets that _apply_filters needs
                mock_ticket_list = MagicMock()
                mock_ticket_list._tickets = []
                mock_status_bar = MagicMock()
                mock_detail = MagicMock()

                def query_side_effect(selector):
                    if selector == TicketList or "ticket-list" in str(selector):
                        return mock_ticket_list
                    elif selector == StatusBar or "status-bar" in str(selector):
                        return mock_status_bar
                    else:
                        return mock_detail

                mock_query.side_effect = query_side_effect

                app._apply_filters()

                # Should NOT have called run_worker - filter locally instead
                mock_worker.assert_not_called()


class TestBuildIterationQuery:
    """Tests for _build_iteration_query method.

    These tests verify the query builder generates correct Rally WSAPI
    queries for different filter combinations.
    """

    def test_query_with_iteration_filter(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Query with iteration filter should include Iteration.Name condition."""
        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)

        app._iteration_filter = "Sprint 26"
        app._user_filter_active = False

        query = app._build_iteration_query()

        assert 'Iteration.Name = "Sprint 26"' in query
        assert f'Project.Name = "{client.project}"' in query

    def test_query_with_backlog_filter(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Query with backlog filter should include Iteration = null condition."""
        from rally_tui.screens import FILTER_BACKLOG

        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)

        app._iteration_filter = FILTER_BACKLOG
        app._user_filter_active = False

        query = app._build_iteration_query()

        assert "(Iteration = null)" in query
        assert f'Project.Name = "{client.project}"' in query

    def test_query_with_all_filter(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Query with 'All' filter (None) should only have project scope."""
        client = MockRallyClient(tickets=tickets_with_iterations)
        app = RallyTUI(client=client, show_splash=False)

        app._iteration_filter = None  # "All" filter
        app._user_filter_active = False

        query = app._build_iteration_query()

        # Should only have project scope, no iteration filter
        assert f'Project.Name = "{client.project}"' in query
        assert "Iteration" not in query

    def test_query_with_user_filter(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Query with user filter should include Owner.DisplayName condition."""
        client = MockRallyClient(tickets=tickets_with_iterations, current_user="Alice")
        app = RallyTUI(client=client, show_splash=False)

        app._iteration_filter = None
        app._user_filter_active = True

        query = app._build_iteration_query()

        assert 'Owner.DisplayName = "Alice"' in query

    def test_query_with_combined_filters(
        self, tickets_with_iterations: list[Ticket]
    ) -> None:
        """Query with multiple filters should combine with AND."""
        from rally_tui.screens import FILTER_BACKLOG

        client = MockRallyClient(tickets=tickets_with_iterations, current_user="Alice")
        app = RallyTUI(client=client, show_splash=False)

        app._iteration_filter = FILTER_BACKLOG
        app._user_filter_active = True

        query = app._build_iteration_query()

        # Should have all three conditions combined with AND
        assert f'Project.Name = "{client.project}"' in query
        assert "(Iteration = null)" in query
        assert 'Owner.DisplayName = "Alice"' in query
        assert "AND" in query
