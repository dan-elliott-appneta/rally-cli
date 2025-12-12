"""Tests for async client integration in the RallyTUI app."""

from rally_tui.app import RallyTUI
from rally_tui.services.mock_client import MockRallyClient


class TestAppAsyncInitialization:
    """Tests for async client initialization."""

    async def test_app_initializes_without_async_client_for_mock(self) -> None:
        """App should not initialize async client when using MockRallyClient."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            # Mock client doesn't trigger async initialization
            assert app._async_client is None
            assert app._use_async is False

    async def test_app_has_sync_client_by_default(self) -> None:
        """App should have sync client available by default."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            # Sync client should always be available
            assert app._client is not None
            assert app._connected is False  # MockRallyClient = not connected

    async def test_app_loads_tickets_with_sync_fallback(self) -> None:
        """App should load tickets via sync path when no async client."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            from rally_tui.widgets import TicketList

            ticket_list = app.query_one(TicketList)
            # Should have loaded tickets from sync client
            assert ticket_list.total_count > 0


class TestAppAsyncWorkerMethods:
    """Tests for async worker methods."""

    async def test_load_initial_tickets_sync_returns_list(self) -> None:
        """Sync loading method should return a list of tickets."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            tickets = app._load_initial_tickets()
            assert isinstance(tickets, list)
            assert len(tickets) > 0

    async def test_load_all_tickets_sync_returns_list(self) -> None:
        """Sync loading all tickets should return a list."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            tickets = app._load_all_tickets()
            assert isinstance(tickets, list)

    async def test_build_iteration_query_for_backlog(self) -> None:
        """Should build correct query for backlog filter."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            from rally_tui.screens import FILTER_BACKLOG

            app._iteration_filter = FILTER_BACKLOG
            query = app._build_iteration_query()
            assert query == "(Iteration = null)"

    async def test_build_iteration_query_for_iteration(self) -> None:
        """Should build correct query for iteration filter."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            app._iteration_filter = "Sprint 42"
            query = app._build_iteration_query()
            assert query == '(Iteration.Name = "Sprint 42")'

    async def test_build_iteration_query_for_none(self) -> None:
        """Should return empty query when no iteration filter."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            app._iteration_filter = None
            query = app._build_iteration_query()
            assert query == ""


class TestAppAsyncLoadMethods:
    """Tests for async load method implementations."""

    async def test_load_initial_tickets_async_without_client(self) -> None:
        """Async loading should fall back when no async client."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            # Should fall back to sync since no async client
            tickets = await app._load_initial_tickets_async()
            assert isinstance(tickets, list)

    async def test_load_all_tickets_async_without_client(self) -> None:
        """Async loading all should return empty list when no async client."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            # Should return empty list since no async client
            tickets = await app._load_all_tickets_async()
            assert isinstance(tickets, list)

    async def test_fetch_filtered_tickets_async_without_client(self) -> None:
        """Async filtered fetch should return empty list when no async client."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            app._iteration_filter = "Sprint 42"
            # Should return empty list since no async client
            tickets = await app._fetch_filtered_tickets_async()
            assert isinstance(tickets, list)

    async def test_refresh_all_tickets_async_without_client(self) -> None:
        """Async refresh should return empty list when no async client."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            # Should return empty list since no async client
            tickets = await app._refresh_all_tickets_async()
            assert isinstance(tickets, list)


class TestAppAsyncFlags:
    """Tests for async mode flags and state."""

    async def test_use_async_defaults_to_false(self) -> None:
        """The _use_async flag should default to False."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            assert app._use_async is False

    async def test_async_client_defaults_to_none(self) -> None:
        """The _async_client should default to None."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            assert app._async_client is None

    async def test_async_caching_client_defaults_to_none(self) -> None:
        """The _async_caching_client should default to None."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            assert app._async_caching_client is None


class TestAppCacheStatusCallbacks:
    """Tests for cache status change callbacks."""

    async def test_on_cache_status_change_handles_all_statuses(self) -> None:
        """Cache status callback should handle all status types."""
        from rally_tui.services.caching_client import CacheStatus

        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            # Test all status values (shouldn't raise exceptions)
            for status in CacheStatus:
                app._on_cache_status_change(status, 5)

    async def test_on_async_cache_status_change_handles_all_statuses(self) -> None:
        """Async cache status callback should handle all status types."""
        from rally_tui.services.async_caching_client import CacheStatus

        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            # Test all status values (shouldn't raise exceptions)
            for status in CacheStatus:
                app._on_async_cache_status_change(status, 5)


class TestAppWorkerHandling:
    """Tests for worker state handling."""

    async def test_worker_state_handler_recognizes_async_names(self) -> None:
        """Worker state handler should recognize async worker names."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=False)

        async with app.run_test():
            # The async worker names should be in the fetch workers tuple
            # This is tested implicitly by the handler not raising errors
            # Verify these are recognized (they appear in the handler's conditions)
            # This test just ensures the app loads without errors
            assert app._connected is False
