"""Tests for the 'discussions' command."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Discussion, Ticket


def _make_ticket(ticket_id: str = "US12345") -> Ticket:
    """Create a minimal Ticket for testing."""
    return Ticket(
        formatted_id=ticket_id,
        name="Test story",
        ticket_type="UserStory",
        state="Defined",
        object_id="99999",
    )


def _make_discussion(
    text: str = "Hello",
    user: str = "Jane Smith",
    artifact_id: str = "US12345",
) -> Discussion:
    """Create a Discussion instance for testing."""
    return Discussion(
        object_id="d1",
        text=text,
        user=user,
        created_at=datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
        artifact_id=artifact_id,
    )


class TestDiscussionsHelp:
    """Tests for discussions --help output."""

    def test_help_shows_ticket_id(self):
        """'discussions --help' should mention TICKET_ID."""
        runner = CliRunner()
        result = runner.invoke(cli, ["discussions", "--help"])
        assert result.exit_code == 0
        assert "TICKET_ID" in result.output

    def test_help_shows_format_option(self):
        """'discussions --help' should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["discussions", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output


class TestDiscussionsNoApiKey:
    """Tests for discussions without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["discussions", "US12345"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output


class TestDiscussionsInvalidTicketId:
    """Tests for invalid ticket ID format."""

    def test_invalid_id_exits_2(self):
        """Invalid ticket ID exits with code 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["discussions", "INVALID"])
        assert result.exit_code == 2

    def test_numeric_only_id_exits_2(self):
        """Numeric-only ticket ID is rejected."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["discussions", "12345"])
        assert result.exit_code == 2


class TestDiscussionsWithMockData:
    """Tests with mocked Rally client."""

    @patch("rally_tui.cli.commands.discussions.AsyncRallyClient")
    def test_discussions_text_format(self, mock_client_cls):
        """Discussions in text format shows user and text."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=_make_ticket())
        mock_client.get_discussions = AsyncMock(
            return_value=[_make_discussion(text="First comment")]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["discussions", "US12345"])
        assert result.exit_code == 0
        assert "Jane Smith" in result.output
        assert "First comment" in result.output

    @patch("rally_tui.cli.commands.discussions.AsyncRallyClient")
    def test_discussions_json_format(self, mock_client_cls):
        """Discussions in JSON format returns valid JSON with data array."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=_make_ticket())
        mock_client.get_discussions = AsyncMock(
            return_value=[_make_discussion(text="JSON comment")]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["discussions", "US12345", "--format", "json"])
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert "JSON comment" in result.output

    @patch("rally_tui.cli.commands.discussions.AsyncRallyClient")
    def test_discussions_csv_format(self, mock_client_cls):
        """Discussions in CSV format returns CSV data."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=_make_ticket())
        mock_client.get_discussions = AsyncMock(return_value=[_make_discussion(text="CSV comment")])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["discussions", "US12345", "--format", "csv"])
        assert result.exit_code == 0
        assert "artifact_id" in result.output
        assert "CSV comment" in result.output

    @patch("rally_tui.cli.commands.discussions.AsyncRallyClient")
    def test_discussions_empty_results(self, mock_client_cls):
        """Empty discussions list shows appropriate message."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=_make_ticket())
        mock_client.get_discussions = AsyncMock(return_value=[])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["discussions", "US12345"])
        assert result.exit_code == 0
        assert "No discussions found" in result.output

    @patch("rally_tui.cli.commands.discussions.AsyncRallyClient")
    def test_discussions_ticket_not_found(self, mock_client_cls):
        """When ticket is not found, exits with error."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=None)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["discussions", "US99999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_valid_ticket_prefixes_accepted(self):
        """Various valid prefixes should pass ID validation."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        valid_ids = ["US12345", "DE67890", "TA111", "TC222", "S333", "F444"]
        for ticket_id in valid_ids:
            result = runner.invoke(cli, ["discussions", ticket_id])
            # Should fail with exit code 1 (API error) not 2 (validation)
            assert result.exit_code != 2, f"Ticket ID {ticket_id} was incorrectly rejected"
