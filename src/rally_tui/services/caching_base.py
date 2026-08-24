"""Shared base for the sync and async Rally caching client wrappers.

Holds everything that doesn't depend on sync vs. async I/O: construction,
pass-through metadata properties, cache-status event wiring, and the
cache-update-after-mutation helper. Each concrete wrapper (CachingRallyClient,
AsyncCachingRallyClient) still owns its own get_tickets/_fetch_from_api and
pass-through methods, since those bodies genuinely differ by async/await.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import Enum
from typing import Any

from rally_tui.models import Ticket
from rally_tui.services.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class CacheStatus(Enum):
    """Status of cached data."""

    LIVE = "live"  # Fresh data from API
    CACHED = "cached"  # Showing cached data
    REFRESHING = "refreshing"  # Background refresh in progress
    OFFLINE = "offline"  # No network, using cache


class BaseCachingClient:
    """Shared state and pass-through metadata for caching client wrappers."""

    def __init__(
        self,
        client: Any,
        cache_manager: CacheManager,
        cache_enabled: bool = True,
        ttl_minutes: int = 15,
        auto_refresh: bool = True,
    ) -> None:
        """Initialize the caching client wrapper.

        Args:
            client: The underlying Rally client to wrap.
            cache_manager: CacheManager instance for persistence.
            cache_enabled: Whether caching is enabled.
            ttl_minutes: Time-to-live for cache in minutes.
            auto_refresh: Whether to auto-refresh when cache is stale.
        """
        self._client = client
        self._cache = cache_manager
        self._enabled = cache_enabled
        self._ttl = ttl_minutes
        self._auto_refresh = auto_refresh
        self._is_offline = False
        self._cache_status = CacheStatus.LIVE
        self._on_status_change: Callable[[CacheStatus, int | None], None] | None = None
        self._on_tickets_updated: Callable[[list[Ticket]], None] | None = None

    # Pass-through properties from underlying client

    @property
    def workspace(self) -> str:
        """Get the current workspace name."""
        return self._client.workspace

    @property
    def project(self) -> str:
        """Get the current project name."""
        return self._client.project

    @property
    def current_user(self) -> str | None:
        """Get the current user's display name."""
        return self._client.current_user

    @property
    def current_iteration(self) -> str | None:
        """Get the current iteration name."""
        return self._client.current_iteration

    # Cache-specific properties

    @property
    def is_offline(self) -> bool:
        """Whether the client is in offline mode."""
        return self._is_offline

    @property
    def cache_status(self) -> CacheStatus:
        """Current cache status."""
        return self._cache_status

    @property
    def cache_age_minutes(self) -> int | None:
        """Age of the cache in minutes, or None if no cache."""
        return self._cache.get_cache_age_minutes()

    # Event handlers

    def set_on_status_change(
        self, callback: Callable[[CacheStatus, int | None], None] | None
    ) -> None:
        """Set callback for cache status changes.

        Args:
            callback: Function called with (status, age_minutes) when status changes.
        """
        self._on_status_change = callback

    def set_on_tickets_updated(self, callback: Callable[[list[Ticket]], None] | None) -> None:
        """Set callback for when tickets are refreshed from API.

        Args:
            callback: Function called with new tickets list after refresh.
        """
        self._on_tickets_updated = callback

    def _set_status(self, status: CacheStatus) -> None:
        """Update cache status and notify listener."""
        self._cache_status = status
        if self._on_status_change:
            self._on_status_change(status, self.cache_age_minutes)

    def is_cache_stale(self) -> bool:
        """Check if cache is stale and needs refresh.

        Returns:
            True if cache is stale or doesn't exist.
        """
        return not self._cache.is_cache_valid(self._ttl)

    def _update_ticket_in_cache(self, updated_ticket: Ticket) -> None:
        """Update a ticket in the cache after a mutation.

        Args:
            updated_ticket: The updated ticket to store in cache.
        """
        cached_tickets, metadata = self._cache.get_cached_tickets()
        if not cached_tickets:
            return

        if not any(t.formatted_id == updated_ticket.formatted_id for t in cached_tickets):
            logger.debug(f"Ticket {updated_ticket.formatted_id} not in cache, skipping save")
            return

        cached_tickets[:] = [
            updated_ticket if t.formatted_id == updated_ticket.formatted_id else t
            for t in cached_tickets
        ]
        self._cache.save_tickets(cached_tickets, workspace=self.workspace, project=self.project)
