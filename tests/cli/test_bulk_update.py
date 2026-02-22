"""Tests for bulk ticket update (multiple ticket IDs)."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Ticket


def _make_ticket(
    formatted_id: str = "US12345",
    state: str = "In-Progress",
    name: str = "Test Ticket",
) -> Ticket:
    """Create a minimal Ticket for testing."""
    return Ticket(
        object_id=formatted_id,
        formatted_id=formatted_id,
        name=name,
        state=state,
        ticket_type="UserStory",
        owner="Jane Smith",
        points=3.0,
    )


def _mock_client_for_update(
    get_responses: dict[str, Ticket | None],
    update_responses: dict[str, Ticket | None] | None = None,
):
    """Create a mock async client with configurable per-ticket responses.

    Args:
        get_responses: Map of ticket_id -> Ticket (or None if not found).
        update_responses: Map of ticket_id -> updated Ticket (or None).
                          Defaults to returning the same ticket.
    """
    if update_responses is None:
        update_responses = {k: v for k, v in get_responses.items() if v is not None}

    async def _get_ticket(ticket_id: str) -> Ticket | None:
        return get_responses.get(ticket_id)

    async def _update_ticket(ticket: Ticket, fields: dict) -> Ticket | None:
        updated = update_responses.get(ticket.formatted_id)
        return updated

    mock_client = AsyncMock()
    mock_client.get_ticket = AsyncMock(side_effect=_get_ticket)
    mock_client.update_ticket = AsyncMock(side_effect=_update_ticket)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestBulkUpdateHelp:
    """Tests for 'tickets update --help' with bulk update context."""

    def test_help_shows_ticket_ids_plural(self):
        """Help should show TICKET_IDS argument (plural, nargs=-1)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert result.exit_code == 0
        # Should indicate multiple IDs are accepted
        assert "TICKET_IDS" in result.output or "ticket_ids" in result.output.lower()

    def test_help_exits_0(self):
        """'tickets update --help' exits 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert result.exit_code == 0


class TestBulkUpdateMultipleIds:
    """Tests for updating multiple tickets at once."""

    @patch("rally_tui.cli.commands.query.AsyncRallyClient")
    def test_multiple_ticket_ids_accepted(self, mock_client_cls):
        """Multiple ticket IDs can be passed to tickets update."""
        t1 = _make_ticket("US12345")
        t2 = _make_ticket("US12346")
        mock_client_cls.return_value = _mock_client_for_update({"US12345": t1, "US12346": t2})

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(
            cli, ["tickets", "update", "US12345", "US12346", "--state", "Completed"]
        )
        assert result.exit_code == 0

    @patch("rally_tui.cli.commands.query.AsyncRallyClient")
    def test_each_ticket_updated(self, mock_client_cls):
        """Each ticket ID is individually updated."""
        t1 = _make_ticket("US12345")
        t2 = _make_ticket("US12346")
        t3 = _make_ticket("US12347")
        mock_client = _mock_client_for_update({"US12345": t1, "US12346": t2, "US12347": t3})
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(
            cli,
            ["tickets", "update", "US12345", "US12346", "US12347", "--state", "Completed"],
        )
        assert result.exit_code == 0
        # get_ticket called once per ticket
        assert mock_client.get_ticket.call_count == 3

    @patch("rally_tui.cli.commands.query.AsyncRallyClient")
    def test_success_summary_shown(self, mock_client_cls):
        """Successful bulk update shows which tickets were updated."""
        t1 = _make_ticket("US12345")
        t2 = _make_ticket("US12346")
        mock_client_cls.return_value = _mock_client_for_update({"US12345": t1, "US12346": t2})

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(
            cli, ["tickets", "update", "US12345", "US12346", "--state", "Completed"]
        )
        assert result.exit_code == 0
        # Should show both IDs in success summary
        assert "US12345" in result.output
        assert "US12346" in result.output

    @patch("rally_tui.cli.commands.query.AsyncRallyClient")
    def test_some_failures_reported(self, mock_client_cls):
        """Failures for individual tickets are reported."""
        t1 = _make_ticket("US12345")
        # US12346 returns None (not found)
        mock_client = _mock_client_for_update({"US12345": t1, "US12346": None})
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(
            cli, ["tickets", "update", "US12345", "US12346", "--state", "Completed"]
        )
        # Should exit 0 (some succeeded)
        assert result.exit_code == 0
        # US12346 failure should be mentioned
        assert "US12346" in result.output

    @patch("rally_tui.cli.commands.query.AsyncRallyClient")
    def test_all_failures_exits_1(self, mock_client_cls):
        """When all tickets fail, exit code is 1."""
        # Both return None (not found)
        mock_client_cls.return_value = _mock_client_for_update({"US12345": None, "US12346": None})

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(
            cli, ["tickets", "update", "US12345", "US12346", "--state", "Completed"]
        )
        assert result.exit_code == 1

    @patch("rally_tui.cli.commands.query.AsyncRallyClient")
    def test_invalid_id_in_bulk_list_exits_2(self, mock_client_cls):
        """Invalid ticket ID in bulk list causes exit 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(
            cli,
            ["tickets", "update", "US12345", "INVALID_ID", "--state", "Completed"],
        )
        assert result.exit_code == 2

    @patch("rally_tui.cli.commands.query.AsyncRallyClient")
    def test_no_options_exits_2_for_bulk(self, mock_client_cls):
        """Bulk update without any field options exits 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tickets", "update", "US12345", "US12346"])
        assert result.exit_code == 2

    @patch("rally_tui.cli.commands.query.AsyncRallyClient")
    def test_mixed_success_failure_exits_0(self, mock_client_cls):
        """Mixed success/failure (at least one success) exits 0."""
        t1 = _make_ticket("US12345")
        mock_client_cls.return_value = _mock_client_for_update({"US12345": t1, "US12346": None})

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(
            cli, ["tickets", "update", "US12345", "US12346", "--state", "Completed"]
        )
        assert result.exit_code == 0
