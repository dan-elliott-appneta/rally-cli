"""Tests for the 'attachments' command group."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Attachment, Ticket


def _make_ticket(
    formatted_id: str = "US12345",
    name: str = "Test Ticket",
) -> Ticket:
    """Create a Ticket for testing."""
    return Ticket(
        formatted_id=formatted_id,
        name=name,
        ticket_type="UserStory",
        state="Defined",
        owner="Test User",
        description="",
        notes="",
        iteration=None,
        points=None,
        object_id="123456",
        parent_id=None,
    )


def _make_attachment(
    name: str = "requirements.pdf",
    size: int = 250880,
    content_type: str = "application/pdf",
    object_id: str = "att1",
) -> Attachment:
    """Create an Attachment for testing."""
    return Attachment(
        name=name,
        size=size,
        content_type=content_type,
        object_id=object_id,
    )


def _mock_client_with_attachments(ticket, attachments_list):
    """Create a mock async client that returns given ticket and attachments."""
    mock_client = AsyncMock()
    mock_client.get_ticket = AsyncMock(return_value=ticket)
    mock_client.get_attachments = AsyncMock(return_value=attachments_list)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestAttachmentsHelp:
    """Tests for attachments --help output."""

    def test_help_exits_0(self):
        """'attachments --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["attachments", "--help"])
        assert result.exit_code == 0

    def test_help_shows_subcommands(self):
        """'attachments --help' should show list, download, upload subcommands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["attachments", "--help"])
        assert "list" in result.output
        assert "download" in result.output
        assert "upload" in result.output


class TestAttachmentsListHelp:
    """Tests for attachments list --help output."""

    def test_list_help_exits_0(self):
        """'attachments list --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["attachments", "list", "--help"])
        assert result.exit_code == 0

    def test_list_help_shows_format(self):
        """'attachments list --help' should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["attachments", "list", "--help"])
        assert "--format" in result.output


class TestAttachmentsListNoApiKey:
    """Tests for attachments list without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["attachments", "list", "US12345"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output


class TestAttachmentsList:
    """Tests for listing attachments."""

    @patch("rally_tui.cli.commands.attachments.AsyncRallyClient")
    def test_list_with_attachments(self, mock_client_cls):
        """Listing attachments shows file names."""
        ticket = _make_ticket()
        attachments_list = [
            _make_attachment("requirements.pdf", 250880, "application/pdf", "a1"),
            _make_attachment("screenshot.png", 102400, "image/png", "a2"),
        ]

        mock_client_cls.return_value = _mock_client_with_attachments(ticket, attachments_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["attachments", "list", "US12345"])
        assert result.exit_code == 0
        assert "requirements.pdf" in result.output
        assert "screenshot.png" in result.output

    @patch("rally_tui.cli.commands.attachments.AsyncRallyClient")
    def test_list_json_format(self, mock_client_cls):
        """Listing attachments with --format json returns JSON output."""
        ticket = _make_ticket()
        attachments_list = [
            _make_attachment("requirements.pdf", 250880, "application/pdf", "a1"),
        ]

        mock_client_cls.return_value = _mock_client_with_attachments(ticket, attachments_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["attachments", "list", "US12345", "--format", "json"])
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert "requirements.pdf" in result.output

    @patch("rally_tui.cli.commands.attachments.AsyncRallyClient")
    def test_list_empty(self, mock_client_cls):
        """Empty attachments shows appropriate message."""
        ticket = _make_ticket()
        mock_client_cls.return_value = _mock_client_with_attachments(ticket, [])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["attachments", "list", "US12345"])
        assert result.exit_code == 0
        assert "No attachments found" in result.output


class TestAttachmentsDownloadHelp:
    """Tests for attachments download --help output."""

    def test_download_help_exits_0(self):
        """'attachments download --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["attachments", "download", "--help"])
        assert result.exit_code == 0

    def test_download_help_shows_options(self):
        """'attachments download --help' should show --output and --all options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["attachments", "download", "--help"])
        assert "--output" in result.output
        assert "--all" in result.output
        assert "--output-dir" in result.output


class TestAttachmentsUploadHelp:
    """Tests for attachments upload --help output."""

    def test_upload_help_exits_0(self):
        """'attachments upload --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["attachments", "upload", "--help"])
        assert result.exit_code == 0

    def test_upload_help_shows_format(self):
        """'attachments upload --help' should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["attachments", "upload", "--help"])
        assert "--format" in result.output


class TestAttachmentsInvalidTicketId:
    """Tests for invalid ticket ID validation."""

    def test_list_invalid_ticket_id(self):
        """Listing attachments with invalid ticket ID exits 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["attachments", "list", "INVALID"])
        assert result.exit_code == 2
        assert "Invalid ticket ID" in result.output

    def test_download_invalid_ticket_id(self):
        """Downloading from invalid ticket ID exits 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["attachments", "download", "BADID", "file.txt"])
        assert result.exit_code == 2

    def test_upload_invalid_ticket_id(self, tmp_path):
        """Uploading to invalid ticket ID exits 2."""
        # Create a temp file so click.Path(exists=True) passes
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["attachments", "upload", "BADID", str(test_file)])
        assert result.exit_code == 2


class TestAttachmentsErrorCases:
    """Tests for error handling in attachments commands."""

    @patch("rally_tui.cli.commands.attachments.AsyncRallyClient")
    def test_list_ticket_not_found(self, mock_client_cls):
        """Listing attachments on nonexistent ticket shows error."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=None)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["attachments", "list", "US99999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("rally_tui.cli.commands.attachments.AsyncRallyClient")
    def test_list_api_error(self, mock_client_cls):
        """API error when listing attachments shows error message."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["attachments", "list", "US12345"])
        assert result.exit_code == 1
        assert "Failed to fetch attachments" in result.output
