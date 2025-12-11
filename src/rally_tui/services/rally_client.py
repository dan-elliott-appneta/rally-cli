"""Rally API client implementation."""

from datetime import date, datetime
from typing import Any

from pyral import Rally

from rally_tui.config import RallyConfig
from rally_tui.models import Discussion, Iteration, Ticket
from rally_tui.utils import get_logger

_log = get_logger("rally_tui.services.rally_client")


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
        _log.debug(f"Initializing Rally client for server: {config.server}")
        self._config = config

        try:
            self._rally = Rally(
                config.server,
                apikey=config.apikey,
                workspace=config.workspace or None,
                project=config.project or None,
            )
            # Cache workspace/project names from connection
            self._workspace = config.workspace or self._rally.getWorkspace().Name
            self._project = config.project or self._rally.getProject().Name
            _log.info(f"Connected to Rally workspace: {self._workspace}, project: {self._project}")
        except Exception as e:
            _log.error(f"Failed to initialize Rally connection: {e}")
            raise

        # Get current user from API
        self._current_user = self._fetch_current_user()
        _log.debug(f"Current user: {self._current_user}")

        # Get current iteration from API
        self._current_iteration = self._fetch_current_iteration()
        _log.debug(f"Current iteration: {self._current_iteration}")

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
        except Exception as e:
            _log.warning(f"Failed to fetch current user: {e}")
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
        except Exception as e:
            _log.warning(f"Failed to fetch current iteration: {e}")
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
        _log.debug(f"Fetching tickets with query: {effective_query}")

        # Fetch different artifact types
        for entity_type in ["HierarchicalRequirement", "Defect", "Task"]:
            try:
                response = self._rally.get(
                    entity_type,
                    fetch="FormattedID,Name,ScheduleState,State,Owner,Description,Notes,Iteration,PlanEstimate,ObjectID",
                    query=effective_query,
                    pagesize=200,
                )

                count = 0
                for item in response:
                    tickets.append(self._to_ticket(item, entity_type))
                    count += 1
                _log.debug(f"Fetched {count} {entity_type} items")
            except Exception as e:
                # Skip entity types that fail (e.g., no permission)
                _log.warning(f"Failed to fetch {entity_type}: {e}")
                continue

        _log.info(f"Fetched {len(tickets)} total tickets")
        return tickets

    def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by formatted ID.

        Args:
            formatted_id: The ticket's formatted ID (e.g., "US1234").

        Returns:
            The ticket if found, None otherwise.
        """
        _log.debug(f"Fetching ticket: {formatted_id}")
        entity_type = self._get_entity_type(formatted_id)

        try:
            response = self._rally.get(
                entity_type,
                fetch="FormattedID,Name,ScheduleState,State,Owner,Description,Notes,Iteration,PlanEstimate,ObjectID",
                query=f'FormattedID = "{formatted_id}"',
            )

            item = response.next()
            _log.debug(f"Found ticket: {formatted_id}")
            return self._to_ticket(item, entity_type)
        except StopIteration:
            _log.warning(f"Ticket not found: {formatted_id}")
            return None
        except Exception as e:
            _log.error(f"Error fetching ticket {formatted_id}: {e}")
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

        # Extract points (PlanEstimate) - preserve decimals
        points = None
        if hasattr(item, "PlanEstimate") and item.PlanEstimate is not None:
            try:
                raw_points = float(item.PlanEstimate)
                # Convert to int if whole number for cleaner display
                points = int(raw_points) if raw_points == int(raw_points) else raw_points
            except (ValueError, TypeError):
                points = None

        # Get state - use ScheduleState for stories/tasks, State for defects
        state = getattr(item, "ScheduleState", None) or getattr(
            item, "State", "Unknown"
        )

        # Get description, handle None
        description = getattr(item, "Description", "") or ""

        # Get notes, handle None
        notes = getattr(item, "Notes", "") or ""

        # Get ObjectID for discussion queries
        object_id = None
        if hasattr(item, "ObjectID") and item.ObjectID:
            object_id = str(item.ObjectID)

        return Ticket(
            formatted_id=item.FormattedID,
            name=item.Name,
            ticket_type=ticket_type,  # type: ignore[arg-type]
            state=state,
            owner=owner,
            description=description,
            notes=notes,
            iteration=iteration,
            points=points,
            object_id=object_id,
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

    def get_discussions(self, ticket: Ticket) -> list[Discussion]:
        """Fetch discussion posts for a ticket.

        Uses Rally's ConversationPost entity to get comments linked to the artifact.

        Args:
            ticket: The ticket to fetch discussions for.

        Returns:
            List of discussions, ordered by creation date (oldest first).
        """
        if not ticket.object_id:
            _log.debug(f"No object_id for ticket {ticket.formatted_id}, skipping discussions")
            return []

        _log.debug(f"Fetching discussions for {ticket.formatted_id}")
        discussions: list[Discussion] = []

        try:
            # Query ConversationPost linked to this artifact
            response = self._rally.get(
                "ConversationPost",
                fetch="ObjectID,Text,User,CreationDate,Artifact",
                query=f'(Artifact.ObjectID = "{ticket.object_id}")',
                order="CreationDate",
                pagesize=200,
            )

            for post in response:
                discussions.append(self._to_discussion(post, ticket.formatted_id))
            _log.debug(f"Fetched {len(discussions)} discussions for {ticket.formatted_id}")
        except Exception as e:
            _log.error(f"Error fetching discussions for {ticket.formatted_id}: {e}")

        return discussions

    def _to_discussion(self, post: Any, artifact_id: str) -> Discussion:
        """Convert a Rally ConversationPost to our Discussion model.

        Args:
            post: The pyral ConversationPost object.
            artifact_id: The formatted ID of the parent ticket.

        Returns:
            A Discussion instance.
        """
        # Extract user name
        user = "Unknown"
        if hasattr(post, "User") and post.User:
            user = (
                getattr(post.User, "DisplayName", None)
                or getattr(post.User, "_refObjectName", None)
                or "Unknown"
            )

        # Parse creation date
        created_at = datetime.now()
        if hasattr(post, "CreationDate") and post.CreationDate:
            try:
                # Rally returns ISO format: 2024-01-15T10:30:00.000Z
                date_str = post.CreationDate
                if isinstance(date_str, str):
                    created_at = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00")
                    )
            except (ValueError, TypeError):
                pass

        return Discussion(
            object_id=str(post.ObjectID),
            text=getattr(post, "Text", "") or "",
            user=user,
            created_at=created_at,
            artifact_id=artifact_id,
        )

    def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
        """Add a comment to a ticket's discussion.

        Creates a ConversationPost linked to the artifact.

        Args:
            ticket: The ticket to comment on.
            text: The comment text.

        Returns:
            The created Discussion, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot add comment: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Adding comment to {ticket.formatted_id}")

        try:
            # Get entity type for the ref
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Create the conversation post
            post_data = {
                "Text": text,
                "Artifact": f"/{entity_type.lower()}/{ticket.object_id}",
            }

            created = self._rally.create("ConversationPost", post_data)

            if created:
                _log.info(f"Comment added successfully to {ticket.formatted_id}")
                return self._to_discussion(created, ticket.formatted_id)
        except Exception as e:
            _log.error(f"Error adding comment to {ticket.formatted_id}: {e}")

        return None

    def update_points(self, ticket: Ticket, points: float) -> Ticket | None:
        """Update a ticket's story points.

        Updates PlanEstimate on User Stories and Defects.

        Args:
            ticket: The ticket to update.
            points: The new story points value (supports decimals like 0.5).

        Returns:
            The updated Ticket with new points, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot update points: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Updating points for {ticket.formatted_id} to {points}")

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Update the PlanEstimate field
            update_data = {
                "ObjectID": ticket.object_id,
                "PlanEstimate": points,
            }

            self._rally.update(entity_type, update_data)
            _log.info(f"Points updated successfully for {ticket.formatted_id}")

            # Return updated ticket (convert to int if whole number)
            stored_points = int(points) if points == int(points) else points
            return Ticket(
                formatted_id=ticket.formatted_id,
                name=ticket.name,
                ticket_type=ticket.ticket_type,
                state=ticket.state,
                owner=ticket.owner,
                description=ticket.description,
                notes=ticket.notes,
                iteration=ticket.iteration,
                points=stored_points,
                object_id=ticket.object_id,
            )
        except Exception as e:
            _log.error(f"Error updating points for {ticket.formatted_id}: {e}")

        return None

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
        _log.info(f"Creating {ticket_type}: {title}")

        try:
            # Build the ticket data
            ticket_data: dict[str, str | None] = {
                "Name": title,
                "Description": description,
            }

            # Add current iteration if available
            if self._current_iteration:
                # Query for the iteration ref
                response = self._rally.get(
                    "Iteration",
                    fetch="Name,ObjectID",
                    query=f'(Name = "{self._current_iteration}")',
                    pagesize=1,
                )
                for iteration in response:
                    ticket_data["Iteration"] = f"/iteration/{iteration.ObjectID}"
                    break

            # Add current user as owner if available
            if self._current_user:
                # Query for the user ref
                response = self._rally.get(
                    "User",
                    fetch="DisplayName,ObjectID",
                    query=f'(DisplayName = "{self._current_user}")',
                    pagesize=1,
                )
                for user in response:
                    ticket_data["Owner"] = f"/user/{user.ObjectID}"
                    break

            # Create the ticket
            created = self._rally.create(ticket_type, ticket_data)

            if created:
                _log.info(f"Created ticket: {created.FormattedID}")
                return self._to_ticket(created, ticket_type)

        except Exception as e:
            _log.error(f"Error creating ticket: {e}")

        return None

    def update_state(self, ticket: Ticket, state: str) -> Ticket | None:
        """Update a ticket's workflow state.

        Updates ScheduleState for User Stories/Tasks or State for Defects.

        Args:
            ticket: The ticket to update.
            state: The new state value (e.g., "In Progress", "Completed").

        Returns:
            The updated Ticket with new state, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot update state: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Updating state for {ticket.formatted_id} to {state}")

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Defects use "State", others use "ScheduleState"
            state_field = "State" if entity_type == "Defect" else "ScheduleState"

            update_data = {
                "ObjectID": ticket.object_id,
                state_field: state,
            }

            self._rally.update(entity_type, update_data)
            _log.info(f"State updated successfully for {ticket.formatted_id}")

            return Ticket(
                formatted_id=ticket.formatted_id,
                name=ticket.name,
                ticket_type=ticket.ticket_type,
                state=state,
                owner=ticket.owner,
                description=ticket.description,
                notes=ticket.notes,
                iteration=ticket.iteration,
                points=ticket.points,
                object_id=ticket.object_id,
            )
        except Exception as e:
            _log.error(f"Error updating state for {ticket.formatted_id}: {e}")

        return None

    def get_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch recent iterations from Rally.

        Queries the Iteration entity and returns iterations that have already
        started (past + current), sorted by start date descending.

        Args:
            count: Maximum number of iterations to return.

        Returns:
            List of Iteration objects, sorted by start date descending.
        """
        from datetime import datetime, timezone

        _log.debug(f"Fetching {count} recent iterations")
        iterations: list[Iteration] = []

        try:
            # Only return iterations that have already started (past + current)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            response = self._rally.get(
                "Iteration",
                fetch="ObjectID,Name,StartDate,EndDate,State",
                query=f'(StartDate <= "{today}")',
                order="StartDate desc",
                pagesize=count * 2,  # Fetch extra to account for filtering
            )

            fetched = 0
            for item in response:
                if fetched >= count:
                    break

                iteration = self._to_iteration(item)
                if iteration:
                    iterations.append(iteration)
                    fetched += 1

            _log.debug(f"Fetched {len(iterations)} iterations")
        except Exception as e:
            _log.error(f"Error fetching iterations: {e}")

        return iterations

    def _to_iteration(self, item: Any) -> Iteration | None:
        """Convert a pyral Iteration entity to our Iteration model.

        Args:
            item: The pyral Iteration object.

        Returns:
            An Iteration instance, or None if conversion fails.
        """
        try:
            # Parse dates from Rally format
            start_date = self._parse_rally_date(getattr(item, "StartDate", None))
            end_date = self._parse_rally_date(getattr(item, "EndDate", None))

            if not start_date or not end_date:
                _log.warning(f"Missing dates for iteration: {item.Name}")
                return None

            return Iteration(
                object_id=str(item.ObjectID),
                name=item.Name,
                start_date=start_date,
                end_date=end_date,
                state=getattr(item, "State", "Planning") or "Planning",
            )
        except Exception as e:
            _log.warning(f"Failed to convert iteration: {e}")
            return None

    def _parse_rally_date(self, date_str: str | None) -> date | None:
        """Parse a Rally date string to a date object.

        Args:
            date_str: Rally date string (e.g., "2024-01-15T00:00:00.000Z").

        Returns:
            A date object, or None if parsing fails.
        """
        if not date_str:
            return None

        try:
            # Rally returns ISO format: 2024-01-15T00:00:00.000Z
            if isinstance(date_str, str):
                # Strip time portion and parse date
                date_part = date_str.split("T")[0]
                return date.fromisoformat(date_part)
        except (ValueError, TypeError) as e:
            _log.warning(f"Failed to parse date '{date_str}': {e}")

        return None
