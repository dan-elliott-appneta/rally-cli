"""Tests for creating and updating tickets without an owner."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from rally_tui.config import RallyConfig
from rally_tui.models import Ticket
from rally_tui.services.async_rally_client import AsyncRallyClient
from rally_tui.services.mock_client import MockRallyClient


def _client() -> AsyncRallyClient:
    client = AsyncRallyClient(RallyConfig(apikey="x"))
    client._current_user = "Jane Doe"
    client._current_iteration = None
    return client


def _created_response() -> dict[str, Any]:
    return {
        "CreateResult": {},
        "QueryResult": {
            "Results": [{"FormattedID": "US1", "Name": "T", "ObjectID": 1}],
            "Errors": [],
            "TotalResultCount": 1,
        },
    }


class TestMockClientNoOwner:
    def test_create_defaults_to_current_user(self) -> None:
        ticket = MockRallyClient(current_user="Jane").create_ticket("T", "HierarchicalRequirement")
        assert ticket is not None and ticket.owner == "Jane"

    def test_create_no_owner(self) -> None:
        ticket = MockRallyClient(current_user="Jane").create_ticket(
            "T", "HierarchicalRequirement", no_owner=True
        )
        assert ticket is not None and ticket.owner is None


class TestAsyncClientNoOwner:
    @pytest.mark.asyncio
    async def test_create_sets_owner_by_default(self) -> None:
        client = _client()
        client._get = AsyncMock(return_value={"QueryResult": {"Results": [{"ObjectID": 7}]}})  # type: ignore[method-assign]
        client._post = AsyncMock(return_value=_created_response())  # type: ignore[method-assign]
        await client.create_ticket("T", "HierarchicalRequirement")
        sent = client._post.call_args.kwargs["data"]["HierarchicalRequirement"]
        assert sent["Owner"] == "/user/7"

    @pytest.mark.asyncio
    async def test_create_no_owner_omits_owner(self) -> None:
        client = _client()
        client._get = AsyncMock()  # type: ignore[method-assign]
        client._post = AsyncMock(return_value=_created_response())  # type: ignore[method-assign]
        await client.create_ticket("T", "HierarchicalRequirement", no_owner=True)
        sent = client._post.call_args.kwargs["data"]["HierarchicalRequirement"]
        assert "Owner" not in sent
        client._get.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_owner_none_unassigns(self) -> None:
        client = _client()
        client._get = AsyncMock()  # type: ignore[method-assign]
        client._post = AsyncMock(return_value={"OperationResult": {"Errors": []}})  # type: ignore[method-assign]
        client.get_ticket = AsyncMock(return_value=None)  # type: ignore[method-assign]
        ticket = Ticket(
            formatted_id="US1", name="T", ticket_type="UserStory", state="Defined", object_id="1"
        )
        await client.update_ticket(ticket, {"owner": None})
        sent = client._post.call_args.kwargs["data"]["HierarchicalRequirement"]
        assert sent == {"Owner": None}
        client._get.assert_not_called()
