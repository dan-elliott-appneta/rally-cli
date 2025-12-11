"""Rally API client implementation."""

from typing import TYPE_CHECKING, Any

from pyral import Rally

from rally_tui.config import RallyConfig
from rally_tui.models import Ticket

if TYPE_CHECKING:
    pass


class RallyClient:
    """Rally API client using pyral.

    Implements RallyClientProtocol for seamless integration with the app.
    Connects to the real Rally API to fetch tickets.
    """

    def __init__(self, config: RallyConfig) -> None:
        """Initialize the Rally client.

        Args:
            config: Rally configuration with API key and connection details.

        Raises:
            Exception: If connection to Rally fails.
        """
        self._config = config
        self._rally = Rally(
            config.server,
            apikey=config.apikey,
            workspace=config.workspace or None,
            project=config.project or None,
        )
        # Cache workspace/project names from connection
        self._workspace = config.workspace or self._rally.getWorkspace().Name
        self._project = config.project or self._rally.getProject().Name

        # Get current user from API
        self._current_user = self._fetch_current_user()

        # Get current iteration from API
        self._current_iteration = self._fetch_current_iteration()

    def _fetch_current_user(self) -> str | None:
        """Fetch the current user's display name from the API.

        Queries the User entity - Rally returns the API key's user first.

        Returns:
            The current user's display name, or None if not available.
        """
        try:
            response = self._rally.get(
                "User",
                fetch="DisplayName",
                pagesize=1,
            )
            for user in response:
                return user.DisplayName
        except Exception:
            pass
        return None

    def _fetch_current_iteration(self) -> str | None:
        """Fetch the current iteration name from the API.

        Queries for iterations where today falls between StartDate and EndDate.

        Returns:
            The current iteration name, or None if not found.
        """
        from datetime import datetime, timezone

        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            # Rally WSAPI requires nested parentheses for AND queries
            response = self._rally.get(
                "Iteration",
                fetch="Name,StartDate,EndDate",
                query=f'((StartDate <= "{today}") AND (EndDate >= "{today}"))',
                order="StartDate desc",
                pagesize=1,
            )
            for iteration in response:
                return iteration.Name
        except Exception:
            pass
        return None

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

    def _build_default_query(self) -> str | None:
        """Build the default query for current user and iteration.

        Returns:
            A Rally query string filtering by current user and iteration,
            or None if neither is available.
        """
        conditions = []

        if self._current_iteration:
            conditions.append(f'(Iteration.Name = "{self._current_iteration}")')

        if self._current_user:
            conditions.append(f'(Owner.DisplayName = "{self._current_user}")')

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        # Rally WSAPI requires format: ((condition1) AND (condition2))
        return f"({conditions[0]} AND {conditions[1]})"

    def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets from Rally.

        Fetches User Stories, Defects, and Tasks from the configured
        workspace/project. By default, filters to tickets in the current
        iteration owned by the current user.

        Args:
            query: Optional Rally query string for filtering. If provided,
                   overrides the default filter.

        Returns:
            List of tickets matching the query.
        """
        tickets: list[Ticket] = []

        # Use provided query or build default filter
        effective_query = query if query is not None else self._build_default_query()

        # Fetch different artifact types
        for entity_type in ["HierarchicalRequirement", "Defect", "Task"]:
            try:
                response = self._rally.get(
                    entity_type,
                    fetch="FormattedID,Name,ScheduleState,State,Owner,Description,Iteration,PlanEstimate",
                    query=effective_query,
                    pagesize=200,
                )

                for item in response:
                    tickets.append(self._to_ticket(item, entity_type))
            except Exception:
                # Skip entity types that fail (e.g., no permission)
                continue

        return tickets

    def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by formatted ID.

        Args:
            formatted_id: The ticket's formatted ID (e.g., "US1234").

        Returns:
            The ticket if found, None otherwise.
        """
        entity_type = self._get_entity_type(formatted_id)

        try:
            response = self._rally.get(
                entity_type,
                fetch="FormattedID,Name,ScheduleState,State,Owner,Description,Iteration,PlanEstimate",
                query=f'FormattedID = "{formatted_id}"',
            )

            item = response.next()
            return self._to_ticket(item, entity_type)
        except StopIteration:
            return None
        except Exception:
            return None

    def _to_ticket(self, item: Any, entity_type: str) -> Ticket:
        """Convert a pyral entity to our Ticket model.

        Args:
            item: The pyral entity object.
            entity_type: The Rally entity type name.

        Returns:
            A Ticket instance.
        """
        # Map entity type to our TicketType
        type_map = {
            "HierarchicalRequirement": "UserStory",
            "Defect": "Defect",
            "Task": "Task",
            "TestCase": "TestCase",
        }
        ticket_type = type_map.get(entity_type, "UserStory")

        # Extract owner name (Owner is a nested object)
        owner = None
        if hasattr(item, "Owner") and item.Owner:
            owner = getattr(item.Owner, "Name", None) or getattr(
                item.Owner, "_refObjectName", None
            )

        # Extract iteration name
        iteration = None
        if hasattr(item, "Iteration") and item.Iteration:
            iteration = getattr(item.Iteration, "Name", None) or getattr(
                item.Iteration, "_refObjectName", None
            )

        # Extract points (PlanEstimate)
        points = None
        if hasattr(item, "PlanEstimate") and item.PlanEstimate is not None:
            try:
                points = int(item.PlanEstimate)
            except (ValueError, TypeError):
                points = None

        # Get state - use ScheduleState for stories/tasks, State for defects
        state = getattr(item, "ScheduleState", None) or getattr(
            item, "State", "Unknown"
        )

        # Get description, handle None
        description = getattr(item, "Description", "") or ""

        return Ticket(
            formatted_id=item.FormattedID,
            name=item.Name,
            ticket_type=ticket_type,  # type: ignore[arg-type]
            state=state,
            owner=owner,
            description=description,
            iteration=iteration,
            points=points,
        )

    def _get_entity_type(self, formatted_id: str) -> str:
        """Determine Rally entity type from formatted ID prefix.

        Args:
            formatted_id: The ticket's formatted ID.

        Returns:
            The Rally entity type name.
        """
        prefix = ""
        for char in formatted_id:
            if char.isdigit():
                break
            prefix += char

        prefix_map = {
            "US": "HierarchicalRequirement",
            "DE": "Defect",
            "TA": "Task",
            "TC": "TestCase",
        }
        return prefix_map.get(prefix.upper(), "HierarchicalRequirement")
