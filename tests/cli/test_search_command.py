"""Tests for the 'search' command."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Ticket


def _make_ticket(
    formatted_id: str = "US12345",
    name: str = "Test Ticket",
    state: str = "In-Progress",
    ticket_type: str = "UserStory",
    owner: str = "Jane Smith",
    points: float = 3.0,
) -> Ticket:
    """Create a minimal Ticket for testing."""
    return Ticket(
        object_id=formatted_id,
        formatted_id=formatted_id,
        name=name,
        state=state,
        ticket_type=ticket_type,
        owner=owner,
        points=points,
        iteration="Sprint 1",
    )


def _mock_client_with_tickets(tickets_list):
    """Create a mock async client that returns given tickets from search."""
    mock_client = AsyncMock()
    mock_client.search_tickets = AsyncMock(return_value=tickets_list)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestSearchHelp:
    """Tests for 'search --help' output."""

    def test_help_exits_0(self):
        """'search --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0

    def test_help_shows_query_argument(self):
        """Help should mention the QUERY argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert "QUERY" in result.output

    def test_help_shows_type_option(self):
        """Help should show --type option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert "--type" in result.output

    def test_help_shows_state_option(self):
        """Help should show --state option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert "--state" in result.output

    def test_help_shows_limit_option(self):
        """Help should show --limit option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert "--limit" in result.output

    def test_help_shows_format_option(self):
        """Help should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert "--format" in result.output

    def test_help_shows_current_iteration_option(self):
        """Help should show --current-iteration option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert "--current-iteration" in result.output


class TestSearchNoApiKey:
    """Tests for 'search' without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["search", "OAuth login"])
        assert result.exit_code == 4

    def test_no_apikey_shows_rally_apikey_message(self):
        """Without API key, error mentions RALLY_APIKEY."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["search", "OAuth login"])
        assert "RALLY_APIKEY" in result.output


class TestSearchWithMockData:
    """Tests with mocked Rally client."""

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_basic_search_returns_results(self, mock_client_cls):
        """Basic search returns matching tickets."""
        ticket = _make_ticket(name="OAuth login screen")
        mock_client_cls.return_value = _mock_client_with_tickets([ticket])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "OAuth login"])
        assert result.exit_code == 0
        assert "US12345" in result.output

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_search_with_type_filter(self, mock_client_cls):
        """Search with --type passes type to client."""
        ticket = _make_ticket(ticket_type="Defect", formatted_id="DE99")
        mock_client = _mock_client_with_tickets([ticket])
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "OAuth", "--type", "Defect"])
        assert result.exit_code == 0
        mock_client.search_tickets.assert_called_once()
        call_kwargs = mock_client.search_tickets.call_args
        assert call_kwargs.kwargs.get("ticket_type") == "Defect" or (
            len(call_kwargs.args) > 1 and call_kwargs.args[1] == "Defect"
        )

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_search_with_state_filter(self, mock_client_cls):
        """Search with --state passes state to client."""
        ticket = _make_ticket(state="In-Progress")
        mock_client = _mock_client_with_tickets([ticket])
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "login", "--state", "In-Progress"])
        assert result.exit_code == 0
        mock_client.search_tickets.assert_called_once()

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_search_with_current_iteration(self, mock_client_cls):
        """Search with --current-iteration passes flag to client."""
        mock_client = _mock_client_with_tickets([])
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "login", "--current-iteration"])
        assert result.exit_code == 0
        mock_client.search_tickets.assert_called_once()
        call_kwargs = mock_client.search_tickets.call_args
        # current_iteration should be True
        assert call_kwargs.kwargs.get("current_iteration") is True or (
            any(a is True for a in call_kwargs.args)
        )

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_search_with_limit(self, mock_client_cls):
        """Search with --limit passes limit to client."""
        mock_client = _mock_client_with_tickets([])
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "OAuth", "--limit", "10"])
        assert result.exit_code == 0
        mock_client.search_tickets.assert_called_once()
        call_kwargs = mock_client.search_tickets.call_args
        assert call_kwargs.kwargs.get("limit") == 10 or (any(a == 10 for a in call_kwargs.args))

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_search_format_json(self, mock_client_cls):
        """Search with --format json returns valid JSON envelope."""
        import json

        ticket = _make_ticket()
        mock_client_cls.return_value = _mock_client_with_tickets([ticket])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "OAuth", "--format", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "data" in parsed

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_empty_search_results(self, mock_client_cls):
        """Empty search results exits 0 with 'No tickets found' message."""
        mock_client_cls.return_value = _mock_client_with_tickets([])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "zxzxzxzx_nonexistent"])
        assert result.exit_code == 0
        assert "No tickets found" in result.output

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_api_error_handling(self, mock_client_cls):
        """API errors exit with code 1 and show error message."""
        mock_client = AsyncMock()
        mock_client.search_tickets = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "OAuth"])
        assert result.exit_code == 1

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_auth_error_handling(self, mock_client_cls):
        """401 errors produce 'Authentication failed' message."""
        mock_client = AsyncMock()
        mock_client.search_tickets = AsyncMock(side_effect=Exception("401 Unauthorized"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "bad_key"})
        result = runner.invoke(cli, ["search", "OAuth"])
        assert result.exit_code == 1
        assert "Authentication failed" in result.output

    @patch("rally_tui.cli.commands.search.AsyncRallyClient")
    def test_search_multiple_results(self, mock_client_cls):
        """Multiple results are all displayed."""
        tickets = [
            _make_ticket("US100", "OAuth login"),
            _make_ticket("US101", "OAuth logout"),
            _make_ticket("DE200", "OAuth token bug", ticket_type="Defect"),
        ]
        mock_client_cls.return_value = _mock_client_with_tickets(tickets)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["search", "OAuth"])
        assert result.exit_code == 0
        assert "US100" in result.output
        assert "US101" in result.output
        assert "DE200" in result.output
