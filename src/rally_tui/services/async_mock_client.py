"""Async mock Rally client for testing.

This module provides an async-compatible mock client that wraps the sync
MockRallyClient for use in async tests and development.
"""

from __future__ import annotations

from typing import Any

from rally_tui.models import Attachment, Discussion, Iteration, Owner, Ticket
from rally_tui.services.mock_client import MockRallyClient
from rally_tui.services.protocol import BulkResult

# Re-export for type checking
__all__ = ["AsyncMockRallyClient"]


class AsyncMockRallyClient:
    """Async wrapper around MockRallyClient for testing.

    This client provides async versions of all MockRallyClient methods,
    enabling async tests without making real API calls.

    Usage:
        async with AsyncMockRallyClient() as client:
            tickets = await client.get_tickets()
    """

    def __init__(
        self,
        tickets: list[Ticket] | None = None,
        discussions: dict[str, list[Discussion]] | None = None,
        iterations: list[Iteration] | None = None,
        features: dict[str, str] | None = None,
        attachments: dict[str, list[Attachment]] | None = None,
        workspace: str = "My Workspace",
        project: str = "My Project",
        current_user: str | None = None,
        current_iteration: str | None = None,
    ) -> None:
        """Initialize the async mock client.

        Args:
            tickets: List of tickets to use.
            discussions: Dict mapping formatted_id to discussions.
            iterations: List of iterations to use.
            features: Dict mapping feature ID to name.
            attachments: Dict mapping formatted_id to attachments.
            workspace: Workspace name to report.
            project: Project name to report.
            current_user: Current user's display name.
            current_iteration: Current iteration name.
        """
        self._sync_client = MockRallyClient(
            tickets=tickets,
            discussions=discussions,
            iterations=iterations,
            features=features,
            attachments=attachments,
            workspace=workspace,
            project=project,
            current_user=current_user,
            current_iteration=current_iteration,
        )

    async def __aenter__(self) -> AsyncMockRallyClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize client (no-op for mock)."""
        pass

    async def close(self) -> None:
        """Close client (no-op for mock)."""
        pass

    @property
    def workspace(self) -> str:
        """Get the workspace name."""
        return self._sync_client.workspace

    @property
    def project(self) -> str:
        """Get the project name."""
        return self._sync_client.project

    @property
    def current_user(self) -> str | None:
        """Get the current user's display name."""
        return self._sync_client.current_user

    @property
    def current_iteration(self) -> str | None:
        """Get the current iteration name."""
        return self._sync_client.current_iteration

    # -------------------------------------------------------------------------
    # Async Ticket Operations
    # -------------------------------------------------------------------------

    async def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets asynchronously."""
        return self._sync_client.get_tickets(query)

    async def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by formatted ID."""
        return self._sync_client.get_ticket(formatted_id)

    # -------------------------------------------------------------------------
    # Async Discussion Operations
    # -------------------------------------------------------------------------

    async def get_discussions(self, ticket: Ticket) -> list[Discussion]:
        """Fetch discussions for a ticket."""
        return self._sync_client.get_discussions(ticket)

    async def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
        """Add a comment to a ticket's discussion."""
        return self._sync_client.add_comment(ticket, text)

    # -------------------------------------------------------------------------
    # Async Update Operations
    # -------------------------------------------------------------------------

    async def update_points(self, ticket: Ticket, points: float) -> Ticket | None:
        """Update a ticket's story points."""
        return self._sync_client.update_points(ticket, points)

    async def update_state(self, ticket: Ticket, state: str) -> Ticket | None:
        """Update a ticket's workflow state."""
        return self._sync_client.update_state(ticket, state)

    async def create_ticket(
        self,
        title: str,
        ticket_type: str,
        description: str = "",
        points: float | None = None,
        backlog: bool = False,
    ) -> Ticket | None:
        """Create a new ticket."""
        return self._sync_client.create_ticket(title, ticket_type, description, points, backlog)

    # -------------------------------------------------------------------------
    # Async Iteration Operations
    # -------------------------------------------------------------------------

    async def get_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch recent iterations."""
        return self._sync_client.get_iterations(count)

    # -------------------------------------------------------------------------
    # Async Feature/Parent Operations
    # -------------------------------------------------------------------------

    async def get_feature(self, formatted_id: str) -> tuple[str, str] | None:
        """Fetch a Feature's name by formatted ID."""
        return self._sync_client.get_feature(formatted_id)

    async def set_parent(self, ticket: Ticket, parent_id: str) -> Ticket | None:
        """Set a ticket's parent Feature."""
        return self._sync_client.set_parent(ticket, parent_id)

    # -------------------------------------------------------------------------
    # Async Bulk Operations
    # -------------------------------------------------------------------------

    async def bulk_set_parent(self, tickets: list[Ticket], parent_id: str) -> BulkResult:
        """Set parent Feature on multiple tickets."""
        return self._sync_client.bulk_set_parent(tickets, parent_id)

    async def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult:
        """Update state on multiple tickets."""
        return self._sync_client.bulk_update_state(tickets, state)

    async def bulk_set_iteration(
        self, tickets: list[Ticket], iteration_name: str | None
    ) -> BulkResult:
        """Set iteration on multiple tickets."""
        return self._sync_client.bulk_set_iteration(tickets, iteration_name)

    async def bulk_update_points(self, tickets: list[Ticket], points: float) -> BulkResult:
        """Update story points on multiple tickets."""
        return self._sync_client.bulk_update_points(tickets, points)

    # -------------------------------------------------------------------------
    # Async Attachment Operations
    # -------------------------------------------------------------------------

    async def get_attachments(self, ticket: Ticket) -> list[Attachment]:
        """Get all attachments for a ticket."""
        return self._sync_client.get_attachments(ticket)

    async def download_attachment(
        self, ticket: Ticket, attachment: Attachment, dest_path: str
    ) -> bool:
        """Download attachment content to a local file."""
        return self._sync_client.download_attachment(ticket, attachment, dest_path)

    async def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None:
        """Upload a local file as an attachment."""
        return self._sync_client.upload_attachment(ticket, file_path)

    async def download_embedded_image(self, url: str, dest_path: str) -> bool:
        """Download an embedded image from a URL."""
        return self._sync_client.download_embedded_image(url, dest_path)

    async def get_users(self, display_names: list[str] | None = None) -> list[Owner]:
        """Fetch Rally users, optionally filtered by display names.

        Args:
            display_names: Optional list of display names to filter by.

        Returns:
            List of Owner objects representing Rally users.
        """
        return self._sync_client.get_users(display_names)

    async def assign_owner(self, ticket: Ticket, owner: Owner) -> Ticket | None:
        """Assign a ticket to a new owner.

        Args:
            ticket: The ticket to update.
            owner: The owner to assign (Owner object with object_id).

        Returns:
            The updated Ticket with new owner, or None on failure.
        """
        return self._sync_client.assign_owner(ticket, owner)

    async def bulk_assign_owner(self, tickets: list[Ticket], owner: Owner) -> BulkResult:
        """Assign owner to multiple tickets.

        Args:
            tickets: List of tickets to update.
            owner: The owner to assign to all tickets.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        return self._sync_client.bulk_assign_owner(tickets, owner)

    async def update_ticket(self, ticket: Ticket, fields: dict[str, Any]) -> Ticket | None:
        """Update arbitrary fields on a ticket.

        Args:
            ticket: The ticket to update.
            fields: Dict of field names to new values.

        Returns:
            The updated Ticket, or None on failure.
        """
        return self._sync_client.update_ticket(ticket, fields)

    async def delete_ticket(self, formatted_id: str) -> bool:
        """Delete a ticket from Rally.

        Args:
            formatted_id: The ticket's formatted ID (e.g., "US1234").

        Returns:
            True on success, False on failure.
        """
        return self._sync_client.delete_ticket(formatted_id)
