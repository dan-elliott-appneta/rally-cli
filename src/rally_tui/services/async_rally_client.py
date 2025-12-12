"""Async Rally API client implementation using httpx.

This module provides an asynchronous Rally client that uses httpx for HTTP
requests, enabling non-blocking API calls in the Textual TUI.
"""

from __future__ import annotations

import asyncio
import base64
from datetime import UTC, date, datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from rally_tui.config import RallyConfig
from rally_tui.models import Attachment, Discussion, Iteration, Ticket
from rally_tui.services.protocol import BulkResult
from rally_tui.services.rally_api import (
    DEFAULT_TIMEOUT,
    MAX_CONCURRENT_REQUESTS,
    MAX_PAGE_SIZE,
    RallyAPIError,
    build_base_url,
    build_fetch_string,
    get_entity_type_from_prefix,
    get_url_path,
    parse_query_result,
)
from rally_tui.utils import get_logger

_log = get_logger("rally_tui.services.async_rally_client")


class AsyncRallyClient:
    """Async Rally API client using httpx.

    This client provides async methods for all Rally API operations,
    enabling non-blocking calls in async applications.

    Usage:
        async with AsyncRallyClient(config) as client:
            tickets = await client.get_tickets()

    Or without context manager:
        client = AsyncRallyClient(config)
        await client.initialize()
        try:
            tickets = await client.get_tickets()
        finally:
            await client.close()
    """

    def __init__(self, config: RallyConfig) -> None:
        """Initialize the async Rally client.

        Args:
            config: Rally configuration with API key and connection details.
        """
        self._config = config
        self._base_url = build_base_url(config.server)
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "ZSESSIONID": config.apikey,
                "Content-Type": "application/json",
            },
            timeout=DEFAULT_TIMEOUT,
        )
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        # Cached values (populated during initialize)
        self._workspace: str = config.workspace or ""
        self._project: str = config.project or ""
        self._current_user: str | None = None
        self._current_iteration: str | None = None
        self._initialized = False

    async def __aenter__(self) -> AsyncRallyClient:
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize client by fetching workspace metadata.

        This must be called before using the client, or use the
        async context manager which calls this automatically.
        """
        if self._initialized:
            return

        _log.debug(f"Initializing async Rally client for server: {self._config.server}")

        try:
            # Fetch workspace and project info if not provided
            if not self._workspace or not self._project:
                await self._fetch_workspace_info()

            # Fetch current user and iteration concurrently
            user_task = self._fetch_current_user()
            iter_task = self._fetch_current_iteration()
            self._current_user, self._current_iteration = await asyncio.gather(user_task, iter_task)

            self._initialized = True
            _log.info(
                f"Connected to Rally workspace: {self._workspace}, "
                f"project: {self._project}, user: {self._current_user}"
            )
        except Exception as e:
            _log.error(f"Failed to initialize Rally connection: {e}")
            raise

    async def close(self) -> None:
        """Close the httpx client and release resources."""
        await self._client.aclose()

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

    # -------------------------------------------------------------------------
    # Internal HTTP Methods
    # -------------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (relative to base URL)
            params: Query parameters
            json_data: JSON body data

        Returns:
            Parsed JSON response

        Raises:
            RallyAPIError: If the API returns an error
            httpx.HTTPError: If the request fails
        """
        async with self._semaphore:
            _log.debug(f"Request: {method} {path}")
            response = await self._client.request(
                method,
                path,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make GET request."""
        return await self._request("GET", path, params=params)

    async def _post(
        self,
        path: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make POST request."""
        return await self._request("POST", path, json_data=data)

    # -------------------------------------------------------------------------
    # Initialization Helpers
    # -------------------------------------------------------------------------

    async def _fetch_workspace_info(self) -> None:
        """Fetch workspace and project info from Rally."""
        # Get workspace
        response = await self._get(
            "/workspace",
            params={"fetch": "Name", "pagesize": 1},
        )
        results, _ = parse_query_result(response)
        if results:
            self._workspace = results[0].get("Name", "")

        # Get project
        response = await self._get(
            "/project",
            params={"fetch": "Name", "pagesize": 1},
        )
        results, _ = parse_query_result(response)
        if results:
            self._project = results[0].get("Name", "")

    async def _fetch_current_user(self) -> str | None:
        """Fetch the current user's display name."""
        try:
            response = await self._get(
                "/user",
                params={"fetch": "DisplayName", "pagesize": 1},
            )
            results, _ = parse_query_result(response)
            if results:
                return results[0].get("DisplayName")
        except Exception as e:
            _log.warning(f"Failed to fetch current user: {e}")
        return None

    async def _fetch_current_iteration(self) -> str | None:
        """Fetch the current iteration name."""
        try:
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            query = f'((StartDate <= "{today}") AND (EndDate >= "{today}"))'
            response = await self._get(
                "/iteration",
                params={
                    "fetch": "Name,StartDate,EndDate",
                    "query": query,
                    "order": "StartDate desc",
                    "pagesize": 1,
                },
            )
            results, _ = parse_query_result(response)
            if results:
                return results[0].get("Name")
        except Exception as e:
            _log.warning(f"Failed to fetch current iteration: {e}")
        return None

    # -------------------------------------------------------------------------
    # Ticket Operations
    # -------------------------------------------------------------------------

    def _build_default_query(self) -> str | None:
        """Build the default query for current user and iteration."""
        conditions = []

        if self._current_iteration:
            conditions.append(f'(Iteration.Name = "{self._current_iteration}")')

        if self._current_user:
            conditions.append(f'(Owner.DisplayName = "{self._current_user}")')

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return f"({conditions[0]} AND {conditions[1]})"

    async def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets from Rally concurrently.

        Fetches User Stories, Defects, and Tasks in parallel for better
        performance compared to sequential fetching.

        Args:
            query: Optional Rally query string. If None, uses default filter.

        Returns:
            List of tickets matching the query.
        """
        effective_query = query if query is not None else self._build_default_query()
        _log.debug(f"Fetching tickets with query: {effective_query}")

        # Fetch all entity types concurrently
        entity_types = ["HierarchicalRequirement", "Defect", "Task"]
        tasks = [
            self._fetch_entity_type(entity_type, effective_query) for entity_type in entity_types
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        tickets: list[Ticket] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                _log.warning(f"Failed to fetch {entity_types[i]}: {result}")
            elif isinstance(result, list):
                tickets.extend(result)

        _log.info(f"Fetched {len(tickets)} total tickets")
        return tickets

    async def _fetch_entity_type(
        self,
        entity_type: str,
        query: str | None,
    ) -> list[Ticket]:
        """Fetch tickets of a specific entity type.

        Args:
            entity_type: Rally entity type name
            query: Optional query string

        Returns:
            List of tickets of this type
        """
        path = f"/{get_url_path(entity_type)}"
        params: dict[str, Any] = {
            "fetch": build_fetch_string(entity_type),
            "pagesize": MAX_PAGE_SIZE,
        }
        if query:
            params["query"] = query

        try:
            response = await self._get(path, params)
            results, total = parse_query_result(response)

            tickets = [self._to_ticket(item, entity_type) for item in results]
            _log.debug(f"Fetched {len(tickets)} {entity_type} items")
            return tickets
        except RallyAPIError as e:
            _log.warning(f"Rally API error fetching {entity_type}: {e}")
            return []
        except Exception as e:
            _log.warning(f"Failed to fetch {entity_type}: {e}")
            return []

    async def get_ticket(self, formatted_id: str) -> Ticket | None:
        """Fetch a single ticket by formatted ID.

        Args:
            formatted_id: The ticket's formatted ID (e.g., "US1234").

        Returns:
            The ticket if found, None otherwise.
        """
        _log.debug(f"Fetching ticket: {formatted_id}")
        entity_type = get_entity_type_from_prefix(formatted_id)
        path = f"/{get_url_path(entity_type)}"

        try:
            response = await self._get(
                path,
                params={
                    "fetch": build_fetch_string(entity_type),
                    "query": f'FormattedID = "{formatted_id}"',
                },
            )
            results, _ = parse_query_result(response)
            if results:
                _log.debug(f"Found ticket: {formatted_id}")
                return self._to_ticket(results[0], entity_type)
        except Exception as e:
            _log.error(f"Error fetching ticket {formatted_id}: {e}")

        return None

    def _to_ticket(self, item: dict[str, Any], entity_type: str) -> Ticket:
        """Convert a Rally API response to our Ticket model.

        Args:
            item: The Rally API response dict
            entity_type: The Rally entity type name

        Returns:
            A Ticket instance
        """
        type_map = {
            "HierarchicalRequirement": "UserStory",
            "Defect": "Defect",
            "Task": "Task",
            "TestCase": "TestCase",
        }
        ticket_type = type_map.get(entity_type, "UserStory")

        # Extract owner name
        owner = None
        owner_obj = item.get("Owner")
        if owner_obj and isinstance(owner_obj, dict):
            owner = owner_obj.get("_refObjectName")

        # Extract iteration name
        iteration = None
        iter_obj = item.get("Iteration")
        if iter_obj and isinstance(iter_obj, dict):
            iteration = iter_obj.get("_refObjectName")

        # Extract points
        points = None
        raw_points = item.get("PlanEstimate") or item.get("Estimate")
        if raw_points is not None:
            try:
                points_float = float(raw_points)
                points = int(points_float) if points_float == int(points_float) else points_float
            except (ValueError, TypeError):
                pass

        # Get state
        state = item.get("ScheduleState") or item.get("State") or "Unknown"

        # Extract parent ID
        parent_id = None
        parent_obj = item.get("PortfolioItem")
        if parent_obj and isinstance(parent_obj, dict):
            parent_id = parent_obj.get("FormattedID")

        return Ticket(
            formatted_id=item.get("FormattedID", ""),
            name=item.get("Name", ""),
            ticket_type=ticket_type,  # type: ignore[arg-type]
            state=state,
            owner=owner,
            description=item.get("Description") or "",
            notes=item.get("Notes") or "",
            iteration=iteration,
            points=points,
            object_id=str(item.get("ObjectID", "")),
            parent_id=parent_id,
        )

    # -------------------------------------------------------------------------
    # Discussion Operations
    # -------------------------------------------------------------------------

    async def get_discussions(self, ticket: Ticket) -> list[Discussion]:
        """Fetch discussion posts for a ticket.

        Args:
            ticket: The ticket to fetch discussions for.

        Returns:
            List of discussions, ordered by creation date.
        """
        if not ticket.object_id:
            _log.debug(f"No object_id for {ticket.formatted_id}, skipping discussions")
            return []

        _log.debug(f"Fetching discussions for {ticket.formatted_id}")

        try:
            response = await self._get(
                "/conversationpost",
                params={
                    "fetch": "ObjectID,Text,User,CreationDate,Artifact",
                    "query": f'(Artifact.ObjectID = "{ticket.object_id}")',
                    "order": "CreationDate",
                    "pagesize": MAX_PAGE_SIZE,
                },
            )
            results, _ = parse_query_result(response)

            discussions = [self._to_discussion(item, ticket.formatted_id) for item in results]
            _log.debug(f"Fetched {len(discussions)} discussions for {ticket.formatted_id}")
            return discussions
        except Exception as e:
            _log.error(f"Error fetching discussions for {ticket.formatted_id}: {e}")
            return []

    def _to_discussion(self, item: dict[str, Any], artifact_id: str) -> Discussion:
        """Convert Rally API response to Discussion model."""
        user = "Unknown"
        user_obj = item.get("User")
        if user_obj and isinstance(user_obj, dict):
            user = user_obj.get("_refObjectName", "Unknown")

        created_at = datetime.now(UTC)
        date_str = item.get("CreationDate")
        if date_str and isinstance(date_str, str):
            try:
                created_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return Discussion(
            object_id=str(item.get("ObjectID", "")),
            text=item.get("Text") or "",
            user=user,
            created_at=created_at,
            artifact_id=artifact_id,
        )

    async def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
        """Add a comment to a ticket's discussion.

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
            entity_type = get_entity_type_from_prefix(ticket.formatted_id)
            response = await self._post(
                "/conversationpost/create",
                data={
                    "ConversationPost": {
                        "Text": text,
                        "Artifact": f"/{get_url_path(entity_type)}/{ticket.object_id}",
                    }
                },
            )
            results, _ = parse_query_result(response)
            if results:
                _log.info(f"Comment added successfully to {ticket.formatted_id}")
                return self._to_discussion(results[0], ticket.formatted_id)
        except Exception as e:
            _log.error(f"Error adding comment to {ticket.formatted_id}: {e}")

        return None

    # -------------------------------------------------------------------------
    # Update Operations
    # -------------------------------------------------------------------------

    async def update_points(self, ticket: Ticket, points: float) -> Ticket | None:
        """Update a ticket's story points.

        Args:
            ticket: The ticket to update.
            points: The new story points value.

        Returns:
            The updated Ticket, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot update points: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Updating points for {ticket.formatted_id} to {points}")

        try:
            entity_type = get_entity_type_from_prefix(ticket.formatted_id)
            path = f"/{get_url_path(entity_type)}/{ticket.object_id}"

            response = await self._post(
                path,
                data={entity_type: {"PlanEstimate": points}},
            )
            results, _ = parse_query_result(response)

            if results:
                _log.info(f"Points updated successfully for {ticket.formatted_id}")
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

    async def update_state(self, ticket: Ticket, state: str) -> Ticket | None:
        """Update a ticket's workflow state.

        Args:
            ticket: The ticket to update.
            state: The new state value.

        Returns:
            The updated Ticket, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot update state: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Updating state for {ticket.formatted_id} to {state}")

        try:
            entity_type = get_entity_type_from_prefix(ticket.formatted_id)
            path = f"/{get_url_path(entity_type)}/{ticket.object_id}"

            # Defects use "State", others use "ScheduleState"
            state_field = "State" if entity_type == "Defect" else "ScheduleState"

            response = await self._post(
                path,
                data={entity_type: {state_field: state}},
            )
            results, _ = parse_query_result(response)

            if results:
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

    async def create_ticket(
        self,
        title: str,
        ticket_type: str,
        description: str = "",
    ) -> Ticket | None:
        """Create a new ticket in Rally.

        Args:
            title: The ticket title/name.
            ticket_type: The entity type ("HierarchicalRequirement" or "Defect").
            description: Optional ticket description.

        Returns:
            The created Ticket, or None on failure.
        """
        _log.info(f"Creating {ticket_type}: {title}")

        try:
            ticket_data: dict[str, Any] = {
                "Name": title,
                "Description": description,
            }

            # Add current iteration if available
            if self._current_iteration:
                iter_response = await self._get(
                    "/iteration",
                    params={
                        "fetch": "Name,ObjectID",
                        "query": f'(Name = "{self._current_iteration}")',
                        "pagesize": 1,
                    },
                )
                iter_results, _ = parse_query_result(iter_response)
                if iter_results:
                    object_id = iter_results[0].get("ObjectID")
                    ticket_data["Iteration"] = f"/iteration/{object_id}"

            # Add current user as owner
            if self._current_user:
                user_response = await self._get(
                    "/user",
                    params={
                        "fetch": "DisplayName,ObjectID",
                        "query": f'(DisplayName = "{self._current_user}")',
                        "pagesize": 1,
                    },
                )
                user_results, _ = parse_query_result(user_response)
                if user_results:
                    object_id = user_results[0].get("ObjectID")
                    ticket_data["Owner"] = f"/user/{object_id}"

            path = f"/{get_url_path(ticket_type)}/create"
            response = await self._post(path, data={ticket_type: ticket_data})
            results, _ = parse_query_result(response)

            if results:
                _log.info(f"Created ticket: {results[0].get('FormattedID')}")
                return self._to_ticket(results[0], ticket_type)

        except Exception as e:
            _log.error(f"Error creating ticket: {e}")

        return None

    # -------------------------------------------------------------------------
    # Iteration Operations
    # -------------------------------------------------------------------------

    async def get_iterations(self, count: int = 5) -> list[Iteration]:
        """Fetch recent iterations from Rally.

        Args:
            count: Maximum number of iterations to return.

        Returns:
            List of Iteration objects with current sprint first.
        """
        _log.debug(f"Fetching {count} recent iterations")
        iterations: list[Iteration] = []

        try:
            today = datetime.now(UTC).strftime("%Y-%m-%d")

            # Fetch current and past iterations concurrently
            current_task = self._get(
                "/iteration",
                params={
                    "fetch": "ObjectID,Name,StartDate,EndDate,State",
                    "query": f'((StartDate <= "{today}") AND (EndDate >= "{today}"))',
                    "pagesize": 1,
                },
            )
            past_task = self._get(
                "/iteration",
                params={
                    "fetch": "ObjectID,Name,StartDate,EndDate,State",
                    "query": f'(EndDate < "{today}")',
                    "order": "StartDate desc",
                    "pagesize": count,
                },
            )

            current_response, past_response = await asyncio.gather(current_task, past_task)

            # Process current iteration
            current_results, _ = parse_query_result(current_response)
            for item in current_results:
                iteration = self._to_iteration(item)
                if iteration:
                    iterations.append(iteration)
                    break

            # Process past iterations
            past_results, _ = parse_query_result(past_response)
            for item in past_results:
                if len(iterations) >= count:
                    break
                iteration = self._to_iteration(item)
                if iteration:
                    iterations.append(iteration)

            _log.debug(f"Fetched {len(iterations)} iterations")
        except Exception as e:
            _log.error(f"Error fetching iterations: {e}")

        return iterations

    def _to_iteration(self, item: dict[str, Any]) -> Iteration | None:
        """Convert Rally API response to Iteration model."""
        try:
            start_date = self._parse_rally_date(item.get("StartDate"))
            end_date = self._parse_rally_date(item.get("EndDate"))

            if not start_date or not end_date:
                _log.warning(f"Missing dates for iteration: {item.get('Name')}")
                return None

            return Iteration(
                object_id=str(item.get("ObjectID", "")),
                name=item.get("Name", ""),
                start_date=start_date,
                end_date=end_date,
                state=item.get("State") or "Planning",
            )
        except Exception as e:
            _log.warning(f"Failed to convert iteration: {e}")
            return None

    def _parse_rally_date(self, date_str: str | None) -> date | None:
        """Parse a Rally date string to a date object."""
        if not date_str:
            return None

        try:
            if isinstance(date_str, str):
                date_part = date_str.split("T")[0]
                return date.fromisoformat(date_part)
        except (ValueError, TypeError) as e:
            _log.warning(f"Failed to parse date '{date_str}': {e}")

        return None

    # -------------------------------------------------------------------------
    # Feature/Parent Operations
    # -------------------------------------------------------------------------

    async def get_feature(self, formatted_id: str) -> tuple[str, str] | None:
        """Fetch a Feature's name by its formatted ID.

        Args:
            formatted_id: The Feature's formatted ID (e.g., "F59625").

        Returns:
            Tuple of (formatted_id, name) if found, None otherwise.
        """
        _log.debug(f"Fetching feature: {formatted_id}")

        try:
            response = await self._get(
                "/portfolioitem/feature",
                params={
                    "fetch": "FormattedID,Name",
                    "query": f'FormattedID = "{formatted_id}"',
                    "projectScopeUp": "true",
                    "projectScopeDown": "true",
                },
            )
            results, _ = parse_query_result(response)
            if results:
                _log.debug(f"Found feature: {formatted_id} - {results[0].get('Name')}")
                return (results[0].get("FormattedID", ""), results[0].get("Name", ""))
        except Exception as e:
            _log.error(f"Error fetching feature {formatted_id}: {e}")

        return None

    async def set_parent(self, ticket: Ticket, parent_id: str) -> Ticket | None:
        """Set a ticket's parent Feature.

        Args:
            ticket: The ticket to update.
            parent_id: The parent Feature's formatted ID.

        Returns:
            The updated Ticket, or None on failure.
        """
        if not ticket.object_id:
            _log.warning(f"Cannot set parent: no object_id for {ticket.formatted_id}")
            return None

        _log.info(f"Setting parent of {ticket.formatted_id} to {parent_id}")

        try:
            # Get the Feature's ObjectID
            feature_response = await self._get(
                "/portfolioitem/feature",
                params={
                    "fetch": "ObjectID",
                    "query": f'FormattedID = "{parent_id}"',
                    "projectScopeUp": "true",
                    "projectScopeDown": "true",
                },
            )
            feature_results, _ = parse_query_result(feature_response)
            if not feature_results:
                _log.error(f"Feature not found: {parent_id}")
                return None

            feature_object_id = feature_results[0].get("ObjectID")
            entity_type = get_entity_type_from_prefix(ticket.formatted_id)
            path = f"/{get_url_path(entity_type)}/{ticket.object_id}"

            response = await self._post(
                path,
                data={
                    entity_type: {
                        "PortfolioItem": f"/portfolioitem/feature/{feature_object_id}",
                    }
                },
            )
            results, _ = parse_query_result(response)

            if results:
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
        except Exception as e:
            _log.error(f"Error setting parent for {ticket.formatted_id}: {e}")

        return None

    # -------------------------------------------------------------------------
    # Bulk Operations (Phase 3)
    # -------------------------------------------------------------------------

    async def bulk_set_parent(self, tickets: list[Ticket], parent_id: str) -> BulkResult:
        """Set parent Feature on multiple tickets concurrently.

        Args:
            tickets: List of tickets to update.
            parent_id: The parent Feature's formatted ID.

        Returns:
            BulkResult with success/failure counts.
        """
        _log.info(f"Bulk setting parent {parent_id} on {len(tickets)} tickets")
        result = BulkResult()

        async def update_one(ticket: Ticket) -> Ticket | Exception:
            if ticket.parent_id:
                return ticket  # Skip tickets with parent
            try:
                updated = await self.set_parent(ticket, parent_id)
                return updated if updated else Exception("Update failed")
            except Exception as e:
                return e

        results = await asyncio.gather(*[update_one(t) for t in tickets])

        for i, res in enumerate(results):
            if isinstance(res, Ticket):
                if res.parent_id == parent_id:
                    result.success_count += 1
                    result.updated_tickets.append(res)
            elif isinstance(res, Exception):
                result.failed_count += 1
                result.errors.append(f"{tickets[i].formatted_id}: {str(res)}")

        _log.info(
            f"Bulk parent complete: {result.success_count} success, {result.failed_count} failed"
        )
        return result

    async def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult:
        """Update state on multiple tickets concurrently.

        Args:
            tickets: List of tickets to update.
            state: The new state value.

        Returns:
            BulkResult with success/failure counts.
        """
        _log.info(f"Bulk updating state to {state} on {len(tickets)} tickets")
        result = BulkResult()

        async def update_one(ticket: Ticket) -> Ticket | Exception:
            try:
                updated = await self.update_state(ticket, state)
                return updated if updated else Exception("Update failed")
            except Exception as e:
                return e

        results = await asyncio.gather(*[update_one(t) for t in tickets])

        for i, res in enumerate(results):
            if isinstance(res, Ticket):
                result.success_count += 1
                result.updated_tickets.append(res)
            elif isinstance(res, Exception):
                result.failed_count += 1
                result.errors.append(f"{tickets[i].formatted_id}: {str(res)}")

        _log.info(
            f"Bulk state update complete: {result.success_count} success, "
            f"{result.failed_count} failed"
        )
        return result

    async def bulk_set_iteration(
        self, tickets: list[Ticket], iteration_name: str | None
    ) -> BulkResult:
        """Set iteration on multiple tickets concurrently.

        Args:
            tickets: List of tickets to update.
            iteration_name: The iteration name, or None for backlog.

        Returns:
            BulkResult with success/failure counts.
        """
        _log.info(f"Bulk setting iteration to {iteration_name} on {len(tickets)} tickets")
        result = BulkResult()

        # Get iteration ref once
        iteration_ref: str | None = None
        if iteration_name:
            try:
                response = await self._get(
                    "/iteration",
                    params={
                        "fetch": "Name,ObjectID",
                        "query": f'(Name = "{iteration_name}")',
                        "pagesize": 1,
                    },
                )
                iter_results, _ = parse_query_result(response)
                if iter_results:
                    iteration_ref = f"/iteration/{iter_results[0].get('ObjectID')}"
                else:
                    _log.error(f"Iteration not found: {iteration_name}")
                    result.failed_count = len(tickets)
                    result.errors.append(f"Iteration not found: {iteration_name}")
                    return result
            except Exception as e:
                _log.error(f"Error fetching iteration: {e}")
                result.failed_count = len(tickets)
                result.errors.append(f"Error fetching iteration: {str(e)}")
                return result

        async def update_one(ticket: Ticket) -> Ticket | Exception:
            if not ticket.object_id:
                return Exception("No object_id")
            try:
                entity_type = get_entity_type_from_prefix(ticket.formatted_id)
                path = f"/{get_url_path(entity_type)}/{ticket.object_id}"

                await self._post(
                    path,
                    data={entity_type: {"Iteration": iteration_ref}},
                )

                return Ticket(
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
            except Exception as e:
                return e

        results = await asyncio.gather(*[update_one(t) for t in tickets])

        for i, res in enumerate(results):
            if isinstance(res, Ticket):
                result.success_count += 1
                result.updated_tickets.append(res)
            elif isinstance(res, Exception):
                result.failed_count += 1
                result.errors.append(f"{tickets[i].formatted_id}: {str(res)}")

        _log.info(
            f"Bulk iteration complete: {result.success_count} success, {result.failed_count} failed"
        )
        return result

    async def bulk_update_points(self, tickets: list[Ticket], points: float) -> BulkResult:
        """Update story points on multiple tickets concurrently.

        Args:
            tickets: List of tickets to update.
            points: The new story points value.

        Returns:
            BulkResult with success/failure counts.
        """
        _log.info(f"Bulk updating points to {points} on {len(tickets)} tickets")
        result = BulkResult()

        async def update_one(ticket: Ticket) -> Ticket | Exception:
            try:
                updated = await self.update_points(ticket, points)
                return updated if updated else Exception("Update failed")
            except Exception as e:
                return e

        results = await asyncio.gather(*[update_one(t) for t in tickets])

        for i, res in enumerate(results):
            if isinstance(res, Ticket):
                result.success_count += 1
                result.updated_tickets.append(res)
            elif isinstance(res, Exception):
                result.failed_count += 1
                result.errors.append(f"{tickets[i].formatted_id}: {str(res)}")

        _log.info(
            f"Bulk points update complete: {result.success_count} success, "
            f"{result.failed_count} failed"
        )
        return result

    # -------------------------------------------------------------------------
    # Attachment Operations
    # -------------------------------------------------------------------------

    async def get_attachments(self, ticket: Ticket) -> list[Attachment]:
        """Get all attachments for a ticket.

        Args:
            ticket: The ticket to get attachments for.

        Returns:
            List of Attachment objects.
        """
        if not ticket.object_id:
            _log.debug(f"No object_id for {ticket.formatted_id}, skipping attachments")
            return []

        _log.debug(f"Fetching attachments for {ticket.formatted_id}")

        try:
            get_entity_type_from_prefix(ticket.formatted_id)
            response = await self._get(
                "/attachment",
                params={
                    "fetch": "ObjectID,Name,Size,ContentType",
                    "query": f'(Artifact.ObjectID = "{ticket.object_id}")',
                    "pagesize": MAX_PAGE_SIZE,
                },
            )
            results, _ = parse_query_result(response)

            attachments = [
                Attachment(
                    name=item.get("Name", ""),
                    size=int(item.get("Size", 0)),
                    content_type=item.get("ContentType", "application/octet-stream"),
                    object_id=str(item.get("ObjectID", "")),
                )
                for item in results
            ]
            _log.debug(f"Fetched {len(attachments)} attachments for {ticket.formatted_id}")
            return attachments
        except Exception as e:
            _log.error(f"Error fetching attachments for {ticket.formatted_id}: {e}")
            return []

    async def download_attachment(
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
        if not ticket.object_id:
            _log.warning(f"Cannot download: no object_id for {ticket.formatted_id}")
            return False

        _log.info(f"Downloading attachment {attachment.name} from {ticket.formatted_id}")

        try:
            # Get attachment content (base64 encoded)
            response = await self._get(
                f"/attachment/{attachment.object_id}",
                params={"fetch": "Content"},
            )
            results, _ = parse_query_result(response)

            if results and "Content" in results[0]:
                content = base64.b64decode(results[0]["Content"])
                with open(dest_path, "wb") as f:
                    f.write(content)
                _log.info(f"Downloaded {attachment.name} to {dest_path}")
                return True
            else:
                _log.error(f"Attachment content not found: {attachment.name}")
                return False
        except Exception as e:
            _log.error(f"Error downloading attachment {attachment.name}: {e}")
            return False

    async def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None:
        """Upload a local file as an attachment to a ticket.

        Args:
            ticket: The ticket to attach the file to.
            file_path: The local path of the file to upload.

        Returns:
            The created Attachment on success, None on failure.
        """
        import mimetypes
        import os

        if not ticket.object_id:
            _log.warning(f"Cannot upload: no object_id for {ticket.formatted_id}")
            return None

        if not os.path.exists(file_path):
            _log.error(f"File not found: {file_path}")
            return None

        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024  # 50 MB
        if file_size > max_size:
            _log.error(f"File too large: {file_size} bytes (max {max_size})")
            return None

        _log.info(f"Uploading {file_path} to {ticket.formatted_id}")

        try:
            filename = os.path.basename(file_path)
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"

            # Read and encode file content
            with open(file_path, "rb") as f:
                content = base64.b64encode(f.read()).decode("utf-8")

            # Create attachment content
            content_response = await self._post(
                "/attachmentcontent/create",
                data={"AttachmentContent": {"Content": content}},
            )
            content_results, _ = parse_query_result(content_response)
            if not content_results:
                _log.error("Failed to create attachment content")
                return None

            content_object_id = content_results[0].get("ObjectID")

            # Create attachment record
            entity_type = get_entity_type_from_prefix(ticket.formatted_id)
            att_response = await self._post(
                "/attachment/create",
                data={
                    "Attachment": {
                        "Name": filename,
                        "ContentType": content_type,
                        "Size": file_size,
                        "Content": f"/attachmentcontent/{content_object_id}",
                        "Artifact": f"/{get_url_path(entity_type)}/{ticket.object_id}",
                    }
                },
            )
            att_results, _ = parse_query_result(att_response)

            if att_results:
                _log.info(f"Uploaded {filename} to {ticket.formatted_id}")
                return Attachment(
                    name=filename,
                    size=file_size,
                    content_type=content_type,
                    object_id=str(att_results[0].get("ObjectID", "")),
                )
        except Exception as e:
            _log.error(f"Error uploading attachment to {ticket.formatted_id}: {e}")

        return None

    async def download_embedded_image(self, url: str, dest_path: str) -> bool:
        """Download an embedded image from a URL.

        Args:
            url: The URL of the embedded image.
            dest_path: The local path to save the file to.

        Returns:
            True on success, False on failure.
        """
        # Make URL absolute if relative
        if url.startswith("/"):
            url = f"https://{self._config.server}{url}"

        _log.info(f"Downloading embedded image from {url}")

        try:
            # Use a separate client for direct URL access
            async with httpx.AsyncClient(
                headers={"ZSESSIONID": self._config.apikey},
                timeout=DEFAULT_TIMEOUT,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                with open(dest_path, "wb") as f:
                    f.write(response.content)

                _log.info(f"Downloaded embedded image to {dest_path}")
                return True
        except Exception as e:
            _log.error(f"Error downloading embedded image: {e}")
            return False
