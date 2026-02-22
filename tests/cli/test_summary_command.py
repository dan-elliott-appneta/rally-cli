"""Tests for the 'summary' command."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli


def _make_summary(
    iteration_name: str = "Sprint 1",
    start_date: str | None = "2026-02-10",
    end_date: str | None = "2026-02-21",
    total_tickets: int = 10,
    total_points: float = 20.0,
    by_state: list | None = None,
    by_owner: list | None = None,
    blocked: list | None = None,
) -> dict:
    """Create a minimal sprint summary dict for testing."""
    return {
        "iteration_name": iteration_name,
        "start_date": start_date,
        "end_date": end_date,
        "total_tickets": total_tickets,
        "total_points": total_points,
        "by_state": by_state
        or [
            {"state": "Defined", "count": 3, "points": 5.0},
            {"state": "In-Progress", "count": 5, "points": 10.0},
            {"state": "Completed", "count": 2, "points": 5.0},
        ],
        "by_owner": by_owner
        or [
            {"owner": "Jane Smith", "count": 6, "points": 12.0},
            {"owner": "Bob Johnson", "count": 4, "points": 8.0},
        ],
        "blocked": blocked or [],
    }


def _mock_client_with_summary(summary_data: dict):
    """Create a mock async client that returns the given summary."""
    mock_client = AsyncMock()
    mock_client.get_sprint_summary = AsyncMock(return_value=summary_data)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestSummaryHelp:
    """Tests for 'summary --help' output."""

    def test_help_exits_0(self):
        """'summary --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["summary", "--help"])
        assert result.exit_code == 0

    def test_help_shows_iteration_option(self):
        """Help should show --iteration option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["summary", "--help"])
        assert "--iteration" in result.output

    def test_help_shows_format_option(self):
        """Help should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["summary", "--help"])
        assert "--format" in result.output


class TestSummaryNoApiKey:
    """Tests for 'summary' without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 4

    def test_no_apikey_shows_rally_apikey_message(self):
        """Without API key, error mentions RALLY_APIKEY."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["summary"])
        assert "RALLY_APIKEY" in result.output


class TestSummaryWithMockData:
    """Tests with mocked Rally client."""

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_default_summary_shows_current_iteration(self, mock_client_cls):
        """Default summary shows iteration name."""
        data = _make_summary(iteration_name="Sprint 7")
        mock_client_cls.return_value = _mock_client_with_summary(data)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 0
        assert "Sprint 7" in result.output

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_summary_with_iteration_flag(self, mock_client_cls):
        """--iteration passes name to client."""
        data = _make_summary(iteration_name="Custom Sprint")
        mock_client = _mock_client_with_summary(data)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary", "--iteration", "Custom Sprint"])
        assert result.exit_code == 0
        mock_client.get_sprint_summary.assert_called_once_with(iteration_name="Custom Sprint")

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_summary_format_json(self, mock_client_cls):
        """--format json returns valid JSON envelope."""
        import json

        data = _make_summary()
        mock_client_cls.return_value = _mock_client_with_summary(data)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary", "--format", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "data" in parsed

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_summary_shows_state_breakdown(self, mock_client_cls):
        """Text summary shows By State section."""
        data = _make_summary()
        mock_client_cls.return_value = _mock_client_with_summary(data)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 0
        assert "By State" in result.output
        assert "Defined" in result.output
        assert "In-Progress" in result.output

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_summary_shows_owner_breakdown(self, mock_client_cls):
        """Text summary shows By Owner section."""
        data = _make_summary()
        mock_client_cls.return_value = _mock_client_with_summary(data)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 0
        assert "By Owner" in result.output
        assert "Jane Smith" in result.output

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_summary_shows_blocked_tickets(self, mock_client_cls):
        """Text summary shows Blocked section when there are blocked tickets."""
        data = _make_summary(
            blocked=[
                {
                    "formatted_id": "US12345",
                    "name": "My story",
                    "blocked_reason": "Waiting on API team",
                },
            ]
        )
        mock_client_cls.return_value = _mock_client_with_summary(data)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 0
        assert "Blocked" in result.output
        assert "US12345" in result.output

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_summary_empty_iteration(self, mock_client_cls):
        """Summary with zero tickets exits 0 and shows totals."""
        data = _make_summary(
            total_tickets=0, total_points=0.0, by_state=[], by_owner=[], blocked=[]
        )
        mock_client_cls.return_value = _mock_client_with_summary(data)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 0
        assert "0" in result.output

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_api_error_handling(self, mock_client_cls):
        """API errors exit with code 1."""
        mock_client = AsyncMock()
        mock_client.get_sprint_summary = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 1

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_auth_error_handling(self, mock_client_cls):
        """401 errors produce 'Authentication failed' message."""
        mock_client = AsyncMock()
        mock_client.get_sprint_summary = AsyncMock(side_effect=Exception("401 Unauthorized"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "bad_key"})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 1
        assert "Authentication failed" in result.output

    @patch("rally_tui.cli.commands.summary.AsyncRallyClient")
    def test_summary_shows_totals(self, mock_client_cls):
        """Summary output shows total ticket count and points."""
        data = _make_summary(total_tickets=24, total_points=47.0)
        mock_client_cls.return_value = _mock_client_with_summary(data)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 0
        assert "24" in result.output
        assert "47" in result.output
