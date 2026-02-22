"""Rally API client implementation."""

from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

from pyral import Rally

from rally_tui.config import RallyConfig
from rally_tui.models import Attachment, Discussion, Iteration, Owner, Release, Tag, Ticket
from rally_tui.services.protocol import BulkResult
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
        from datetime import datetime

        try:
            today = datetime.now(UTC).strftime("%Y-%m-%d")
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
        """Build the default query for current user, iteration, and project.

        Returns:
            A Rally query string filtering by project, current user, and iteration,
            or None if no conditions are available.
        """
        conditions = []

        # Always scope to current project to prevent cross-project leakage
        if self._project:
            conditions.append(f'(Project.Name = "{self._project}")')

        # Exclude Jira Migration items
        conditions.append('(Owner.DisplayName != "Jira Migration")')

        if self._current_iteration:
            conditions.append(f'(Iteration.Name = "{self._current_iteration}")')

        if self._current_user:
            conditions.append(f'(Owner.DisplayName = "{self._current_user}")')

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        # Rally WSAPI requires nested ANDs: ((cond1) AND (cond2))
        result = conditions[0]
        for condition in conditions[1:]:
            result = f"({result} AND {condition})"
        return result

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
                    fetch="FormattedID,Name,FlowState,Owner,Description,Notes,Iteration,PlanEstimate,ObjectID,PortfolioItem",
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
                fetch="FormattedID,Name,FlowState,Owner,Description,Notes,Iteration,PlanEstimate,ObjectID,PortfolioItem",
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
            owner = getattr(item.Owner, "Name", None) or getattr(item.Owner, "_refObjectName", None)

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

        # Get state - FlowState can be a string, dict, or pyral reference object
        state: str = "Unknown"
        flow_state = getattr(item, "FlowState", None)
        if flow_state:
            if isinstance(flow_state, str):
                state = flow_state
            elif isinstance(flow_state, dict):
                state = flow_state.get("_refObjectName") or flow_state.get("Name") or "Unknown"
            elif hasattr(flow_state, "_refObjectName"):
                # pyral reference object with _refObjectName
                ref_name = flow_state._refObjectName
                state = str(ref_name) if ref_name else "Unknown"
            elif hasattr(flow_state, "Name"):
                # pyral reference object with Name
                state = str(flow_state.Name) if flow_state.Name else "Unknown"
            else:
                state = str(flow_state)

        # Get description, handle None
        description = getattr(item, "Description", "") or ""

        # Get notes, handle None
        notes = getattr(item, "Notes", "") or ""

        # Get ObjectID for discussion queries
        object_id = None
        if hasattr(item, "ObjectID") and item.ObjectID:
            object_id = str(item.ObjectID)

        # Extract parent ID from PortfolioItem (for User Stories)
        parent_id = None
        if hasattr(item, "PortfolioItem") and item.PortfolioItem:
            parent_id = getattr(item.PortfolioItem, "FormattedID", None)

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
            parent_id=parent_id,
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
                    created_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
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
                parent_id=ticket.parent_id,
            )
        except Exception as e:
            _log.error(f"Error updating points for {ticket.formatted_id}: {e}")

        return None

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
        _log.info(f"Creating {ticket_type}: {title}")

        try:
            # Build the ticket data
            ticket_data: dict[str, str | None | float] = {
                "Name": title,
                "Description": description,
            }
            if points is not None:
                ticket_data["PlanEstimate"] = points

            # Add current iteration if available (unless backlog)
            if not backlog and self._current_iteration:
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

        Updates FlowState for all entity types. Looks up the FlowState reference
        by name since Rally requires a reference object, not a string.

        Args:
            ticket: The ticket to update.
            state: The new state value (e.g., "In-Progress", "Completed").

        Returns:
            The updated Ticket with new state, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot update state: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Updating state for {ticket.formatted_id} to {state}")

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Look up the FlowState reference by name
            flow_state_ref: str | None = None
            response = self._rally.get(
                "FlowState",
                fetch="Name,ObjectID",
                query=f'(Name = "{state}")',
                pagesize=1,
            )
            for flow_state in response:
                flow_state_ref = f"/flowstate/{flow_state.ObjectID}"
                _log.debug(f"Found FlowState ref: {flow_state_ref} for state: {state}")
                break

            if not flow_state_ref:
                _log.error(f"FlowState not found: {state}")
                return None

            update_data = {
                "ObjectID": ticket.object_id,
                "FlowState": flow_state_ref,
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
                parent_id=ticket.parent_id,
            )
        except Exception as e:
            _log.error(f"Error updating state for {ticket.formatted_id}: {e}")

        return None

    def update_ticket(self, ticket: Ticket, fields: dict[str, Any]) -> Ticket | None:
        """Update arbitrary fields on a ticket.

        Note: The sync RallyClient delegates to update_state for state
        changes. Full multi-field update is handled by AsyncRallyClient.
        """
        if "state" in fields and len(fields) == 1:
            return self.update_state(ticket, fields["state"])
        _log.warning(
            "update_ticket with multiple fields not supported in sync client; use async client"
        )
        return None

    def delete_ticket(self, formatted_id: str) -> bool:
        """Delete a ticket from Rally."""
        if not formatted_id:
            return False
        try:
            entity_type = self._get_entity_type(formatted_id)
            ticket = self.get_ticket(formatted_id)
            if not ticket or not ticket.object_id:
                _log.error(f"Cannot delete: ticket {formatted_id} not found")
                return False
            self._rally.delete(entity_type, ticket.object_id)
            _log.info(f"Deleted {formatted_id}")
            return True
        except Exception as e:
            _log.error(f"Error deleting {formatted_id}: {e}")
            return False

    def get_iterations(self, count: int = 5, state: str | None = None) -> list[Iteration]:
        """Fetch recent iterations from Rally.

        Returns the current iteration first (button 1), followed by recent
        past iterations sorted by start date descending.

        Args:
            count: Maximum number of iterations to return.
            state: Optional state filter (Planning, Committed, Accepted).

        Returns:
            List of Iteration objects with current sprint first.
        """
        from datetime import datetime

        _log.debug(f"Fetching {count} recent iterations (state={state})")
        iterations: list[Iteration] = []
        current_iteration: Iteration | None = None

        try:
            today = datetime.now(UTC).strftime("%Y-%m-%d")

            # First, find the current iteration (today between start and end)
            current_response = self._rally.get(
                "Iteration",
                fetch="ObjectID,Name,StartDate,EndDate,State",
                query=f'((StartDate <= "{today}") AND (EndDate >= "{today}"))',
                pagesize=1,
            )
            for item in current_response:
                current_iteration = self._to_iteration(item)
                if current_iteration:
                    if state is None or current_iteration.state == state:
                        iterations.append(current_iteration)
                    _log.debug(f"Current iteration: {current_iteration.name}")
                break

            # Then get recent past iterations (started but already ended)
            past_response = self._rally.get(
                "Iteration",
                fetch="ObjectID,Name,StartDate,EndDate,State",
                query=f'(EndDate < "{today}")',
                order="StartDate desc",
                pagesize=count,
            )

            for item in past_response:
                if len(iterations) >= count:
                    break
                iteration = self._to_iteration(item)
                if iteration:
                    if state is None or iteration.state == state:
                        iterations.append(iteration)

            _log.debug(f"Fetched {len(iterations)} iterations")
        except Exception as e:
            _log.error(f"Error fetching iterations: {e}")

        return iterations

    def get_future_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch future iterations starting after today.

        Args:
            count: Maximum number of iterations to return.

        Returns:
            List of Iteration objects sorted by start date ascending.
        """
        from datetime import datetime

        _log.debug(f"Fetching {count} future iterations")
        iterations: list[Iteration] = []

        try:
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            response = self._rally.get(
                "Iteration",
                fetch="ObjectID,Name,StartDate,EndDate,State",
                query=f'(StartDate > "{today}")',
                order="StartDate asc",
                pagesize=count,
            )
            for item in response:
                if len(iterations) >= count:
                    break
                iteration = self._to_iteration(item)
                if iteration:
                    iterations.append(iteration)
            _log.debug(f"Fetched {len(iterations)} future iterations")
        except Exception as e:
            _log.error(f"Error fetching future iterations: {e}")

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

    def get_feature(self, formatted_id: str) -> tuple[str, str] | None:
        """Fetch a Feature's name by its formatted ID.

        Args:
            formatted_id: The Feature's formatted ID (e.g., "F59625").

        Returns:
            Tuple of (formatted_id, name) if found, None otherwise.
        """
        _log.debug(f"Fetching feature: {formatted_id}")

        try:
            # Search workspace-wide since Features may be at a higher level
            response = self._rally.get(
                "PortfolioItem/Feature",
                fetch="FormattedID,Name",
                query=f'FormattedID = "{formatted_id}"',
                projectScopeUp=True,
                projectScopeDown=True,
            )

            item = response.next()
            _log.debug(f"Found feature: {formatted_id} - {item.Name}")
            return (item.FormattedID, item.Name)
        except StopIteration:
            _log.warning(f"Feature not found: {formatted_id}")
            return None
        except Exception as e:
            _log.error(f"Error fetching feature {formatted_id}: {e}")
            return None

    def set_parent(self, ticket: Ticket, parent_id: str) -> Ticket | None:
        """Set a ticket's parent Feature.

        Args:
            ticket: The ticket to update.
            parent_id: The parent Feature's formatted ID (e.g., "F59625").

        Returns:
            The updated Ticket with parent_id set, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot set parent: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Setting parent of {ticket.formatted_id} to {parent_id}")

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Get the Feature's ObjectID for the ref (search workspace-wide)
            feature_response = self._rally.get(
                "PortfolioItem/Feature",
                fetch="ObjectID",
                query=f'FormattedID = "{parent_id}"',
                projectScopeUp=True,
                projectScopeDown=True,
            )
            feature = feature_response.next()
            feature_object_id = feature.ObjectID

            # Update the ticket's PortfolioItem
            update_data = {
                "ObjectID": ticket.object_id,
                "PortfolioItem": f"/portfolioitem/feature/{feature_object_id}",
            }

            self._rally.update(entity_type, update_data)
            _log.info(f"Parent set successfully for {ticket.formatted_id}")

            return Ticket(
                formatted_id=ticket.formatted_id,
                name=ticket.name,
                ticket_type=ticket.ticket_type,
                state=ticket.state,
                owner=ticket.owner,
                description=ticket.description,
                notes=ticket.notes,
                iteration=ticket.iteration,
                points=ticket.points,
                object_id=ticket.object_id,
                parent_id=parent_id,
            )
        except StopIteration:
            _log.error(f"Feature not found: {parent_id}")
            return None
        except Exception as e:
            _log.error(f"Error setting parent for {ticket.formatted_id}: {e}")
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
        _log.info(f"Bulk setting parent {parent_id} on {len(tickets)} tickets")
        result = BulkResult()

        for ticket in tickets:
            # Skip tickets that already have a parent
            if ticket.parent_id:
                _log.debug(f"Skipping {ticket.formatted_id}: already has parent")
                continue

            try:
                updated = self.set_parent(ticket, parent_id)
                if updated:
                    result.success_count += 1
                    result.updated_tickets.append(updated)
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Failed to set parent")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")
                _log.error(f"Error setting parent for {ticket.formatted_id}: {e}")

        _log.info(
            f"Bulk parent complete: {result.success_count} success, {result.failed_count} failed"
        )
        return result

    def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult:
        """Update state on multiple tickets.

        Args:
            tickets: List of tickets to update.
            state: The new state value.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        _log.info(f"Bulk updating state to {state} on {len(tickets)} tickets")
        result = BulkResult()

        for ticket in tickets:
            try:
                updated = self.update_state(ticket, state)
                if updated:
                    result.success_count += 1
                    result.updated_tickets.append(updated)
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Failed to update state")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")
                _log.error(f"Error updating state for {ticket.formatted_id}: {e}")

        _log.info(
            f"Bulk state update complete: {result.success_count} success, "
            f"{result.failed_count} failed"
        )
        return result

    def bulk_set_iteration(self, tickets: list[Ticket], iteration_name: str | None) -> BulkResult:
        """Set iteration on multiple tickets.

        Args:
            tickets: List of tickets to update.
            iteration_name: The iteration name, or None for backlog.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        _log.info(f"Bulk setting iteration to {iteration_name} on {len(tickets)} tickets")
        result = BulkResult()

        # Get the iteration ref if not None (backlog)
        iteration_ref: str | None = None
        if iteration_name:
            try:
                response = self._rally.get(
                    "Iteration",
                    fetch="Name,ObjectID",
                    query=f'(Name = "{iteration_name}")',
                    pagesize=1,
                )
                for iteration in response:
                    iteration_ref = f"/iteration/{iteration.ObjectID}"
                    break

                if not iteration_ref:
                    _log.error(f"Iteration not found: {iteration_name}")
                    result.failed_count = len(tickets)
                    result.errors.append(f"Iteration not found: {iteration_name}")
                    return result
            except Exception as e:
                _log.error(f"Error fetching iteration: {e}")
                result.failed_count = len(tickets)
                result.errors.append(f"Error fetching iteration: {str(e)}")
                return result

        for ticket in tickets:
            try:
                if not ticket.object_id:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: No object_id")
                    continue

                entity_type = self._get_entity_type(ticket.formatted_id)
                update_data: dict[str, str | None] = {
                    "ObjectID": ticket.object_id,
                    "Iteration": iteration_ref,  # None removes iteration (backlog)
                }

                self._rally.update(entity_type, update_data)

                updated = Ticket(
                    formatted_id=ticket.formatted_id,
                    name=ticket.name,
                    ticket_type=ticket.ticket_type,
                    state=ticket.state,
                    owner=ticket.owner,
                    description=ticket.description,
                    notes=ticket.notes,
                    iteration=iteration_name,
                    points=ticket.points,
                    object_id=ticket.object_id,
                    parent_id=ticket.parent_id,
                )
                result.success_count += 1
                result.updated_tickets.append(updated)
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")
                _log.error(f"Error setting iteration for {ticket.formatted_id}: {e}")

        _log.info(
            f"Bulk iteration complete: {result.success_count} success, {result.failed_count} failed"
        )
        return result

    def bulk_update_points(self, tickets: list[Ticket], points: float) -> BulkResult:
        """Update story points on multiple tickets.

        Args:
            tickets: List of tickets to update.
            points: The new story points value.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        _log.info(f"Bulk updating points to {points} on {len(tickets)} tickets")
        result = BulkResult()

        for ticket in tickets:
            try:
                updated = self.update_points(ticket, points)
                if updated:
                    result.success_count += 1
                    result.updated_tickets.append(updated)
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Failed to update points")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")
                _log.error(f"Error updating points for {ticket.formatted_id}: {e}")

        _log.info(
            f"Bulk points update complete: {result.success_count} success, "
            f"{result.failed_count} failed"
        )
        return result

    def get_attachments(self, ticket: Ticket) -> list[Attachment]:
        """Get all attachments for a ticket.

        Uses Rally's getAttachments method to fetch attachment metadata.

        Args:
            ticket: The ticket to get attachments for.

        Returns:
            List of Attachment objects for the ticket.
        """
        if not ticket.object_id:
            _log.debug(f"No object_id for ticket {ticket.formatted_id}, skipping attachments")
            return []

        _log.debug(f"Fetching attachments for {ticket.formatted_id}")
        attachments: list[Attachment] = []

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Get the artifact entity to pass to getAttachments
            response = self._rally.get(
                entity_type,
                fetch="ObjectID,Name",
                query=f'ObjectID = "{ticket.object_id}"',
            )
            artifact = next(response)

            # Get all attachments for this artifact
            rally_attachments = self._rally.getAttachments(artifact)

            for att in rally_attachments:
                attachments.append(
                    Attachment(
                        name=att.Name,
                        size=int(att.Size) if hasattr(att, "Size") else 0,
                        content_type=getattr(att, "ContentType", "application/octet-stream"),
                        object_id=str(att.ObjectID),
                    )
                )

            _log.debug(f"Fetched {len(attachments)} attachments for {ticket.formatted_id}")
        except StopIteration:
            _log.warning(f"Ticket not found: {ticket.formatted_id}")
        except Exception as e:
            _log.error(f"Error fetching attachments for {ticket.formatted_id}: {e}")

        return attachments

    def download_attachment(self, ticket: Ticket, attachment: Attachment, dest_path: str) -> bool:
        """Download attachment content to a local file.

        Uses Rally's getAttachment method to fetch content and writes to file.

        Args:
            ticket: The ticket the attachment belongs to.
            attachment: The attachment to download.
            dest_path: The local path to save the file to.

        Returns:
            True on success, False on failure.
        """
        import base64

        if not ticket.object_id:
            _log.warning(f"Cannot download attachment: no object_id for {ticket.formatted_id}")
            return False

        _log.info(f"Downloading attachment {attachment.name} from {ticket.formatted_id}")

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Get the artifact entity
            response = self._rally.get(
                entity_type,
                fetch="ObjectID,Name",
                query=f'ObjectID = "{ticket.object_id}"',
            )
            artifact = next(response)

            # Get the attachment with content
            att = self._rally.getAttachment(artifact, attachment.name)

            if att and hasattr(att, "Content"):
                # Content is base64 encoded
                content = base64.b64decode(att.Content)
                with open(dest_path, "wb") as f:
                    f.write(content)
                _log.info(f"Downloaded {attachment.name} to {dest_path}")
                return True
            else:
                _log.error(f"Attachment content not found: {attachment.name}")
                return False
        except StopIteration:
            _log.warning(f"Ticket not found: {ticket.formatted_id}")
            return False
        except Exception as e:
            _log.error(f"Error downloading attachment {attachment.name}: {e}")
            return False

    def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None:
        """Upload a local file as an attachment to a ticket.

        Uses Rally's addAttachment method to upload the file.

        Args:
            ticket: The ticket to attach the file to.
            file_path: The local path of the file to upload.

        Returns:
            The created Attachment on success, None on failure.
        """
        import mimetypes
        import os

        if not ticket.object_id:
            _log.warning(f"Cannot upload attachment: no object_id for {ticket.formatted_id}")
            return None

        if not os.path.exists(file_path):
            _log.error(f"File not found: {file_path}")
            return None

        # Check file size (Rally limit is 50MB)
        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024  # 50 MB
        if file_size > max_size:
            _log.error(f"File too large: {file_size} bytes (max {max_size})")
            return None

        _log.info(f"Uploading {file_path} to {ticket.formatted_id}")

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Get the artifact entity
            response = self._rally.get(
                entity_type,
                fetch="ObjectID,Name",
                query=f'ObjectID = "{ticket.object_id}"',
            )
            artifact = next(response)

            # Determine MIME type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"

            # Upload the attachment
            result = self._rally.addAttachment(artifact, file_path, mime_type=content_type)

            if result:
                filename = os.path.basename(file_path)
                _log.info(f"Uploaded {filename} to {ticket.formatted_id}")
                return Attachment(
                    name=filename,
                    size=file_size,
                    content_type=content_type,
                    object_id=str(getattr(result, "ObjectID", "unknown")),
                )
        except StopIteration:
            _log.warning(f"Ticket not found: {ticket.formatted_id}")
        except Exception as e:
            _log.error(f"Error uploading attachment to {ticket.formatted_id}: {e}")

        return None

    def download_embedded_image(self, url: str, dest_path: str) -> bool:
        """Download an embedded image from a URL.

        Embedded images in Rally are stored on Rally's servers and require
        authentication to download.

        Args:
            url: The URL of the embedded image (may be relative or absolute).
            dest_path: The local path to save the file to.

        Returns:
            True on success, False on failure.
        """
        import requests

        # Make URL absolute if it's relative
        if url.startswith("/"):
            url = f"https://{self._config.server}{url}"

        _log.info(f"Downloading embedded image from {url}")

        try:
            # Rally embedded images require API key authentication
            headers = {
                "ZSESSIONID": self._config.apikey,
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            with open(dest_path, "wb") as f:
                f.write(response.content)

            _log.info(f"Downloaded embedded image to {dest_path}")
            return True
        except requests.RequestException as e:
            _log.error(f"Error downloading embedded image: {e}")
            return False
        except Exception as e:
            _log.error(f"Error saving embedded image: {e}")
            return False

    def get_users(self, display_names: list[str] | None = None) -> list[Owner]:
        """Fetch Rally users by display names.

        Args:
            display_names: Optional list of user display names to filter by.

        Returns:
            List of Owner objects matching the display names.
        """
        params = {
            "fetch": "ObjectID,DisplayName,UserName,EmailAddress",
            "pagesize": 200,
        }

        if display_names:
            # Build OR query for display names (with sanitization to prevent injection)
            conditions = [
                f'(DisplayName = "{self._sanitize_query_value(name)}")' for name in display_names
            ]
            if len(conditions) == 1:
                params["query"] = conditions[0]
            else:
                query = conditions[0]
                for cond in conditions[1:]:
                    query = f"({query} OR {cond})"
                params["query"] = query

        try:
            response = self._rally.get("User", **params)
            users: list[Owner] = []
            for item in response:
                users.append(self._to_owner(item))
            return users
        except Exception as e:
            _log.error(f"Error fetching users: {e}")
            return []

    def _sanitize_query_value(self, value: str) -> str:
        """Escape special characters for Rally WSAPI queries.

        Args:
            value: The value to sanitize.

        Returns:
            Sanitized value safe for use in queries.
        """
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _to_owner(self, item: Any) -> Owner:
        """Convert Rally User response to Owner model.

        Args:
            item: The pyral User object.

        Returns:
            An Owner instance.
        """
        return Owner(
            object_id=str(item.ObjectID),
            display_name=item.DisplayName,
            user_name=getattr(item, "UserName", None),
        )

    def assign_owner(self, ticket: Ticket, owner: Owner) -> Ticket | None:
        """Assign a ticket to a new owner.

        Args:
            ticket: The ticket to update.
            owner: The owner to assign (Owner object with object_id).

        Returns:
            The updated Ticket with new owner, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot assign owner: no object_id for {ticket.formatted_id}")
            return None

        if not owner.object_id or not owner.object_id.strip():
            _log.warning(f"Cannot assign owner: invalid object_id for {owner.display_name}")
            return None

        _log.info(f"Assigning {ticket.formatted_id} to {owner.display_name}")

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            # Update the Owner field with user reference
            update_data = {
                "ObjectID": ticket.object_id,
                "Owner": f"/user/{owner.object_id}",
            }

            self._rally.update(entity_type, update_data)
            _log.info(f"Owner assigned successfully for {ticket.formatted_id}")

            # Return updated ticket
            return replace(ticket, owner=owner.display_name)
        except Exception as e:
            _log.error(f"Error assigning owner for {ticket.formatted_id}: {e}")

        return None

    def bulk_assign_owner(self, tickets: list[Ticket], owner: Owner) -> BulkResult:
        """Assign owner to multiple tickets.

        Args:
            tickets: List of tickets to update.
            owner: The owner to assign to all tickets.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        _log.info(f"Bulk assigning owner {owner.display_name} to {len(tickets)} tickets")
        result = BulkResult()

        for ticket in tickets:
            try:
                updated = self.assign_owner(ticket, owner)
                if updated:
                    result.success_count += 1
                    result.updated_tickets.append(updated)
                else:
                    result.failed_count += 1
                    result.errors.append(f"{ticket.formatted_id}: Failed to assign owner")
            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{ticket.formatted_id}: {str(e)}")
                _log.error(f"Error assigning owner for {ticket.formatted_id}: {e}")

        _log.info(
            f"Bulk owner assignment complete: {result.success_count} success, "
            f"{result.failed_count} failed"
        )
        return result

    # -------------------------------------------------------------------------
    # Release Operations
    # -------------------------------------------------------------------------

    def get_releases(self, count: int = 10, state: str | None = None) -> list[Release]:
        """Fetch releases from Rally.

        Args:
            count: Maximum number of releases to return.
            state: Optional state filter (Planning, Active, Locked).

        Returns:
            List of Release objects sorted by start date descending.
        """
        _log.debug(f"Fetching {count} releases (state={state})")
        releases: list[Release] = []

        try:
            kwargs: dict[str, Any] = {
                "fetch": "ObjectID,Name,ReleaseStartDate,ReleaseDate,State,Theme,Notes",
                "order": "ReleaseStartDate desc",
                "pagesize": count,
            }
            if state:
                kwargs["query"] = f'(State = "{self._sanitize_query_value(state)}")'

            response = self._rally.get("Release", **kwargs)
            for item in response:
                if len(releases) >= count:
                    break
                release = self._to_release(item)
                if release:
                    releases.append(release)

            _log.debug(f"Fetched {len(releases)} releases")
        except Exception as e:
            _log.error(f"Error fetching releases: {e}")

        return releases

    def get_release(self, name: str) -> Release | None:
        """Fetch a single release by name.

        Args:
            name: The release name to search for.

        Returns:
            The Release if found, None otherwise.
        """
        _log.debug(f"Fetching release: {name}")

        try:
            sanitized_name = self._sanitize_query_value(name)
            response = self._rally.get(
                "Release",
                fetch="ObjectID,Name,ReleaseStartDate,ReleaseDate,State,Theme,Notes",
                query=f'(Name = "{sanitized_name}")',
                pagesize=1,
            )
            for item in response:
                return self._to_release(item)
        except Exception as e:
            _log.error(f"Error fetching release {name}: {e}")

        return None

    def set_release(self, ticket: Ticket, release_name: str | None) -> Ticket | None:
        """Set or remove release assignment on a ticket.

        Args:
            ticket: The ticket to update.
            release_name: The release name to assign, or None to remove.

        Returns:
            The updated Ticket, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot set release: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Setting release on {ticket.formatted_id} to {release_name}")

        try:
            entity_type = self._get_entity_type(ticket.formatted_id)

            if release_name is None:
                update_data: dict[str, Any] = {
                    "ObjectID": ticket.object_id,
                    "Release": None,
                }
                self._rally.update(entity_type, update_data)
            else:
                release = self.get_release(release_name)
                if not release:
                    _log.error(f"Release not found: {release_name}")
                    return None
                update_data = {
                    "ObjectID": ticket.object_id,
                    "Release": f"/release/{release.object_id}",
                }
                self._rally.update(entity_type, update_data)

            return replace(ticket, release=release_name or "")
        except Exception as e:
            _log.error(f"Error setting release for {ticket.formatted_id}: {e}")

        return None

    def _to_release(self, item: Any) -> Release | None:
        """Convert a pyral Release entity to our Release model."""
        try:
            start_date = self._parse_rally_date(getattr(item, "ReleaseStartDate", None))
            end_date = self._parse_rally_date(getattr(item, "ReleaseDate", None))

            if not start_date or not end_date:
                _log.warning(f"Missing dates for release: {item.Name}")
                return None

            return Release(
                object_id=str(item.ObjectID),
                name=item.Name,
                start_date=start_date,
                end_date=end_date,
                state=getattr(item, "State", "Planning") or "Planning",
                theme=getattr(item, "Theme", "") or "",
                notes=getattr(item, "Notes", "") or "",
            )
        except Exception as e:
            _log.warning(f"Failed to convert release: {e}")
            return None

    # -------------------------------------------------------------------------
    # Tag Operations
    # -------------------------------------------------------------------------

    def get_tags(self) -> list[Tag]:
        """Fetch all tags in the workspace.

        Returns:
            List of Tag objects sorted by name.
        """
        _log.debug("Fetching tags")
        tags: list[Tag] = []

        try:
            response = self._rally.get(
                "Tag",
                fetch="ObjectID,Name",
                order="Name asc",
                pagesize=200,
            )
            for item in response:
                tags.append(
                    Tag(
                        object_id=str(item.ObjectID),
                        name=item.Name,
                    )
                )
            _log.debug(f"Fetched {len(tags)} tags")
        except Exception as e:
            _log.error(f"Error fetching tags: {e}")

        return tags

    def add_tag(self, ticket: Ticket, tag_name: str) -> bool:
        """Add a tag to a ticket.

        Note: The sync RallyClient does not support tag collection
        operations via pyral. Use AsyncRallyClient for tag operations.

        Args:
            ticket: The ticket to tag.
            tag_name: The tag name to add.

        Returns:
            True on success, False on failure.
        """
        _log.warning("add_tag not supported in sync client; use async client")
        return False

    def remove_tag(self, ticket: Ticket, tag_name: str) -> bool:
        """Remove a tag from a ticket.

        Note: The sync RallyClient does not support tag collection
        operations via pyral. Use AsyncRallyClient for tag operations.

        Args:
            ticket: The ticket to untag.
            tag_name: The tag name to remove.

        Returns:
            True on success, False on failure.
        """
        _log.warning("remove_tag not supported in sync client; use async client")
        return False

    def create_tag(self, name: str) -> Tag | None:
        """Create a new tag.

        Args:
            name: The tag name.

        Returns:
            The created Tag, or None on failure.
        """
        _log.info(f"Creating tag: {name}")

        try:
            created = self._rally.create("Tag", {"Name": name})
            if created:
                return Tag(
                    object_id=str(created.ObjectID),
                    name=created.Name,
                )
        except Exception as e:
            _log.error(f"Error creating tag: {e}")

        return None
