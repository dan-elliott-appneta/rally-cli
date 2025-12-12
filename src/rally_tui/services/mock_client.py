"""Mock Rally client for testing."""

from datetime import date, datetime, timedelta, timezone

from rally_tui.models import Discussion, Iteration, Ticket
from rally_tui.models.sample_data import SAMPLE_DISCUSSIONS, SAMPLE_TICKETS
from rally_tui.services.protocol import BulkResult


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
            workspace: Workspace name to report.
            project: Project name to report.
            current_user: Current user's display name.
            current_iteration: Current iteration name.
        """
        self._tickets = tickets if tickets is not None else list(SAMPLE_TICKETS)
        self._discussions: dict[str, list[Discussion]] = (
            discussions if discussions is not None else dict(SAMPLE_DISCUSSIONS)
        )
        self._iterations = iterations if iterations is not None else _generate_sample_iterations()
        self._features = features if features is not None else dict(DEFAULT_FEATURES)
        self._workspace = workspace
        self._project = project
        self._current_user = current_user
        self._current_iteration = current_iteration
        self._next_discussion_id = 300000  # For generating new discussion IDs
        self._next_story_id = 9000  # For generating new User Story IDs
        self._next_defect_id = 9000  # For generating new Defect IDs

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
            created_at=datetime.now(timezone.utc),
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
    ) -> Ticket | None:
        """Create a new ticket.

        Args:
            title: The ticket title/name.
            ticket_type: The entity type ("HierarchicalRequirement" or "Defect").
            description: Optional ticket description.

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
        ticket = Ticket(
            formatted_id=formatted_id,
            name=title,
            ticket_type=internal_type,  # type: ignore[arg-type]
            state="Defined",
            owner=self._current_user,
            description=description,
            iteration=self._current_iteration,
            points=None,
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
        sorted_iters = sorted(
            self._iterations, key=lambda i: i.start_date, reverse=True
        )
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

    def bulk_set_parent(
        self, tickets: list[Ticket], parent_id: str
    ) -> BulkResult:
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

    def bulk_update_state(
        self, tickets: list[Ticket], state: str
    ) -> BulkResult:
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

    def bulk_set_iteration(
        self, tickets: list[Ticket], iteration_name: str | None
    ) -> BulkResult:
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
