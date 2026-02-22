"""Tests for the 'iterations' command."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Iteration


def _make_iteration(
    name: str = "Sprint 1",
    start_offset: int = 0,
    end_offset: int = 13,
    state: str = "Planning",
) -> Iteration:
    """Create an Iteration with dates relative to today.

    Args:
        name: Iteration name.
        start_offset: Days from today for start date (negative = past).
        end_offset: Days from today for end date.
        state: Iteration state.
    """
    today = date.today()
    return Iteration(
        object_id="it1",
        name=name,
        start_date=today + timedelta(days=start_offset),
        end_date=today + timedelta(days=end_offset),
        state=state,
    )


def _mock_client_with_iterations(iterations_list):
    """Create a mock async client that returns given iterations."""
    mock_client = AsyncMock()
    mock_client.get_iterations = AsyncMock(return_value=iterations_list)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestIterationsHelp:
    """Tests for iterations --help output."""

    def test_help_exits_0(self):
        """'iterations --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["iterations", "--help"])
        assert result.exit_code == 0

    def test_help_shows_count(self):
        """'iterations --help' should show --count option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["iterations", "--help"])
        assert "--count" in result.output

    def test_help_shows_current(self):
        """'iterations --help' should show --current option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["iterations", "--help"])
        assert "--current" in result.output

    def test_help_shows_future(self):
        """'iterations --help' should show --future option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["iterations", "--help"])
        assert "--future" in result.output

    def test_help_shows_past(self):
        """'iterations --help' should show --past option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["iterations", "--help"])
        assert "--past" in result.output

    def test_help_shows_state(self):
        """'iterations --help' should show --state option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["iterations", "--help"])
        assert "--state" in result.output

    def test_help_shows_format(self):
        """'iterations --help' should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["iterations", "--help"])
        assert "--format" in result.output


class TestIterationsNoApiKey:
    """Tests for iterations without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["iterations"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output


class TestIterationsWithMockData:
    """Tests with mocked Rally client."""

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_default(self, mock_client_cls):
        """Default iterations command shows iteration names."""
        current = _make_iteration(
            "Current Sprint", start_offset=-7, end_offset=7, state="Committed"
        )
        past = _make_iteration("Past Sprint", start_offset=-21, end_offset=-8, state="Accepted")

        mock_client_cls.return_value = _mock_client_with_iterations([current, past])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations"])
        assert result.exit_code == 0
        assert "Current Sprint" in result.output
        assert "Past Sprint" in result.output

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_current_flag(self, mock_client_cls):
        """--current flag shows only the current iteration."""
        current = _make_iteration("Current Sprint", start_offset=-7, end_offset=7)
        past = _make_iteration("Past Sprint", start_offset=-21, end_offset=-8)

        mock_client_cls.return_value = _mock_client_with_iterations([current, past])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations", "--current"])
        assert result.exit_code == 0
        assert "Current Sprint" in result.output
        assert "Past Sprint" not in result.output

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_future_flag(self, mock_client_cls):
        """--future flag shows only future iterations."""
        current = _make_iteration("Current Sprint", start_offset=-7, end_offset=7)
        future = _make_iteration("Future Sprint", start_offset=14, end_offset=27)

        mock_client_cls.return_value = _mock_client_with_iterations([current, future])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations", "--future"])
        assert result.exit_code == 0
        assert "Future Sprint" in result.output
        assert "Current Sprint" not in result.output

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_past_flag(self, mock_client_cls):
        """--past flag shows only past iterations."""
        current = _make_iteration("Current Sprint", start_offset=-7, end_offset=7)
        past = _make_iteration("Past Sprint", start_offset=-21, end_offset=-8)

        mock_client_cls.return_value = _mock_client_with_iterations([current, past])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations", "--past"])
        assert result.exit_code == 0
        assert "Past Sprint" in result.output
        assert "Current Sprint" not in result.output

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_state_filter(self, mock_client_cls):
        """--state filter shows only iterations with matching state."""
        committed = _make_iteration("Sprint A", start_offset=-7, end_offset=7, state="Committed")
        planning = _make_iteration("Sprint B", start_offset=14, end_offset=27, state="Planning")

        mock_client_cls.return_value = _mock_client_with_iterations([committed, planning])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations", "--state", "Committed"])
        assert result.exit_code == 0
        assert "Sprint A" in result.output
        assert "Sprint B" not in result.output

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_count_option(self, mock_client_cls):
        """--count option limits the number of iterations shown."""
        sprints = [
            _make_iteration(f"Sprint {i}", start_offset=-14 * i, end_offset=-14 * i + 13)
            for i in range(10)
        ]

        mock_client_cls.return_value = _mock_client_with_iterations(sprints)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations", "--count", "3"])
        assert result.exit_code == 0
        # Should have at most 3 iteration rows (plus header/separator)

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_json_format(self, mock_client_cls):
        """--format json returns valid JSON output."""
        current = _make_iteration("Test Sprint", start_offset=-7, end_offset=7)

        mock_client_cls.return_value = _mock_client_with_iterations([current])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations", "--format", "json"])
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert "Test Sprint" in result.output

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_csv_format(self, mock_client_cls):
        """--format csv returns CSV data."""
        current = _make_iteration("Test Sprint", start_offset=-7, end_offset=7)

        mock_client_cls.return_value = _mock_client_with_iterations([current])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations", "--format", "csv"])
        assert result.exit_code == 0
        assert "name" in result.output
        assert "Test Sprint" in result.output

    @patch("rally_tui.cli.commands.iterations.AsyncRallyClient")
    def test_iterations_empty_results(self, mock_client_cls):
        """Empty iterations shows appropriate message."""
        mock_client_cls.return_value = _mock_client_with_iterations([])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["iterations"])
        assert result.exit_code == 0
        assert "No iterations found" in result.output
