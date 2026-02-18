"""Mock Rally client for testing."""

from datetime import UTC, date, datetime, timedelta

from rally_tui.models import Attachment, Discussion, Iteration, Owner, Ticket
from rally_tui.models.sample_data import SAMPLE_DISCUSSIONS, SAMPLE_TICKETS
from rally_tui.services.protocol import BulkResult

# Sample attachments for mock data (keyed by ticket formatted_id)
SAMPLE_ATTACHMENTS: dict[str, list[Attachment]] = {
    "US1234": [
        Attachment(
            name="requirements.pdf",
            size=250880,  # ~245 KB
            content_type="application/pdf",
            object_id="att_001",
        ),
        Attachment(
            name="screenshot.png",
            size=91136,  # ~89 KB
            content_type="image/png",
            object_id="att_002",
        ),
    ],
    "US5678": [
        Attachment(
            name="test-data.csv",
            size=12288,  # ~12 KB
            content_type="text/csv",
            object_id="att_003",
        ),
    ],
}


def _generate_sample_iterations() -> list[Iteration]:
    """Generate sample iterations around today's date."""
    today = date.today()
    # Find the Monday of current week as sprint start approximation
    days_since_monday = today.weekday()
    current_start = today - timedelta(days=days_since_monday)

    iterations = []
    # Previous iteration (2 weeks ago)
    prev_start = current_start - timedelta(days=14)
    prev_end = prev_start + timedelta(days=13)
    iterations.append(
        Iteration(
            object_id="iter_prev",
            name="Sprint 25",
            start_date=prev_start,
            end_date=prev_end,
            state="Accepted",
        )
    )

    # Current iteration
    current_end = current_start + timedelta(days=13)
    iterations.append(
        Iteration(
            object_id="iter_current",
            name="Sprint 26",
            start_date=current_start,
            end_date=current_end,
            state="Committed",
        )
    )

    # Next iteration
    next_start = current_end + timedelta(days=1)
    next_end = next_start + timedelta(days=13)
    iterations.append(
        Iteration(
            object_id="iter_next",
            name="Sprint 27",
            start_date=next_start,
            end_date=next_end,
            state="Planning",
        )
    )

    return iterations


# Default mock features for parent selection
DEFAULT_FEATURES: dict[str, str] = {
    "F59625": "API Platform Modernization Initiative",
    "F59627": "Customer Portal Enhancement Phase 2",
    "F59628": "Infrastructure Reliability Improvements",
}

# Default mock users for owner assignment
MOCK_USERS = [
    {"ObjectID": "100001", "DisplayName": "Alice Johnson", "UserName": "alice@example.com"},
    {"ObjectID": "100002", "DisplayName": "Bob Smith", "UserName": "bob@example.com"},
    {"ObjectID": "100003", "DisplayName": "Carol Davis", "UserName": "carol@example.com"},
    {"ObjectID": "100004", "DisplayName": "David Wilson", "UserName": "david@example.com"},
    {"ObjectID": "100005", "DisplayName": "Emma Brown", "UserName": "emma@example.com"},
]


class MockRallyClient:
    """Mock Rally client for testing and development.

    Implements RallyClientProtocol using in-memory data. Defaults to
    SAMPLE_TICKETS for backward compatibility, but can be initialized
    with custom ticket data for testing specific scenarios.
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
        """Initialize the mock client.

        Args:
            tickets: List of tickets to use. Defaults to SAMPLE_TICKETS.
            discussions: Dict mapping formatted_id to discussions. Defaults to SAMPLE_DISCUSSIONS.
            iterations: List of iterations to use. Defaults to generated sample iterations.
            features: Dict mapping feature ID to name. Defaults to DEFAULT_FEATURES.
            attachments: Dict mapping formatted_id to attachments. Defaults to SAMPLE_ATTACHMENTS.
            workspace: Workspace name to report.
            project: Project name to report.
            current_user: Current user's display name.
            current_iteration: Current iteration name.
        """
        self._tickets = tickets if tickets is not None else list(SAMPLE_TICKETS)
        # Deep copy discussions to avoid test isolation issues (shallow copy shares inner lists)
        self._discussions: dict[str, list[Discussion]] = (
            discussions
            if discussions is not None
            else {k: list(v) for k, v in SAMPLE_DISCUSSIONS.items()}
        )
        self._iterations = iterations if iterations is not None else _generate_sample_iterations()
        self._features = features if features is not None else dict(DEFAULT_FEATURES)
        self._attachments: dict[str, list[Attachment]] = (
            attachments if attachments is not None else dict(SAMPLE_ATTACHMENTS)
        )
        self._workspace = workspace
        self._project = project
        self._current_user = current_user
        self._current_iteration = current_iteration
        self._next_discussion_id = 300000  # For generating new discussion IDs
        self._next_story_id = 9000  # For generating new User Story IDs
        self._next_defect_id = 9000  # For generating new Defect IDs
        self._next_attachment_id = 9000  # For generating new Attachment IDs

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

    def get_discussions(self, ticket: Ticket) -> list[Discussion]:
        """Fetch discussion posts for a ticket.

        Args:
            ticket: The ticket to fetch discussions for.

        Returns:
            List of discussions, ordered by creation date (oldest first).
        """
        discussions = self._discussions.get(ticket.formatted_id, [])
        return sorted(discussions, key=lambda d: d.created_at)

    def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
        """Add a comment to a ticket's discussion.

        Args:
            ticket: The ticket to comment on.
            text: The comment text.

        Returns:
            The created Discussion, or None on failure.
        """
        user = self._current_user or "Test User"
        discussion = Discussion(
            object_id=str(self._next_discussion_id),
            text=text,
            user=user,
            created_at=datetime.now(UTC),
            artifact_id=ticket.formatted_id,
        )
        self._next_discussion_id += 1

        if ticket.formatted_id not in self._discussions:
            self._discussions[ticket.formatted_id] = []
        self._discussions[ticket.formatted_id].append(discussion)

        return discussion

    def update_points(self, ticket: Ticket, points: float) -> Ticket | None:
        """Update a ticket's story points.

        Args:
            ticket: The ticket to update.
            points: The new story points value (supports decimals like 0.5).

        Returns:
            The updated Ticket with new points, or None on failure.
        """
        # Find and update the ticket in our list
        # Convert to int if whole number for cleaner display
        stored_points = int(points) if points == int(points) else points
        for i, t in enumerate(self._tickets):
            if t.formatted_id == ticket.formatted_id:
                updated = Ticket(
                    formatted_id=t.formatted_id,
                    name=t.name,
                    ticket_type=t.ticket_type,
                    state=t.state,
                    owner=t.owner,
                    description=t.description,
                    notes=t.notes,
                    iteration=t.iteration,
                    points=stored_points,
                    object_id=t.object_id,
                    parent_id=t.parent_id,
                )
                self._tickets[i] = updated
                return updated
        return None

    def create_ticket(
        self,
        title: str,
        ticket_type: str,
        description: str = "",
        points: float | None = None,
    ) -> Ticket | None:
        """Create a new ticket.

        Args:
            title: The ticket title/name.
            ticket_type: The entity type ("HierarchicalRequirement" or "Defect").
            description: Optional ticket description.
            points: Optional story points to set on create.

        Returns:
            The created Ticket.
        """
        # Generate formatted ID based on type
        if ticket_type == "HierarchicalRequirement":
            formatted_id = f"US{self._next_story_id}"
            self._next_story_id += 1
            internal_type = "UserStory"
        else:
            formatted_id = f"DE{self._next_defect_id}"
            self._next_defect_id += 1
            internal_type = "Defect"

        # Create the ticket with current user/iteration
        stored_points = None
        if points is not None:
            stored_points = int(points) if points == int(points) else points
        ticket = Ticket(
            formatted_id=formatted_id,
            name=title,
            ticket_type=internal_type,  # type: ignore[arg-type]
            state="Defined",
            owner=self._current_user,
            description=description,
            iteration=self._current_iteration,
            points=stored_points,
            object_id=str(self._next_discussion_id),
        )
        self._next_discussion_id += 1

        # Add to tickets list
        self._tickets.append(ticket)

        return ticket

    def update_state(self, ticket: Ticket, state: str) -> Ticket | None:
        """Update a ticket's workflow state.

        Args:
            ticket: The ticket to update.
            state: The new state value (e.g., "In Progress", "Completed").

        Returns:
            The updated Ticket with new state, or None on failure.
        """
        for i, t in enumerate(self._tickets):
            if t.formatted_id == ticket.formatted_id:
                updated = Ticket(
                    formatted_id=t.formatted_id,
                    name=t.name,
                    ticket_type=t.ticket_type,
                    state=state,
                    owner=t.owner,
                    description=t.description,
                    notes=t.notes,
                    iteration=t.iteration,
                    points=t.points,
                    object_id=t.object_id,
                    parent_id=t.parent_id,
                )
                self._tickets[i] = updated
                return updated
        return None

    def get_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch recent iterations (sprints).

        Args:
            count: Maximum number of iterations to return.

        Returns:
            List of iterations, sorted by start date (most recent first).
        """
        # Sort by start date descending (most recent first)
        sorted_iters = sorted(self._iterations, key=lambda i: i.start_date, reverse=True)
        return sorted_iters[:count]

    def get_feature(self, formatted_id: str) -> tuple[str, str] | None:
        """Fetch a Feature's name by its formatted ID.

        Args:
            formatted_id: The Feature's formatted ID (e.g., "F59625").

        Returns:
            Tuple of (formatted_id, name) if found, None otherwise.
        """
        name = self._features.get(formatted_id)
        if name:
            return (formatted_id, name)
        return None

    def set_parent(self, ticket: Ticket, parent_id: str) -> Ticket | None:
        """Set a ticket's parent Feature.

        Args:
            ticket: The ticket to update.
            parent_id: The parent Feature's formatted ID (e.g., "F59625").

        Returns:
            The updated Ticket with parent_id set, or None on failure.
        """
        for i, t in enumerate(self._tickets):
            if t.formatted_id == ticket.formatted_id:
                updated = Ticket(
                    formatted_id=t.formatted_id,
                    name=t.name,
                    ticket_type=t.ticket_type,
                    state=t.state,
                    owner=t.owner,
                    description=t.description,
                    notes=t.notes,
                    iteration=t.iteration,
                    points=t.points,
                    object_id=t.object_id,
                    parent_id=parent_id,
                )
                self._tickets[i] = updated
                return updated
        return None

    def bulk_set_parent(self, tickets: list[Ticket], parent_id: str) -> BulkResult:
        """Set parent Feature on multiple tickets.

        Only sets parent on tickets that don't already have one.

        Args:
            tickets: List of tickets to update.
            parent_id: The parent Feature's formatted ID.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        result = BulkResult()

        for ticket in tickets:
            # Skip tickets that already have a parent
            if ticket.parent_id:
                continue

            try:
                updated = self.set_parent(ticket, parent_id)
                if updated:
                    result.success_count += 1
                    result.updated_tickets.append(updated)
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Ticket not found")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")

        return result

    def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult:
        """Update state on multiple tickets.

        Args:
            tickets: List of tickets to update.
            state: The new state value.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        result = BulkResult()

        for ticket in tickets:
            try:
                updated = self.update_state(ticket, state)
                if updated:
                    result.success_count += 1
                    result.updated_tickets.append(updated)
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Ticket not found")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")

        return result

    def bulk_set_iteration(self, tickets: list[Ticket], iteration_name: str | None) -> BulkResult:
        """Set iteration on multiple tickets.

        Args:
            tickets: List of tickets to update.
            iteration_name: The iteration name, or None for backlog.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        result = BulkResult()

        for ticket in tickets:
            try:
                # Find and update the ticket
                for i, t in enumerate(self._tickets):
                    if t.formatted_id == ticket.formatted_id:
                        updated = Ticket(
                            formatted_id=t.formatted_id,
                            name=t.name,
                            ticket_type=t.ticket_type,
                            state=t.state,
                            owner=t.owner,
                            description=t.description,
                            notes=t.notes,
                            iteration=iteration_name,
                            points=t.points,
                            object_id=t.object_id,
                            parent_id=t.parent_id,
                        )
                        self._tickets[i] = updated
                        result.success_count += 1
                        result.updated_tickets.append(updated)
                        break
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Ticket not found")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")

        return result

    def bulk_update_points(self, tickets: list[Ticket], points: float) -> BulkResult:
        """Update story points on multiple tickets.

        Args:
            tickets: List of tickets to update.
            points: The new story points value.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        result = BulkResult()

        for ticket in tickets:
            try:
                updated = self.update_points(ticket, points)
                if updated:
                    result.success_count += 1
                    result.updated_tickets.append(updated)
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Ticket not found")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")

        return result

    def get_attachments(self, ticket: Ticket) -> list[Attachment]:
        """Get all attachments for a ticket.

        Args:
            ticket: The ticket to get attachments for.

        Returns:
            List of Attachment objects for the ticket.
        """
        return self._attachments.get(ticket.formatted_id, [])

    def download_attachment(self, ticket: Ticket, attachment: Attachment, dest_path: str) -> bool:
        """Download attachment content to a local file.

        In the mock client, this simulates a successful download without
        actually writing any file content.

        Args:
            ticket: The ticket the attachment belongs to.
            attachment: The attachment to download.
            dest_path: The local path to save the file to.

        Returns:
            True on success (always succeeds in mock).
        """
        # Verify the attachment exists for this ticket
        attachments = self._attachments.get(ticket.formatted_id, [])
        for att in attachments:
            if att.object_id == attachment.object_id:
                return True
        return False

    def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None:
        """Upload a local file as an attachment to a ticket.

        In the mock client, this creates an Attachment record without
        actually reading any file content.

        Args:
            ticket: The ticket to attach the file to.
            file_path: The local path of the file to upload.

        Returns:
            The created Attachment on success.
        """
        import mimetypes
        import os

        # Extract filename from path
        filename = os.path.basename(file_path)

        # Guess MIME type from filename
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = "application/octet-stream"

        # Create the attachment
        attachment = Attachment(
            name=filename,
            size=1024,  # Mock size
            content_type=content_type,
            object_id=f"att_{self._next_attachment_id}",
        )
        self._next_attachment_id += 1

        # Add to the ticket's attachments
        if ticket.formatted_id not in self._attachments:
            self._attachments[ticket.formatted_id] = []
        self._attachments[ticket.formatted_id].append(attachment)

        return attachment

    def download_embedded_image(self, url: str, dest_path: str) -> bool:
        """Download an embedded image from a URL (mock implementation).

        In mock mode, this creates a placeholder file.

        Args:
            url: The URL of the embedded image.
            dest_path: The local path to save the file to.

        Returns:
            True on success, False on failure.
        """
        try:
            # Create a simple placeholder image (1x1 transparent PNG)
            # This is a minimal valid PNG file
            placeholder = bytes(
                [
                    0x89,
                    0x50,
                    0x4E,
                    0x47,
                    0x0D,
                    0x0A,
                    0x1A,
                    0x0A,  # PNG signature
                    0x00,
                    0x00,
                    0x00,
                    0x0D,
                    0x49,
                    0x48,
                    0x44,
                    0x52,  # IHDR chunk
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x01,  # 1x1 image
                    0x08,
                    0x06,
                    0x00,
                    0x00,
                    0x00,
                    0x1F,
                    0x15,
                    0xC4,
                    0x89,
                    0x00,
                    0x00,
                    0x00,
                    0x0A,
                    0x49,
                    0x44,
                    0x41,  # IDAT chunk
                    0x54,
                    0x78,
                    0x9C,
                    0x63,
                    0x00,
                    0x01,
                    0x00,
                    0x00,
                    0x05,
                    0x00,
                    0x01,
                    0x0D,
                    0x0A,
                    0x2D,
                    0xB4,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x49,
                    0x45,
                    0x4E,
                    0x44,
                    0xAE,  # IEND chunk
                    0x42,
                    0x60,
                    0x82,
                ]
            )
            with open(dest_path, "wb") as f:
                f.write(placeholder)
            return True
        except Exception:
            return False

    def get_users(self, display_names: list[str] | None = None) -> list[Owner]:
        """Fetch Rally users, optionally filtered by display names.

        Args:
            display_names: Optional list of display names to filter by.

        Returns:
            List of Owner objects representing Rally users.
        """
        users = MOCK_USERS
        if display_names:
            users = [u for u in users if u["DisplayName"] in display_names]

        return [
            Owner(
                object_id=u["ObjectID"],
                display_name=u["DisplayName"],
                user_name=u.get("UserName"),
            )
            for u in users
        ]

    def assign_owner(self, ticket: Ticket, owner: Owner) -> Ticket | None:
        """Assign a ticket to a new owner.

        Args:
            ticket: The ticket to update.
            owner: The owner to assign (Owner object with object_id).

        Returns:
            The updated Ticket with new owner, or None on failure.
        """
        # Find and update the ticket in our list
        for i, t in enumerate(self._tickets):
            if t.formatted_id == ticket.formatted_id:
                updated = Ticket(
                    formatted_id=t.formatted_id,
                    name=t.name,
                    ticket_type=t.ticket_type,
                    state=t.state,
                    owner=owner.display_name,
                    description=t.description,
                    notes=t.notes,
                    iteration=t.iteration,
                    points=t.points,
                    object_id=t.object_id,
                    parent_id=t.parent_id,
                )
                self._tickets[i] = updated
                return updated
        return None

    def bulk_assign_owner(self, tickets: list[Ticket], owner: Owner) -> BulkResult:
        """Assign owner to multiple tickets.

        Args:
            tickets: List of tickets to update.
            owner: The owner to assign to all tickets.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        result = BulkResult()

        for ticket in tickets:
            try:
                updated = self.assign_owner(ticket, owner)
                if updated:
                    result.success_count += 1
                    result.updated_tickets.append(updated)
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Ticket not found")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")

        return result
