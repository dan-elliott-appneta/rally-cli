"""Mock Rally client for testing."""

from rally_tui.models import Ticket
from rally_tui.models.sample_data import SAMPLE_TICKETS


class MockRallyClient:
    """Mock Rally client for testing and development.

    Implements RallyClientProtocol using in-memory data. Defaults to
    SAMPLE_TICKETS for backward compatibility, but can be initialized
    with custom ticket data for testing specific scenarios.
    """

    def __init__(
        self,
        tickets: list[Ticket] | None = None,
        workspace: str = "My Workspace",
        project: str = "My Project",
        current_user: str | None = None,
        current_iteration: str | None = None,
    ) -> None:
        """Initialize the mock client.

        Args:
            tickets: List of tickets to use. Defaults to SAMPLE_TICKETS.
            workspace: Workspace name to report.
            project: Project name to report.
            current_user: Current user's display name.
            current_iteration: Current iteration name.
        """
        self._tickets = tickets if tickets is not None else list(SAMPLE_TICKETS)
        self._workspace = workspace
        self._project = project
        self._current_user = current_user
        self._current_iteration = current_iteration

    @property
    def workspace(self) -> str:
        """Get the workspace name."""
        return self._workspace

    @property
    def project(self) -> str:
        """Get the project name."""
        return self._project

    @property
    def current_user(self) -> str | None:
        """Get the current user's display name."""
        return self._current_user

    @property
    def current_iteration(self) -> str | None:
        """Get the current iteration name."""
        return self._current_iteration

    def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets, optionally filtered by query.

        Args:
            query: Optional search string to filter by ticket name.

        Returns:
            List of matching tickets.
        """
        if query is None:
            return self._tickets
        # Simple case-insensitive filter on name and formatted_id
        query_lower = query.lower()
        return [
            t
            for t in self._tickets
            if query_lower in t.name.lower() or query_lower in t.formatted_id.lower()
        ]

    def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by its formatted ID.

        Args:
            formatted_id: The ticket's formatted ID (e.g., "US1234").

        Returns:
            The ticket if found, None otherwise.
        """
        for ticket in self._tickets:
            if ticket.formatted_id == formatted_id:
                return ticket
        return None
