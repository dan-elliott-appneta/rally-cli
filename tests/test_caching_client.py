"""Tests for the CachingRallyClient."""

from pathlib import Path
from unittest.mock import MagicMock

from rally_tui.models import Ticket
from rally_tui.services.cache_manager import CacheManager
from rally_tui.services.caching_client import CacheStatus, CachingRallyClient
from rally_tui.services.mock_client import MockRallyClient


class TestCachingRallyClientInit:
    """Tests for CachingRallyClient initialization."""

    def test_creates_with_defaults(self, tmp_path: Path) -> None:
        """Should initialize with default settings."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        assert caching._enabled is True
        assert caching._ttl == 15
        assert caching._auto_refresh is True
        assert caching.is_offline is False

    def test_creates_with_custom_settings(self, tmp_path: Path) -> None:
        """Should accept custom settings."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(
            client,
            cache,
            cache_enabled=False,
            ttl_minutes=30,
            auto_refresh=False,
        )

        assert caching._enabled is False
        assert caching._ttl == 30
        assert caching._auto_refresh is False


class TestCachingRallyClientProperties:
    """Tests for pass-through properties."""

    def test_workspace_passthrough(self, tmp_path: Path) -> None:
        """workspace should come from underlying client."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        assert caching.workspace == client.workspace

    def test_project_passthrough(self, tmp_path: Path) -> None:
        """project should come from underlying client."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        assert caching.project == client.project

    def test_current_user_passthrough(self, tmp_path: Path) -> None:
        """current_user should come from underlying client."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        assert caching.current_user == client.current_user

    def test_current_iteration_passthrough(self, tmp_path: Path) -> None:
        """current_iteration should come from underlying client."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        assert caching.current_iteration == client.current_iteration


class TestCachingRallyClientCacheDisabled:
    """Tests when caching is disabled."""

    def test_fetches_from_api_when_disabled(self, tmp_path: Path) -> None:
        """Should always fetch from API when caching disabled."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache, cache_enabled=False)

        tickets = caching.get_tickets()

        assert len(tickets) > 0
        assert caching.cache_status == CacheStatus.LIVE


class TestCachingRallyClientCacheFirst:
    """Tests for cache-first behavior."""

    def test_returns_cached_tickets_when_available(self, tmp_path: Path) -> None:
        """Should return cached tickets without API call."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)

        # Pre-populate cache
        cached_ticket = Ticket(
            formatted_id="CACHED1",
            name="Cached ticket",
            ticket_type="UserStory",
            state="Defined",
        )
        cache.save_tickets([cached_ticket], workspace=client.workspace, project=client.project)

        caching = CachingRallyClient(client, cache)
        tickets = caching.get_tickets()

        assert len(tickets) == 1
        assert tickets[0].formatted_id == "CACHED1"
        assert caching.cache_status == CacheStatus.CACHED

    def test_fetches_from_api_when_cache_empty(self, tmp_path: Path) -> None:
        """Should fetch from API when no cache exists."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        tickets = caching.get_tickets()

        assert len(tickets) > 0
        assert caching.cache_status == CacheStatus.LIVE

    def test_fetches_when_cache_for_different_project(self, tmp_path: Path) -> None:
        """Should fetch from API when cache is for different project."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)

        # Pre-populate cache for different project
        cache.save_tickets([], workspace="Different", project="Other")

        caching = CachingRallyClient(client, cache)
        tickets = caching.get_tickets()

        # Should have fetched fresh data
        assert len(tickets) > 0
        assert caching.cache_status == CacheStatus.LIVE


class TestCachingRallyClientRefresh:
    """Tests for cache refresh behavior."""

    def test_refresh_cache_fetches_fresh_data(self, tmp_path: Path) -> None:
        """refresh_cache should always fetch from API."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)

        # Pre-populate cache
        cached_ticket = Ticket(
            formatted_id="OLD1",
            name="Old ticket",
            ticket_type="UserStory",
            state="Defined",
        )
        cache.save_tickets([cached_ticket], workspace=client.workspace, project=client.project)

        caching = CachingRallyClient(client, cache)
        tickets = caching.refresh_cache()

        # Should have fresh data from mock client, not cached
        assert all(t.formatted_id != "OLD1" for t in tickets)
        assert caching.cache_status == CacheStatus.LIVE

    def test_is_cache_stale_true_when_no_cache(self, tmp_path: Path) -> None:
        """is_cache_stale should return True when no cache."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        assert caching.is_cache_stale() is True

    def test_is_cache_stale_false_when_fresh(self, tmp_path: Path) -> None:
        """is_cache_stale should return False when cache is fresh."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        # Populate cache
        caching.refresh_cache()

        assert caching.is_cache_stale() is False


class TestCachingRallyClientOffline:
    """Tests for offline mode behavior."""

    def test_offline_mode_returns_cached_tickets(self, tmp_path: Path) -> None:
        """Should return cached tickets when API fails."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)

        # Pre-populate cache
        cached_ticket = Ticket(
            formatted_id="OFFLINE1",
            name="Offline ticket",
            ticket_type="UserStory",
            state="Defined",
        )
        cache.save_tickets([cached_ticket], workspace=client.workspace, project=client.project)

        # Create client that will fail
        failing_client = MagicMock()
        failing_client.workspace = client.workspace
        failing_client.project = client.project
        failing_client.get_tickets.side_effect = Exception("Network error")

        caching = CachingRallyClient(failing_client, cache)
        # Force API call by clearing valid cache
        cache.clear_cache()
        cache.save_tickets([cached_ticket], workspace=client.workspace, project=client.project)

        # Make the cache appear stale so it tries API
        caching._cache._ensure_cache_dir()
        caching.refresh_cache()

        assert caching.is_offline is True
        assert caching.cache_status == CacheStatus.OFFLINE

    def test_offline_blocks_write_operations(self, tmp_path: Path) -> None:
        """Write operations should return None when offline."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)
        caching._is_offline = True

        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )

        assert caching.update_state(ticket, "In-Progress") is None
        assert caching.update_points(ticket, 5) is None
        assert caching.add_comment(ticket, "comment") is None
        assert caching.set_parent(ticket, "F123") is None
        assert caching.create_ticket("Title", "HierarchicalRequirement") is None
        assert caching.upload_attachment(ticket, "/path/file.txt") is None

    def test_offline_blocks_bulk_operations(self, tmp_path: Path) -> None:
        """Bulk operations should fail when offline."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)
        caching._is_offline = True

        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        tickets = [ticket]

        result = caching.bulk_update_state(tickets, "In-Progress")
        assert result.failed_count == 1
        assert "offline" in result.errors[0].lower()

        result = caching.bulk_set_parent(tickets, "F123")
        assert result.failed_count == 1

        result = caching.bulk_set_iteration(tickets, "Sprint 1")
        assert result.failed_count == 1

        result = caching.bulk_update_points(tickets, 5)
        assert result.failed_count == 1


class TestCachingRallyClientPassthrough:
    """Tests for pass-through methods."""

    def test_get_ticket_passthrough(self, tmp_path: Path) -> None:
        """get_ticket should call underlying client."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        ticket = caching.get_ticket("US1234")
        assert ticket is not None

    def test_get_discussions_passthrough(self, tmp_path: Path) -> None:
        """get_discussions should call underlying client."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        discussions = caching.get_discussions(ticket)
        assert isinstance(discussions, list)

    def test_get_iterations_passthrough(self, tmp_path: Path) -> None:
        """get_iterations should call underlying client."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        iterations = caching.get_iterations()
        assert len(iterations) > 0

    def test_get_attachments_passthrough(self, tmp_path: Path) -> None:
        """get_attachments should call underlying client."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        attachments = caching.get_attachments(ticket)
        assert isinstance(attachments, list)


class TestCachingRallyClientCallbacks:
    """Tests for event callbacks."""

    def test_status_change_callback(self, tmp_path: Path) -> None:
        """Should call status change callback."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)
        caching = CachingRallyClient(client, cache)

        status_changes = []

        def on_status(status: CacheStatus, age: int | None) -> None:
            status_changes.append((status, age))

        caching.set_on_status_change(on_status)
        caching.get_tickets()

        assert len(status_changes) > 0
        # Final status should be LIVE after successful fetch
        assert status_changes[-1][0] == CacheStatus.LIVE

    def test_cache_age_returned_in_callback(self, tmp_path: Path) -> None:
        """Callback should receive cache age."""
        client = MockRallyClient()
        cache = CacheManager(cache_dir=tmp_path)

        # Pre-populate cache
        cache.save_tickets([], workspace=client.workspace, project=client.project)

        caching = CachingRallyClient(client, cache)

        ages = []

        def on_status(status: CacheStatus, age: int | None) -> None:
            ages.append(age)

        caching.set_on_status_change(on_status)
        caching.get_tickets()

        # Age should be 0 for fresh cache
        assert any(a == 0 for a in ages)


class TestCacheStatusEnum:
    """Tests for CacheStatus enum."""

    def test_cache_status_values(self) -> None:
        """CacheStatus should have expected values."""
        assert CacheStatus.LIVE.value == "live"
        assert CacheStatus.CACHED.value == "cached"
        assert CacheStatus.REFRESHING.value == "refreshing"
        assert CacheStatus.OFFLINE.value == "offline"
