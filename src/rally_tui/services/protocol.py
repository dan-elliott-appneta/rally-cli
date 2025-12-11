"""Protocol defining the Rally client interface."""

from typing import Protocol

from rally_tui.models import Discussion, Ticket


class RallyClientProtocol(Protocol):
    """Protocol defining the interface for Rally clients.

    This protocol uses structural subtyping, meaning any class that implements
    these methods will be compatible without explicit inheritance.
    """

    @property
    def workspace(self) -> str:
        """Get the current workspace name."""
        ...

    @property
    def project(self) -> str:
        """Get the current project name."""
        ...

    @property
    def current_user(self) -> str | None:
        """Get the current user's display name."""
        ...

    @property
    def current_iteration(self) -> str | None:
        """Get the current iteration name."""
        ...

    def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets, optionally filtered by query.

        Args:
            query: Optional search query to filter tickets.

        Returns:
            List of tickets matching the query, or all tickets if no query.
        """
        ...

    def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by its formatted ID.

        Args:
            formatted_id: The ticket's formatted ID (e.g., "US1234").

        Returns:
            The ticket if found, None otherwise.
        """
        ...

    def get_discussions(self, ticket: Ticket) -> list[Discussion]:
        """Fetch discussion posts for a ticket.

        Args:
            ticket: The ticket to fetch discussions for.

        Returns:
            List of discussions, ordered by creation date (oldest first).
        """
        ...

    def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
        """Add a comment to a ticket's discussion.

        Args:
            ticket: The ticket to comment on.
            text: The comment text.

        Returns:
            The created Discussion, or None on failure.
        """
        ...

    def update_points(self, ticket: Ticket, points: float) -> Ticket | None:
        """Update a ticket's story points.

        Args:
            ticket: The ticket to update.
            points: The new story points value (supports decimals like 0.5).

        Returns:
            The updated Ticket with new points, or None on failure.
        """
        ...
