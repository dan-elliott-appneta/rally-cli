"""Tests for creating Tasks under a parent User Story."""

from typing import Any
from unittest.mock import AsyncMock

import pytest
from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient
from rally_tui.services.mock_client import MockRallyClient


def _client() -> AsyncRallyClient:
    client = AsyncRallyClient(RallyConfig(apikey="x"))
    client._current_user = "Jane Doe"
    client._current_iteration = "Sprint 1"
    return client


def _created_response() -> dict[str, Any]:
    return {
        "CreateResult": {},
        "QueryResult": {
            "Results": [{"FormattedID": "TA1", "Name": "T", "ObjectID": 1}],
            "Errors": [],
            "TotalResultCount": 1,
        },
    }


class TestMockClientTask:
    def test_task_takes_parent_iteration(self) -> None:
        client = MockRallyClient(current_user="Jane", current_iteration="Sprint 9")
        parent = next(t for t in client.get_tickets() if t.iteration)
        task = client.create_ticket("T", "Task", parent=parent.formatted_id)
        assert task is not None
        assert task.formatted_id.startswith("TA")
        assert task.ticket_type == "Task"
        assert task.iteration == parent.iteration
        assert task.owner == "Jane"

    def test_task_with_unknown_parent_fails(self) -> None:
        assert MockRallyClient().create_ticket("T", "Task", parent="US0") is None


class TestAsyncClientTask:
    @pytest.mark.asyncio
    async def test_task_sets_work_product_and_skips_iteration(self) -> None:
        client = _client()
        client._get = AsyncMock(return_value={"QueryResult": {"Results": [{"ObjectID": 42}]}})  # type: ignore[method-assign]
        client._post = AsyncMock(return_value=_created_response())  # type: ignore[method-assign]
        created = await client.create_ticket("T", "Task", parent="US100")
        assert created is not None and created.ticket_type == "Task"
        path = client._post.call_args.args[0]
        sent = client._post.call_args.kwargs["data"]["Task"]
        assert path == "/task/create"
        assert sent["WorkProduct"] == "/hierarchicalrequirement/42"
        assert sent["Owner"] == "/user/42"
        assert "Iteration" not in sent
        assert "PlanEstimate" not in sent

    @pytest.mark.asyncio
    async def test_task_without_parent_is_rejected(self) -> None:
        client = _client()
        client._get = AsyncMock()  # type: ignore[method-assign]
        client._post = AsyncMock()  # type: ignore[method-assign]
        assert await client.create_ticket("T", "Task") is None
        client._post.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_with_unknown_parent_is_not_created(self) -> None:
        client = _client()
        client._get = AsyncMock(return_value={"QueryResult": {"Results": []}})  # type: ignore[method-assign]
        client._post = AsyncMock()  # type: ignore[method-assign]
        assert await client.create_ticket("T", "Task", parent="US404") is None
        client._post.assert_not_called()


class TestCreateTaskCommand:
    def _invoke(self, *args: str) -> Any:
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        return runner.invoke(cli, ["tickets", "create", "T", *args])

    def test_task_requires_parent(self) -> None:
        result = self._invoke("--type", "Task")
        assert result.exit_code == 2
        assert "--parent is required" in result.output

    def test_parent_rejected_for_story(self) -> None:
        result = self._invoke("--parent", "US1")
        assert result.exit_code == 2
        assert "only supported for --type Task" in result.output

    @pytest.mark.parametrize("flag", [["--points", "1"], ["--backlog"]])
    def test_story_only_flags_rejected_for_task(self, flag: list[str]) -> None:
        result = self._invoke("--type", "Task", "--parent", "US1", *flag)
        assert result.exit_code == 2
        assert "do not apply" in result.output

    def test_help_lists_task_and_parent(self) -> None:
        result = CliRunner().invoke(cli, ["tickets", "create", "--help"])
        assert "--parent" in result.output
        assert "Task" in result.output
