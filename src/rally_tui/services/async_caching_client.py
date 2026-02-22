"""Async caching wrapper for Rally client with stale-while-revalidate strategy.

This module provides an async caching layer that wraps an async Rally client,
providing the same caching behavior as CachingRallyClient but for async operations.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Protocol

from rally_tui.models import Attachment, Discussion, Iteration, Owner, Ticket
from rally_tui.services.cache_manager import CacheManager
from rally_tui.services.protocol import BulkResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AsyncRallyClientProtocol(Protocol):
    """Protocol for async Rally clients."""

    @property
    def workspace(self) -> str: ...

    @property
    def project(self) -> str: ...

    @property
    def current_user(self) -> str | None: ...

    @property
    def current_iteration(self) -> str | None: ...

    async def get_tickets(self, query: str | None = None) -> list[Ticket]: ...
    async def get_ticket(self, formatted_id: str) -> Ticket | None: ...
    async def get_discussions(self, ticket: Ticket) -> list[Discussion]: ...
    async def add_comment(self, ticket: Ticket, text: str) -> Discussion | None: ...
    async def update_points(self, ticket: Ticket, points: float) -> Ticket | None: ...
    async def update_state(self, ticket: Ticket, state: str) -> Ticket | None: ...
    async def create_ticket(
        self,
        title: str,
        ticket_type: str,
        description: str = "",
        points: float | None = None,
        backlog: bool = False,
    ) -> Ticket | None: ...
    async def get_iterations(self, count: int = 5, state: str | None = None) -> list[Iteration]: ...
    async def get_future_iterations(self, count: int = 5) -> list[Iteration]: ...
    async def get_feature(self, formatted_id: str) -> tuple[str, str] | None: ...
    async def set_parent(self, ticket: Ticket, parent_id: str) -> Ticket | None: ...
    async def bulk_set_parent(self, tickets: list[Ticket], parent_id: str) -> BulkResult: ...
    async def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult: ...
    async def bulk_set_iteration(
        self, tickets: list[Ticket], iteration_name: str | None
    ) -> BulkResult: ...
    async def bulk_update_points(self, tickets: list[Ticket], points: float) -> BulkResult: ...
    async def get_attachments(self, ticket: Ticket) -> list[Attachment]: ...
    async def download_attachment(
        self, ticket: Ticket, attachment: Attachment, dest_path: str
    ) -> bool: ...
    async def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None: ...
    async def download_embedded_image(self, url: str, dest_path: str) -> bool: ...
    async def get_users(self, display_names: list[str] | None = None) -> list[Owner]: ...
    async def assign_owner(self, ticket: Ticket, owner: Owner) -> Ticket | None: ...
    async def bulk_assign_owner(self, tickets: list[Ticket], owner: Owner) -> BulkResult: ...


class CacheStatus(Enum):
    """Status of cached data."""

    LIVE = "live"  # Fresh data from API
    CACHED = "cached"  # Showing cached data
    REFRESHING = "refreshing"  # Background refresh in progress
    OFFLINE = "offline"  # No network, using cache


class AsyncCachingRallyClient:
    """Async caching wrapper for Rally client.

    Implements stale-while-revalidate caching with async operations:
    - On get_tickets(): Return cached data immediately if available
    - Trigger background refresh if cache is stale
    - Cache is invalidated when workspace/project changes

    All write operations are passed through to the underlying client.
    """

    def __init__(
        self,
        client: AsyncRallyClientProtocol,
        cache_manager: CacheManager,
        cache_enabled: bool = True,
        ttl_minutes: int = 15,
        auto_refresh: bool = True,
    ) -> None:
        """Initialize the async caching client wrapper.

        Args:
            client: The underlying async Rally client to wrap
            cache_manager: CacheManager instance for persistence
            cache_enabled: Whether caching is enabled
            ttl_minutes: Time-to-live for cache in minutes
            auto_refresh: Whether to auto-refresh when cache is stale
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

    # Pass-through properties

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
        """Set callback for cache status changes."""
        self._on_status_change = callback

    def set_on_tickets_updated(self, callback: Callable[[list[Ticket]], None] | None) -> None:
        """Set callback for when tickets are refreshed from API."""
        self._on_tickets_updated = callback

    def _set_status(self, status: CacheStatus) -> None:
        """Update cache status and notify listener."""
        self._cache_status = status
        if self._on_status_change:
            self._on_status_change(status, self.cache_age_minutes)

    # Core caching methods

    async def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Get tickets, using cache if available.

        Cache-first strategy:
        1. If cache disabled, fetch from API
        2. If query provided, bypass cache and fetch from API
        3. If cache exists and valid, return cached data
        4. If cache exists but stale, return cached + trigger refresh
        5. If no cache, fetch from API

        Args:
            query: Optional query (passed to underlying client).

        Returns:
            List of tickets (may be cached)
        """
        if not self._enabled:
            return await self._fetch_from_api(query)

        # When a specific query is provided, bypass cache
        if query:
            logger.info(f"Query provided, bypassing cache: {query}")
            return await self._fetch_from_api(query)

        # Check if cache is for correct workspace/project
        if not self._cache.is_cache_for_project(self.workspace, self.project):
            logger.info("Cache is for different project, fetching fresh data")
            return await self._fetch_from_api(query)

        # Try to get cached tickets
        cached_tickets, metadata = self._cache.get_cached_tickets()

        if cached_tickets:
            is_stale = not self._cache.is_cache_valid(self._ttl)

            if is_stale and self._auto_refresh:
                logger.info("Cache is stale, returning cached and will refresh")
                self._set_status(CacheStatus.CACHED)
            else:
                self._set_status(CacheStatus.CACHED)

            return cached_tickets

        # No cache, fetch from API
        return await self._fetch_from_api(query)

    async def _fetch_from_api(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets from the underlying async API.

        Args:
            query: Optional query filter.

        Returns:
            List of tickets from API
        """
        try:
            self._set_status(CacheStatus.REFRESHING)
            tickets = await self._client.get_tickets(query)

            # Only save to cache when fetching all tickets (no query)
            if self._enabled and not query:
                self._cache.save_tickets(
                    tickets,
                    workspace=self.workspace,
                    project=self.project,
                )

            self._is_offline = False
            self._set_status(CacheStatus.LIVE)
            return tickets

        except Exception as e:
            logger.error(f"Failed to fetch tickets from API: {e}")
            self._is_offline = True
            self._set_status(CacheStatus.OFFLINE)

            # Try to return cached data as fallback
            cached_tickets, _ = self._cache.get_cached_tickets()
            if cached_tickets:
                logger.info("Returning cached tickets due to API failure")
                return cached_tickets

            return []

    async def refresh_cache(self) -> list[Ticket]:
        """Force refresh tickets from API and update cache."""
        return await self._fetch_from_api()

    def is_cache_stale(self) -> bool:
        """Check if cache is stale and needs refresh."""
        return not self._cache.is_cache_valid(self._ttl)

    # Pass-through methods (no caching)

    async def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by ID (not cached)."""
        return await self._client.get_ticket(formatted_id)

    async def get_discussions(self, ticket: Ticket) -> list[Discussion]:
        """Fetch discussions for a ticket (not cached)."""
        return await self._client.get_discussions(ticket)

    async def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
        """Add a comment to a ticket."""
        if self._is_offline:
            return None
        return await self._client.add_comment(ticket, text)

    async def update_points(self, ticket: Ticket, points: float) -> Ticket | None:
        """Update a ticket's story points."""
        if self._is_offline:
            return None
        return await self._client.update_points(ticket, points)

    async def create_ticket(
        self,
        title: str,
        ticket_type: str,
        description: str = "",
        points: float | None = None,
        backlog: bool = False,
    ) -> Ticket | None:
        """Create a new ticket."""
        if self._is_offline:
            return None
        return await self._client.create_ticket(title, ticket_type, description, points, backlog)

    async def update_state(self, ticket: Ticket, state: str) -> Ticket | None:
        """Update a ticket's workflow state."""
        if self._is_offline:
            return None
        return await self._client.update_state(ticket, state)

    async def get_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch recent iterations (not cached)."""
        return await self._client.get_iterations(count)

    async def get_feature(self, formatted_id: str) -> tuple[str, str] | None:
        """Fetch a Feature's name by ID (not cached)."""
        return await self._client.get_feature(formatted_id)

    async def set_parent(self, ticket: Ticket, parent_id: str) -> Ticket | None:
        """Set a ticket's parent Feature."""
        if self._is_offline:
            return None
        return await self._client.set_parent(ticket, parent_id)

    async def bulk_set_parent(self, tickets: list[Ticket], parent_id: str) -> BulkResult:
        """Set parent Feature on multiple tickets."""
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )
        return await self._client.bulk_set_parent(tickets, parent_id)

    async def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult:
        """Update state on multiple tickets."""
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )
        return await self._client.bulk_update_state(tickets, state)

    async def bulk_set_iteration(
        self, tickets: list[Ticket], iteration_name: str | None
    ) -> BulkResult:
        """Set iteration on multiple tickets."""
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )
        return await self._client.bulk_set_iteration(tickets, iteration_name)

    async def bulk_update_points(self, tickets: list[Ticket], points: float) -> BulkResult:
        """Update story points on multiple tickets."""
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )
        return await self._client.bulk_update_points(tickets, points)

    async def get_attachments(self, ticket: Ticket) -> list[Attachment]:
        """Get all attachments for a ticket (not cached)."""
        return await self._client.get_attachments(ticket)

    async def download_attachment(
        self, ticket: Ticket, attachment: Attachment, dest_path: str
    ) -> bool:
        """Download attachment content to a local file."""
        return await self._client.download_attachment(ticket, attachment, dest_path)

    async def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None:
        """Upload a local file as an attachment to a ticket."""
        if self._is_offline:
            return None
        return await self._client.upload_attachment(ticket, file_path)

    async def download_embedded_image(self, url: str, dest_path: str) -> bool:
        """Download an embedded image from a URL."""
        return await self._client.download_embedded_image(url, dest_path)

    async def get_users(self, display_names: list[str] | None = None) -> list[Owner]:
        """Fetch Rally users, optionally filtered by display names.

        Args:
            display_names: Optional list of display names to filter by.

        Returns:
            List of Owner objects representing Rally users.
        """
        return await self._client.get_users(display_names)

    async def assign_owner(self, ticket: Ticket, owner: Owner) -> Ticket | None:
        """Assign a ticket to a new owner.

        Updates the ticket in the cache if the assignment succeeds.

        Args:
            ticket: The ticket to update.
            owner: The owner to assign (Owner object with object_id).

        Returns:
            The updated Ticket with new owner, or None on failure.
        """
        if self._is_offline:
            return None

        result = await self._client.assign_owner(ticket, owner)
        if result and self._enabled:
            # Update ticket in cache
            self._update_ticket_in_cache(result)
        return result

    async def bulk_assign_owner(self, tickets: list[Ticket], owner: Owner) -> BulkResult:
        """Assign owner to multiple tickets.

        Updates successfully updated tickets in the cache.

        Args:
            tickets: List of tickets to update.
            owner: The owner to assign to all tickets.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )

        result = await self._client.bulk_assign_owner(tickets, owner)
        if self._enabled:
            # Update all successfully updated tickets in cache
            for updated_ticket in result.updated_tickets:
                self._update_ticket_in_cache(updated_ticket)
        return result

    def _update_ticket_in_cache(self, updated_ticket: Ticket) -> None:
        """Update a ticket in the cache after a mutation.

        Args:
            updated_ticket: The updated ticket to store in cache.
        """
        cached_tickets, metadata = self._cache.get_cached_tickets()
        if cached_tickets:
            found = False
            # Find and replace the ticket in cached list
            for i, cached_ticket in enumerate(cached_tickets):
                if cached_ticket.formatted_id == updated_ticket.formatted_id:
                    cached_tickets[i] = updated_ticket
                    found = True
                    break

            # Only save if ticket was found in cache
            if found:
                self._cache.save_tickets(
                    cached_tickets,
                    workspace=self.workspace,
                    project=self.project,
                )
            else:
                logger.debug(f"Ticket {updated_ticket.formatted_id} not in cache, skipping save")
