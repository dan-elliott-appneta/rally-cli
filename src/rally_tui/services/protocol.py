"""Protocol defining the Rally client interface."""

from dataclasses import dataclass, field
from typing import Protocol

from rally_tui.models import Attachment, Discussion, Iteration, Ticket


@dataclass
class BulkResult:
    """Result of a bulk operation on multiple tickets.

    Attributes:
        success_count: Number of tickets successfully updated.
        failed_count: Number of tickets that failed to update.
        updated_tickets: List of successfully updated Ticket objects.
        errors: List of error messages for failed updates.
    """

    success_count: int = 0
    failed_count: int = 0
    updated_tickets: list[Ticket] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


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

    def create_ticket(
        self,
        title: str,
        ticket_type: str,
        description: str = "",
    ) -> Ticket | None:
        """Create a new ticket in Rally.

        Creates a ticket with the current user as owner and assigns it
        to the current iteration.

        Args:
            title: The ticket title/name.
            ticket_type: The entity type ("HierarchicalRequirement" or "Defect").
            description: Optional ticket description.

        Returns:
            The created Ticket, or None on failure.
        """
        ...

    def update_state(self, ticket: Ticket, state: str) -> Ticket | None:
        """Update a ticket's workflow state.

        Args:
            ticket: The ticket to update.
            state: The new state value (e.g., "In Progress", "Completed").

        Returns:
            The updated Ticket with new state, or None on failure.
        """
        ...

    def get_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch recent iterations (sprints).

        Returns iterations centered around the current iteration:
        previous iterations, current, and upcoming iterations.

        Args:
            count: Maximum number of iterations to return.

        Returns:
            List of iterations, sorted by start date (newest first).
        """
        ...

    def get_feature(self, formatted_id: str) -> tuple[str, str] | None:
        """Fetch a Feature's name by its formatted ID.

        Args:
            formatted_id: The Feature's formatted ID (e.g., "F59625").

        Returns:
            Tuple of (formatted_id, name) if found, None otherwise.
        """
        ...

    def set_parent(self, ticket: Ticket, parent_id: str) -> Ticket | None:
        """Set a ticket's parent Feature.

        Args:
            ticket: The ticket to update.
            parent_id: The parent Feature's formatted ID (e.g., "F59625").

        Returns:
            The updated Ticket with parent_id set, or None on failure.
        """
        ...

    def bulk_set_parent(
        self, tickets: list[Ticket], parent_id: str
    ) -> BulkResult:
        """Set parent Feature on multiple tickets.

        Only sets parent on tickets that don't already have one.

        Args:
            tickets: List of tickets to update.
            parent_id: The parent Feature's formatted ID (e.g., "F59625").

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        ...

    def bulk_update_state(
        self, tickets: list[Ticket], state: str
    ) -> BulkResult:
        """Update state on multiple tickets.

        Note: Does NOT enforce parent requirement for "In-Progress" state.
        Caller should filter tickets appropriately before bulk state change.

        Args:
            tickets: List of tickets to update.
            state: The new state value (e.g., "In-Progress", "Completed").

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        ...

    def bulk_set_iteration(
        self, tickets: list[Ticket], iteration_name: str | None
    ) -> BulkResult:
        """Set iteration on multiple tickets.

        Args:
            tickets: List of tickets to update.
            iteration_name: The iteration name, or None for backlog (no iteration).

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        ...

    def bulk_update_points(
        self, tickets: list[Ticket], points: float
    ) -> BulkResult:
        """Update story points on multiple tickets.

        Args:
            tickets: List of tickets to update.
            points: The new story points value.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        ...

    def get_attachments(self, ticket: Ticket) -> list[Attachment]:
        """Get all attachments for a ticket.

        Args:
            ticket: The ticket to get attachments for.

        Returns:
            List of Attachment objects for the ticket.
        """
        ...

    def download_attachment(
        self, ticket: Ticket, attachment: Attachment, dest_path: str
    ) -> bool:
        """Download attachment content to a local file.

        Args:
            ticket: The ticket the attachment belongs to.
            attachment: The attachment to download.
            dest_path: The local path to save the file to.

        Returns:
            True on success, False on failure.
        """
        ...

    def upload_attachment(
        self, ticket: Ticket, file_path: str
    ) -> Attachment | None:
        """Upload a local file as an attachment to a ticket.

        Args:
            ticket: The ticket to attach the file to.
            file_path: The local path of the file to upload.

        Returns:
            The created Attachment on success, None on failure.
        """
        ...

    def download_embedded_image(self, url: str, dest_path: str) -> bool:
        """Download an embedded image from a URL.

        Embedded images in Rally descriptions are referenced by URL.
        This method downloads the image content to a local file.

        Args:
            url: The URL of the embedded image.
            dest_path: The local path to save the file to.

        Returns:
            True on success, False on failure.
        """
        ...
