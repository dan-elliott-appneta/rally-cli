"""Caching wrapper for Rally client with stale-while-revalidate strategy."""

from __future__ import annotations

import logging
from typing import Any

from rally_tui.models import Attachment, Discussion, Feature, Iteration, Owner, Release, Tag, Ticket
from rally_tui.services.caching_base import BaseCachingClient, CacheStatus
from rally_tui.services.protocol import BulkResult

logger = logging.getLogger(__name__)


class CachingRallyClient(BaseCachingClient):
    """Wraps a RallyClient with a caching layer.

    Implements stale-while-revalidate caching:
    - On get_tickets(): Return cached data immediately if available
    - Trigger background refresh if cache is stale
    - Cache is invalidated when workspace/project changes

    All write operations (update_state, update_points, etc.) are passed
    through to the underlying client without caching.
    """

    # Core caching methods

    def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Get tickets, using cache if available.

        Cache-first strategy:
        1. If cache disabled, fetch from API
        2. If query provided (iteration filter), bypass cache and fetch from API
        3. If cache exists and valid, return cached data
        4. If cache exists but stale, return cached + trigger refresh
        5. If no cache, fetch from API

        Args:
            query: Optional query (passed to underlying client).
                   When provided, cache is bypassed to ensure fresh data.

        Returns:
            List of tickets (may be cached)
        """
        if not self._enabled:
            return self._fetch_from_api(query)

        # When a specific query is provided (e.g., iteration filter),
        # bypass cache and fetch fresh data from API
        if query:
            logger.info(f"Query provided, bypassing cache: {query}")
            return self._fetch_from_api(query)

        # Check if cache is for correct workspace/project
        if not self._cache.is_cache_for_project(self.workspace, self.project):
            logger.info("Cache is for different project, fetching fresh data")
            return self._fetch_from_api(query)

        # Try to get cached tickets
        cached_tickets, metadata = self._cache.get_cached_tickets()

        if cached_tickets:
            # Determine if cache is stale
            is_stale = not self._cache.is_cache_valid(self._ttl)

            if is_stale and self._auto_refresh:
                logger.info("Cache is stale, returning cached and will refresh")
                self._set_status(CacheStatus.CACHED)
                # Note: Actual background refresh is handled by the app layer
                # This just signals that refresh should happen
            else:
                self._set_status(CacheStatus.CACHED)

            return cached_tickets

        # No cache, fetch from API
        return self._fetch_from_api(query)

    def _fetch_from_api(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets from the underlying API.

        Args:
            query: Optional query filter. When provided, results are NOT cached
                   to avoid overwriting the full ticket cache with filtered data.

        Returns:
            List of tickets from API

        Note:
            Sets offline mode if API call fails.
            Only caches results when no query is provided.
        """
        try:
            self._set_status(CacheStatus.REFRESHING)
            tickets = self._client.get_tickets(query)

            # Only save to cache when fetching all tickets (no query)
            # Filtered results should not overwrite the full ticket cache
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

    def refresh_cache(self) -> list[Ticket]:
        """Force refresh tickets from API and update cache.

        Returns:
            Fresh list of tickets from API
        """
        return self._fetch_from_api()

    # Pass-through methods (no caching for single item or write operations)

    def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by ID (not cached)."""
        return self._client.get_ticket(formatted_id)

    def get_discussions(self, ticket: Ticket) -> list[Discussion]:
        """Fetch discussions for a ticket (not cached)."""
        return self._client.get_discussions(ticket)

    def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
        """Add a comment to a ticket."""
        if self._is_offline:
            return None
        return self._client.add_comment(ticket, text)

    def update_points(self, ticket: Ticket, points: float) -> Ticket | None:
        """Update a ticket's story points."""
        if self._is_offline:
            return None
        return self._client.update_points(ticket, points)

    def create_ticket(
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
        return self._client.create_ticket(title, ticket_type, description, points, backlog)

    def update_state(self, ticket: Ticket, state: str) -> Ticket | None:
        """Update a ticket's workflow state."""
        if self._is_offline:
            return None
        return self._client.update_state(ticket, state)

    def update_ticket(self, ticket: Ticket, fields: dict[str, Any]) -> Ticket | None:
        """Update arbitrary fields on a ticket."""
        if self._is_offline:
            return None
        return self._client.update_ticket(ticket, fields)

    def delete_ticket(self, formatted_id: str) -> bool:
        """Delete a ticket from Rally."""
        if self._is_offline:
            return False
        return self._client.delete_ticket(formatted_id)

    def get_iterations(self, count: int = 5, state: str | None = None) -> list[Iteration]:
        """Fetch recent iterations (not cached)."""
        return self._client.get_iterations(count, state=state)

    def get_future_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch future iterations (not cached)."""
        return self._client.get_future_iterations(count)

    def get_feature(self, formatted_id: str) -> tuple[str, str] | None:
        """Fetch a Feature's name by ID (not cached)."""
        return self._client.get_feature(formatted_id)

    def get_features(self, query: str | None = None, count: int = 50) -> list[Feature]:
        """Fetch features (portfolio items) (not cached)."""
        return self._client.get_features(query, count)

    def get_feature_children(self, feature_id: str) -> list[Ticket]:
        """Fetch child user stories for a feature (not cached)."""
        return self._client.get_feature_children(feature_id)

    def set_parent(self, ticket: Ticket, parent_id: str) -> Ticket | None:
        """Set a ticket's parent Feature."""
        if self._is_offline:
            return None
        return self._client.set_parent(ticket, parent_id)

    def bulk_set_parent(self, tickets: list[Ticket], parent_id: str) -> BulkResult:
        """Set parent Feature on multiple tickets."""
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )
        return self._client.bulk_set_parent(tickets, parent_id)

    def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult:
        """Update state on multiple tickets."""
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )
        return self._client.bulk_update_state(tickets, state)

    def bulk_set_iteration(self, tickets: list[Ticket], iteration_name: str | None) -> BulkResult:
        """Set iteration on multiple tickets."""
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )
        return self._client.bulk_set_iteration(tickets, iteration_name)

    def bulk_update_points(self, tickets: list[Ticket], points: float) -> BulkResult:
        """Update story points on multiple tickets."""
        if self._is_offline:
            return BulkResult(
                failed_count=len(tickets),
                errors=["Cannot update tickets while offline"],
            )
        return self._client.bulk_update_points(tickets, points)

    def get_attachments(self, ticket: Ticket) -> list[Attachment]:
        """Get all attachments for a ticket (not cached)."""
        return self._client.get_attachments(ticket)

    def download_attachment(self, ticket: Ticket, attachment: Attachment, dest_path: str) -> bool:
        """Download attachment content to a local file."""
        return self._client.download_attachment(ticket, attachment, dest_path)

    def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None:
        """Upload a local file as an attachment to a ticket."""
        if self._is_offline:
            return None
        return self._client.upload_attachment(ticket, file_path)

    def download_embedded_image(self, url: str, dest_path: str) -> bool:
        """Download an embedded image from a URL."""
        return self._client.download_embedded_image(url, dest_path)

    def get_users(self, display_names: list[str] | None = None) -> list[Owner]:
        """Fetch Rally users, optionally filtered by display names.

        Args:
            display_names: Optional list of display names to filter by.

        Returns:
            List of Owner objects representing Rally users.
        """
        return self._client.get_users(display_names)

    def assign_owner(self, ticket: Ticket, owner: Owner) -> Ticket | None:
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

        result = self._client.assign_owner(ticket, owner)
        if result and self._enabled:
            # Update ticket in cache
            self._update_ticket_in_cache(result)
        return result

    def bulk_assign_owner(self, tickets: list[Ticket], owner: Owner) -> BulkResult:
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

        result = self._client.bulk_assign_owner(tickets, owner)
        if self._enabled:
            # Update all successfully updated tickets in cache
            for updated_ticket in result.updated_tickets:
                self._update_ticket_in_cache(updated_ticket)
        return result

    # Release & Tag pass-through methods

    def get_releases(self, count: int = 10, state: str | None = None) -> list[Release]:
        """Fetch releases (not cached)."""
        return self._client.get_releases(count, state)

    def get_release(self, name: str) -> Release | None:
        """Fetch a single release by name (not cached)."""
        return self._client.get_release(name)

    def set_release(self, ticket: Ticket, release_name: str | None) -> Ticket | None:
        """Set or remove release assignment on a ticket."""
        if self._is_offline:
            return None
        return self._client.set_release(ticket, release_name)

    def get_tags(self) -> list[Tag]:
        """Fetch all tags (not cached)."""
        return self._client.get_tags()

    def add_tag(self, ticket: Ticket, tag_name: str) -> bool:
        """Add a tag to a ticket."""
        if self._is_offline:
            return False
        return self._client.add_tag(ticket, tag_name)

    def remove_tag(self, ticket: Ticket, tag_name: str) -> bool:
        """Remove a tag from a ticket."""
        if self._is_offline:
            return False
        return self._client.remove_tag(ticket, tag_name)

    def create_tag(self, name: str) -> Tag | None:
        """Create a new tag."""
        if self._is_offline:
            return None
        return self._client.create_tag(name)

    def search_tickets(
        self,
        text: str,
        ticket_type: str | None = None,
        state: str | None = None,
        current_iteration: bool = False,
        limit: int = 50,
    ) -> list[Ticket]:
        """Search tickets by full-text. Passthrough to underlying client."""
        return self._client.search_tickets(
            text=text,
            ticket_type=ticket_type,
            state=state,
            current_iteration=current_iteration,
            limit=limit,
        )

    def get_sprint_summary(self, iteration_name: str | None = None) -> dict:
        """Fetch sprint summary. Passthrough to underlying client."""
        return self._client.get_sprint_summary(iteration_name)
