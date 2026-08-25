"""Tests for async client integration in the RallyTUI app."""

from rally_tui.app import RallyTUI
from rally_tui.services.async_adapter import AsyncClientAdapter
from rally_tui.services.mock_client import MockRallyClient


class TestAppClientSetup:
    """Tests for how the app wires up its Rally client."""

    async def test_sync_client_is_wrapped_for_async_use(self) -> None:
        """A synchronous client should be adapted, not used directly."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            assert isinstance(app._client, AsyncClientAdapter)
            assert app._client.wrapped is client

    async def test_mock_client_does_not_connect(self) -> None:
        """MockRallyClient means offline: no real client, no cache."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            assert app._connected is False
            assert app._async_client is None
            assert app._async_caching_client is None
            assert app._cache_manager is None

    async def test_app_loads_tickets_from_client(self) -> None:
        """Tickets should be loaded through the adapted client."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            from rally_tui.widgets import TicketList

            assert app.query_one(TicketList).total_count > 0

    async def test_adapter_passes_through_properties(self) -> None:
        """Properties should read through the adapter unchanged."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            assert app._client.workspace == client.workspace
            assert app._client.project == client.project
            assert app._client.current_user == client.current_user


class TestAppLoadMethods:
    """Tests for the ticket-loading coroutines."""

    async def test_load_initial_tickets(self) -> None:
        """Initial load should return the client's tickets."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            tickets = await app._load_initial_tickets()
            assert isinstance(tickets, list)
            assert len(tickets) > 0

    async def test_load_all_tickets(self) -> None:
        """Background load should return a list."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            assert isinstance(await app._load_all_tickets(), list)

    async def test_fetch_filtered_tickets(self) -> None:
        """Filtered fetch should return a list."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            app._iteration_filter = "Sprint 42"
            assert isinstance(await app._fetch_filtered_tickets(), list)

    async def test_refresh_all_tickets(self) -> None:
        """Refresh should return a list even without a caching client."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            assert isinstance(await app._refresh_all_tickets(), list)

    async def test_load_returns_empty_list_on_client_error(self) -> None:
        """A failing client should degrade to an empty list, not raise."""
        from unittest.mock import AsyncMock

        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            app._client.get_tickets = AsyncMock(side_effect=Exception("boom"))
            assert await app._load_initial_tickets() == []


class TestAppQueryBuilding:
    """Tests for server-side filter query construction."""

    async def test_build_iteration_query_for_backlog(self) -> None:
        """Should build correct query for backlog filter with project scoping."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            from rally_tui.screens import FILTER_BACKLOG

            app._iteration_filter = FILTER_BACKLOG
            query = app._build_iteration_query()
            assert '(Project.Name = "My Project")' in query
            assert "(Iteration = null)" in query

    async def test_build_iteration_query_for_iteration(self) -> None:
        """Should build correct query for iteration filter with project scoping."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            app._iteration_filter = "Sprint 42"
            query = app._build_iteration_query()
            assert '(Project.Name = "My Project")' in query
            assert '(Iteration.Name = "Sprint 42")' in query

    async def test_build_iteration_query_for_none(self) -> None:
        """Should return project-only query when no iteration filter."""
        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            app._iteration_filter = None
            assert app._build_iteration_query() == '(Project.Name = "My Project")'


class TestAppCacheStatusCallback:
    """Tests for the cache status change callback."""

    async def test_handles_all_statuses(self) -> None:
        """Cache status callback should handle all status types."""
        from rally_tui.services.async_caching_client import CacheStatus

        app = RallyTUI(client=MockRallyClient(), show_splash=False)

        async with app.run_test():
            for status in CacheStatus:
                app._on_cache_status_change(status, 5)
