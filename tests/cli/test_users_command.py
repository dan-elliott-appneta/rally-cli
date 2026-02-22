"""Tests for the 'users' command."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Owner


def _make_owner(
    display_name: str = "John Smith",
    user_name: str | None = "jsmith@example.com",
    object_id: str = "u1",
) -> Owner:
    """Create an Owner instance for testing."""
    return Owner(
        object_id=object_id,
        display_name=display_name,
        user_name=user_name,
    )


def _mock_client_with_users(users_list):
    """Create a mock async client that returns given users."""
    mock_client = AsyncMock()
    mock_client.get_users = AsyncMock(return_value=users_list)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestUsersHelp:
    """Tests for users --help output."""

    def test_help_exits_0(self):
        """'users --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["users", "--help"])
        assert result.exit_code == 0

    def test_help_shows_search(self):
        """'users --help' should show --search option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["users", "--help"])
        assert "--search" in result.output

    def test_help_shows_format(self):
        """'users --help' should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["users", "--help"])
        assert "--format" in result.output


class TestUsersNoApiKey:
    """Tests for users without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["users"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output


class TestUsersWithMockData:
    """Tests with mocked Rally client."""

    @patch("rally_tui.cli.commands.users.AsyncRallyClient")
    def test_users_default(self, mock_client_cls):
        """Default users command shows user names."""
        users_list = [
            _make_owner("Alice Brown", "abrown@example.com", "u1"),
            _make_owner("Bob Jones", "bjones@example.com", "u2"),
        ]

        mock_client_cls.return_value = _mock_client_with_users(users_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["users"])
        assert result.exit_code == 0
        assert "Alice Brown" in result.output
        assert "Bob Jones" in result.output

    @patch("rally_tui.cli.commands.users.AsyncRallyClient")
    def test_users_search_filter(self, mock_client_cls):
        """--search filter matches by display name substring."""
        users_list = [
            _make_owner("Daniel Elliot", "delliot@example.com", "u1"),
            _make_owner("Jane Smith", "jsmith@example.com", "u2"),
        ]

        mock_client_cls.return_value = _mock_client_with_users(users_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["users", "--search", "Daniel"])
        assert result.exit_code == 0
        assert "Daniel Elliot" in result.output
        assert "Jane Smith" not in result.output

    @patch("rally_tui.cli.commands.users.AsyncRallyClient")
    def test_users_search_case_insensitive(self, mock_client_cls):
        """--search is case-insensitive."""
        users_list = [
            _make_owner("Daniel Elliot", "delliot@example.com", "u1"),
        ]

        mock_client_cls.return_value = _mock_client_with_users(users_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["users", "--search", "daniel"])
        assert result.exit_code == 0
        assert "Daniel Elliot" in result.output

    @patch("rally_tui.cli.commands.users.AsyncRallyClient")
    def test_users_json_format(self, mock_client_cls):
        """--format json returns valid JSON output."""
        users_list = [_make_owner("Test User", "tuser@example.com")]

        mock_client_cls.return_value = _mock_client_with_users(users_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["users", "--format", "json"])
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert "Test User" in result.output

    @patch("rally_tui.cli.commands.users.AsyncRallyClient")
    def test_users_csv_format(self, mock_client_cls):
        """--format csv returns CSV data."""
        users_list = [_make_owner("Test User", "tuser@example.com")]

        mock_client_cls.return_value = _mock_client_with_users(users_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["users", "--format", "csv"])
        assert result.exit_code == 0
        assert "display_name" in result.output
        assert "Test User" in result.output

    @patch("rally_tui.cli.commands.users.AsyncRallyClient")
    def test_users_empty_results(self, mock_client_cls):
        """Empty users list shows appropriate message."""
        mock_client_cls.return_value = _mock_client_with_users([])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["users"])
        assert result.exit_code == 0
        assert "No users found" in result.output

    @patch("rally_tui.cli.commands.users.AsyncRallyClient")
    def test_users_sorted_by_name(self, mock_client_cls):
        """Users are sorted alphabetically by display name."""
        users_list = [
            _make_owner("Zoe Adams", "zadams@example.com", "u1"),
            _make_owner("Alice Baker", "abaker@example.com", "u2"),
        ]

        mock_client_cls.return_value = _mock_client_with_users(users_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["users"])
        assert result.exit_code == 0
        # Alice should appear before Zoe
        alice_pos = result.output.index("Alice Baker")
        zoe_pos = result.output.index("Zoe Adams")
        assert alice_pos < zoe_pos

    @patch("rally_tui.cli.commands.users.AsyncRallyClient")
    def test_users_search_no_matches(self, mock_client_cls):
        """--search with no matches shows no users found message."""
        users_list = [_make_owner("Alice Baker")]

        mock_client_cls.return_value = _mock_client_with_users(users_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["users", "--search", "NonExistent"])
        assert result.exit_code == 0
        assert "No users found" in result.output
