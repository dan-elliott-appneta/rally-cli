"""Protocol defining the Rally client interface."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from rally_tui.models import Attachment, Discussion, Feature, Iteration, Owner, Release, Tag, Ticket


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
        points: float | None = None,
        backlog: bool = False,
    ) -> Ticket | None:
        """Create a new ticket in Rally.

        Creates a ticket with the current user as owner and assigns it
        to the current iteration unless backlog is True.

        Args:
            title: The ticket title/name.
            ticket_type: The entity type ("HierarchicalRequirement" or "Defect").
            description: Optional ticket description.
            points: Optional story points (PlanEstimate) to set on create.
            backlog: If True, do not assign to current iteration (leave in backlog).

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

    def get_iterations(self, count: int = 5, state: str | None = None) -> list[Iteration]:
        """Fetch recent iterations (sprints).

        Returns iterations centered around the current iteration:
        previous iterations, current, and upcoming iterations.

        Args:
            count: Maximum number of iterations to return.
            state: Optional state filter (Planning, Committed, Accepted).

        Returns:
            List of iterations, sorted by start date (newest first).
        """
        ...

    def get_future_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch future iterations (sprints) starting after today.

        Args:
            count: Maximum number of iterations to return.

        Returns:
            List of future iterations, sorted by start date ascending.
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

    def get_features(self, query: str | None = None, count: int = 50) -> list[Feature]:
        """Fetch features (portfolio items) from Rally.

        Args:
            query: Optional Rally query string to filter features.
            count: Maximum number of features to return.

        Returns:
            List of Feature objects.
        """
        ...

    def get_feature_children(self, feature_id: str) -> list[Ticket]:
        """Fetch child user stories for a feature by its formatted ID.

        Args:
            feature_id: The Feature's formatted ID (e.g., "F59625").

        Returns:
            List of Ticket objects representing child user stories.
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

    def bulk_set_parent(self, tickets: list[Ticket], parent_id: str) -> BulkResult:
        """Set parent Feature on multiple tickets.

        Only sets parent on tickets that don't already have one.

        Args:
            tickets: List of tickets to update.
            parent_id: The parent Feature's formatted ID (e.g., "F59625").

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        ...

    def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult:
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

    def bulk_set_iteration(self, tickets: list[Ticket], iteration_name: str | None) -> BulkResult:
        """Set iteration on multiple tickets.

        Args:
            tickets: List of tickets to update.
            iteration_name: The iteration name, or None for backlog (no iteration).

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        ...

    def bulk_update_points(self, tickets: list[Ticket], points: float) -> BulkResult:
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

    def download_attachment(self, ticket: Ticket, attachment: Attachment, dest_path: str) -> bool:
        """Download attachment content to a local file.

        Args:
            ticket: The ticket the attachment belongs to.
            attachment: The attachment to download.
            dest_path: The local path to save the file to.

        Returns:
            True on success, False on failure.
        """
        ...

    def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None:
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

    def get_users(self, display_names: list[str] | None = None) -> list[Owner]:
        """Fetch Rally users, optionally filtered by display names.

        Args:
            display_names: Optional list of display names to filter by.
                          If None, returns all users in the project.

        Returns:
            List of Owner objects representing Rally users.
        """
        ...

    def assign_owner(self, ticket: Ticket, owner: Owner) -> Ticket | None:
        """Assign a ticket to a new owner.

        Args:
            ticket: The ticket to update.
            owner: The owner to assign (Owner object with object_id).

        Returns:
            The updated Ticket with new owner, or None on failure.
        """
        ...

    def bulk_assign_owner(self, tickets: list[Ticket], owner: Owner) -> BulkResult:
        """Assign owner to multiple tickets.

        Args:
            tickets: List of tickets to update.
            owner: The owner to assign to all tickets.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        ...

    def get_releases(self, count: int = 10, state: str | None = None) -> list[Release]:
        """Fetch releases, optionally filtered by state.

        Args:
            count: Maximum number of releases to return.
            state: Optional state filter (Planning, Active, Locked).

        Returns:
            List of releases, sorted by start date (newest first).
        """
        ...

    def get_release(self, name: str) -> Release | None:
        """Fetch a single release by name.

        Args:
            name: The release name to search for.

        Returns:
            The Release if found, None otherwise.
        """
        ...

    def set_release(self, ticket: Ticket, release_name: str | None) -> Ticket | None:
        """Set or remove release assignment on a ticket.

        Args:
            ticket: The ticket to update.
            release_name: The release name to assign, or None to remove.

        Returns:
            The updated Ticket, or None on failure.
        """
        ...

    def get_tags(self) -> list[Tag]:
        """Fetch all tags in the workspace.

        Returns:
            List of Tag objects sorted by name.
        """
        ...

    def add_tag(self, ticket: Ticket, tag_name: str) -> bool:
        """Add a tag to a ticket. Creates the tag if it doesn't exist.

        Args:
            ticket: The ticket to tag.
            tag_name: The tag name to add.

        Returns:
            True on success, False on failure.
        """
        ...

    def remove_tag(self, ticket: Ticket, tag_name: str) -> bool:
        """Remove a tag from a ticket.

        Args:
            ticket: The ticket to untag.
            tag_name: The tag name to remove.

        Returns:
            True on success, False on failure.
        """
        ...

    def create_tag(self, name: str) -> Tag | None:
        """Create a new tag.

        Args:
            name: The tag name.

        Returns:
            The created Tag, or None on failure.
        """
        ...

    def update_ticket(self, ticket: Ticket, fields: dict[str, Any]) -> Ticket | None:
        """Update arbitrary fields on a ticket.

        Special field handling:
        - 'state'     -> looks up FlowState reference by name
        - 'owner'     -> looks up Owner user by display name
        - 'iteration' -> looks up Iteration by name (None removes iteration)
        - 'parent'    -> looks up Feature by formatted ID

        Args:
            ticket: The ticket to update.
            fields: Dict of field names/aliases to new values.

        Returns:
            The updated Ticket (re-fetched from Rally), or None on failure.
        """
        ...

    def delete_ticket(self, formatted_id: str) -> bool:
        """Delete a ticket from Rally.

        Args:
            formatted_id: The ticket's formatted ID (e.g., "US1234").

        Returns:
            True on success, False on failure.
        """
        ...
