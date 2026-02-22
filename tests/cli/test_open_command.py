"""Tests for the 'open' command."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Ticket


def _make_ticket(
    object_id: str = "987654321",
    formatted_id: str = "US12345",
    ticket_type: str = "UserStory",
    name: str = "Test Ticket",
    state: str = "In-Progress",
) -> Ticket:
    """Create a minimal Ticket for testing."""
    return Ticket(
        object_id=object_id,
        formatted_id=formatted_id,
        name=name,
        state=state,
        ticket_type=ticket_type,
        owner="Jane Smith",
        points=3.0,
    )


def _mock_client_with_ticket(ticket: Ticket | None):
    """Create a mock async client that returns the given ticket."""
    mock_client = AsyncMock()
    mock_client.get_ticket = AsyncMock(return_value=ticket)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestOpenHelp:
    """Tests for 'open --help' output."""

    def test_help_exits_0(self):
        """'open --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["open", "--help"])
        assert result.exit_code == 0

    def test_help_shows_ticket_id_argument(self):
        """Help should mention TICKET_ID argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ["open", "--help"])
        assert "TICKET_ID" in result.output


class TestOpenNoApiKey:
    """Tests for 'open' without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["open", "US12345"])
        assert result.exit_code == 4

    def test_no_apikey_shows_rally_apikey_message(self):
        """Without API key, error mentions RALLY_APIKEY."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["open", "US12345"])
        assert "RALLY_APIKEY" in result.output


class TestOpenInvalidId:
    """Tests for 'open' with invalid ticket IDs."""

    def test_invalid_ticket_id_exits_2(self):
        """Invalid ticket ID format exits with code 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["open", "INVALID123"])
        assert result.exit_code == 2

    def test_numeric_only_id_exits_2(self):
        """Numeric-only ID is rejected with exit code 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["open", "12345"])
        assert result.exit_code == 2

    def test_valid_prefix_ids_pass_validation(self):
        """Valid ID prefixes (US, DE, TA, TC, S, F) pass validation."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        valid_ids = ["US12345", "DE67890", "TA111", "TC222", "S333", "F444"]
        for ticket_id in valid_ids:
            with patch("rally_tui.cli.commands.open_cmd.AsyncRallyClient") as mock_cls:
                mock_cls.return_value = _mock_client_with_ticket(None)
                result = runner.invoke(cli, ["open", ticket_id])
                # Should not fail with exit code 2 (validation error)
                assert result.exit_code != 2, f"ID {ticket_id} incorrectly rejected"


class TestOpenWithMockData:
    """Tests with mocked Rally client."""

    @patch("rally_tui.cli.commands.open_cmd.webbrowser")
    @patch("rally_tui.cli.commands.open_cmd.AsyncRallyClient")
    def test_opens_correct_url_in_browser(self, mock_client_cls, mock_browser):
        """Valid ticket ID opens the correct Rally URL in browser."""
        ticket = _make_ticket(object_id="987654321", formatted_id="US12345")
        mock_client_cls.return_value = _mock_client_with_ticket(ticket)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["open", "US12345"])
        assert result.exit_code == 0
        # webbrowser.open should have been called with a Rally URL
        mock_browser.open.assert_called_once()
        url_arg = mock_browser.open.call_args[0][0]
        assert "rally1.rallydev.com" in url_arg
        assert "987654321" in url_arg

    @patch("rally_tui.cli.commands.open_cmd.webbrowser")
    @patch("rally_tui.cli.commands.open_cmd.AsyncRallyClient")
    def test_ticket_not_found_exits_1(self, mock_client_cls, mock_browser):
        """Ticket not found exits with code 1."""
        mock_client_cls.return_value = _mock_client_with_ticket(None)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["open", "US99999"])
        assert result.exit_code == 1

    @patch("rally_tui.cli.commands.open_cmd.webbrowser")
    @patch("rally_tui.cli.commands.open_cmd.AsyncRallyClient")
    def test_auth_error_handling(self, mock_client_cls, mock_browser):
        """401 errors produce 'Authentication failed' message and exit 1."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(side_effect=Exception("401 Unauthorized"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "bad_key"})
        result = runner.invoke(cli, ["open", "US12345"])
        assert result.exit_code == 1
        assert "Authentication failed" in result.output

    @patch("rally_tui.cli.commands.open_cmd.webbrowser")
    @patch("rally_tui.cli.commands.open_cmd.AsyncRallyClient")
    def test_api_error_exits_1(self, mock_client_cls, mock_browser):
        """API errors exit with code 1."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(side_effect=Exception("Network timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["open", "US12345"])
        assert result.exit_code == 1

    @patch("rally_tui.cli.commands.open_cmd.webbrowser")
    @patch("rally_tui.cli.commands.open_cmd.AsyncRallyClient")
    def test_defect_url_uses_defect_type(self, mock_client_cls, mock_browser):
        """Defect tickets use the 'defect' URL type."""
        ticket = _make_ticket(object_id="111222333", formatted_id="DE67890", ticket_type="Defect")
        mock_client_cls.return_value = _mock_client_with_ticket(ticket)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["open", "DE67890"])
        assert result.exit_code == 0
        mock_browser.open.assert_called_once()
        url_arg = mock_browser.open.call_args[0][0]
        assert "defect" in url_arg
        assert "111222333" in url_arg

    @patch("rally_tui.cli.commands.open_cmd.webbrowser")
    @patch("rally_tui.cli.commands.open_cmd.AsyncRallyClient")
    def test_output_shows_opening_message(self, mock_client_cls, mock_browser):
        """Opening a ticket prints a message to stdout."""
        ticket = _make_ticket(object_id="987654321")
        mock_client_cls.return_value = _mock_client_with_ticket(ticket)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["open", "US12345"])
        assert result.exit_code == 0
        assert "US12345" in result.output
