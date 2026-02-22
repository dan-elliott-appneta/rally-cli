"""Tests for the 'releases' command."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Release


def _make_release(
    name: str = "2026.Q1",
    start_offset: int = -30,
    end_offset: int = 60,
    state: str = "Active",
    theme: str = "",
) -> Release:
    """Create a Release with dates relative to today.

    Args:
        name: Release name.
        start_offset: Days from today for start date (negative = past).
        end_offset: Days from today for end date.
        state: Release state.
        theme: Release theme.
    """
    today = date.today()
    return Release(
        object_id="rel1",
        name=name,
        start_date=today + timedelta(days=start_offset),
        end_date=today + timedelta(days=end_offset),
        state=state,
        theme=theme,
    )


def _mock_client_with_releases(releases_list):
    """Create a mock async client that returns given releases."""
    mock_client = AsyncMock()
    mock_client.get_releases = AsyncMock(return_value=releases_list)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestReleasesHelp:
    """Tests for releases --help output."""

    def test_help_exits_0(self):
        """'releases --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["releases", "--help"])
        assert result.exit_code == 0

    def test_help_shows_count(self):
        """'releases --help' should show --count option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["releases", "--help"])
        assert "--count" in result.output

    def test_help_shows_current(self):
        """'releases --help' should show --current option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["releases", "--help"])
        assert "--current" in result.output

    def test_help_shows_state(self):
        """'releases --help' should show --state option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["releases", "--help"])
        assert "--state" in result.output

    def test_help_shows_format(self):
        """'releases --help' should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["releases", "--help"])
        assert "--format" in result.output


class TestReleasesNoApiKey:
    """Tests for releases without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["releases"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output


class TestReleasesWithMockData:
    """Tests with mocked Rally client."""

    @patch("rally_tui.cli.commands.releases.AsyncRallyClient")
    def test_releases_default(self, mock_client_cls):
        """Default releases command shows release names."""
        active = _make_release(
            "2026.Q1", start_offset=-30, end_offset=60, state="Active", theme="Security hardening"
        )
        planning = _make_release(
            "2026.Q2", start_offset=61, end_offset=150, state="Planning", theme="Performance"
        )

        mock_client_cls.return_value = _mock_client_with_releases([active, planning])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["releases"])
        assert result.exit_code == 0
        assert "2026.Q1" in result.output
        assert "2026.Q2" in result.output

    @patch("rally_tui.cli.commands.releases.AsyncRallyClient")
    def test_releases_current_flag(self, mock_client_cls):
        """--current flag shows only the current/active release."""
        active = _make_release("2026.Q1", start_offset=-30, end_offset=60, state="Active")
        future = _make_release("2026.Q2", start_offset=61, end_offset=150, state="Planning")

        mock_client_cls.return_value = _mock_client_with_releases([active, future])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["releases", "--current"])
        assert result.exit_code == 0
        assert "2026.Q1" in result.output
        assert "2026.Q2" not in result.output

    @patch("rally_tui.cli.commands.releases.AsyncRallyClient")
    def test_releases_state_filter(self, mock_client_cls):
        """--state filter shows only releases with matching state."""
        active = _make_release("2026.Q1", start_offset=-30, end_offset=60, state="Active")
        locked = _make_release("2025.Q4", start_offset=-120, end_offset=-31, state="Locked")

        mock_client_cls.return_value = _mock_client_with_releases([active, locked])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["releases", "--state", "Active"])
        assert result.exit_code == 0
        assert "2026.Q1" in result.output
        assert "2025.Q4" not in result.output

    @patch("rally_tui.cli.commands.releases.AsyncRallyClient")
    def test_releases_count_option(self, mock_client_cls):
        """--count option limits the number of releases shown."""
        releases_list = [
            _make_release(f"Release {i}", start_offset=-90 * i, end_offset=-90 * i + 89)
            for i in range(10)
        ]

        mock_client_cls.return_value = _mock_client_with_releases(releases_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["releases", "--count", "3"])
        assert result.exit_code == 0

    @patch("rally_tui.cli.commands.releases.AsyncRallyClient")
    def test_releases_json_format(self, mock_client_cls):
        """--format json returns valid JSON output."""
        active = _make_release("2026.Q1", start_offset=-30, end_offset=60, state="Active")

        mock_client_cls.return_value = _mock_client_with_releases([active])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["releases", "--format", "json"])
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert "2026.Q1" in result.output

    @patch("rally_tui.cli.commands.releases.AsyncRallyClient")
    def test_releases_csv_format(self, mock_client_cls):
        """--format csv returns CSV data."""
        active = _make_release("2026.Q1", start_offset=-30, end_offset=60, state="Active")

        mock_client_cls.return_value = _mock_client_with_releases([active])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["releases", "--format", "csv"])
        assert result.exit_code == 0
        assert "name" in result.output
        assert "2026.Q1" in result.output

    @patch("rally_tui.cli.commands.releases.AsyncRallyClient")
    def test_releases_empty_results(self, mock_client_cls):
        """Empty releases shows appropriate message."""
        mock_client_cls.return_value = _mock_client_with_releases([])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["releases"])
        assert result.exit_code == 0
        assert "No releases found" in result.output

    @patch("rally_tui.cli.commands.releases.AsyncRallyClient")
    def test_releases_with_theme(self, mock_client_cls):
        """Releases with theme data show theme in text output."""
        release = _make_release(
            "2026.Q1", start_offset=-30, end_offset=60, state="Active", theme="Security hardening"
        )

        mock_client_cls.return_value = _mock_client_with_releases([release])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["releases"])
        assert result.exit_code == 0
        assert "Security hardening" in result.output
