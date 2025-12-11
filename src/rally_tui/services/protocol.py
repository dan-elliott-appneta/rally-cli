"""Protocol defining the Rally client interface."""

from typing import Protocol

from rally_tui.models import Ticket


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
