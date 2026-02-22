"""Tests for the 'tags' command group."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Tag, Ticket


def _make_tag(name: str = "sprint-goal", object_id: str = "tag1") -> Tag:
    """Create a Tag for testing."""
    return Tag(object_id=object_id, name=name)


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


def _mock_client_with_tags(tags_list):
    """Create a mock async client that returns given tags."""
    mock_client = AsyncMock()
    mock_client.get_tags = AsyncMock(return_value=tags_list)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestTagsHelp:
    """Tests for tags --help output."""

    def test_help_exits_0(self):
        """'tags --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tags", "--help"])
        assert result.exit_code == 0

    def test_help_shows_format(self):
        """'tags --help' should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tags", "--help"])
        assert "--format" in result.output

    def test_help_shows_subcommands(self):
        """'tags --help' should show create, add, remove subcommands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tags", "--help"])
        assert "create" in result.output
        assert "add" in result.output
        assert "remove" in result.output


class TestTagsNoApiKey:
    """Tests for tags without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tags"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output


class TestTagsList:
    """Tests for listing tags."""

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_list_default(self, mock_client_cls):
        """Default tags command shows tag names."""
        tags_list = [
            _make_tag("sprint-goal", "t1"),
            _make_tag("backlog", "t2"),
            _make_tag("technical-debt", "t3"),
        ]

        mock_client_cls.return_value = _mock_client_with_tags(tags_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags"])
        assert result.exit_code == 0
        assert "sprint-goal" in result.output
        assert "backlog" in result.output
        assert "technical-debt" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_list_json_format(self, mock_client_cls):
        """--format json returns valid JSON output."""
        tags_list = [_make_tag("sprint-goal")]

        mock_client_cls.return_value = _mock_client_with_tags(tags_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "--format", "json"])
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert "sprint-goal" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_list_csv_format(self, mock_client_cls):
        """--format csv returns CSV data."""
        tags_list = [_make_tag("sprint-goal")]

        mock_client_cls.return_value = _mock_client_with_tags(tags_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "--format", "csv"])
        assert result.exit_code == 0
        assert "name" in result.output
        assert "sprint-goal" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_list_empty(self, mock_client_cls):
        """Empty tags shows appropriate message."""
        mock_client_cls.return_value = _mock_client_with_tags([])

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags"])
        assert result.exit_code == 0
        assert "No tags found" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_list_sorted(self, mock_client_cls):
        """Tags should be sorted alphabetically."""
        tags_list = [
            _make_tag("zebra", "t1"),
            _make_tag("alpha", "t2"),
            _make_tag("middle", "t3"),
        ]

        mock_client_cls.return_value = _mock_client_with_tags(tags_list)

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        # Find the tag lines (after header)
        # Header: Tags, ====, Name, ----
        # Tag data starts after the separator line
        data_start = None
        for i, line in enumerate(lines):
            if line.startswith("-"):
                data_start = i + 1
                break
        assert data_start is not None
        tag_lines = [line for line in lines[data_start:] if line.strip()]
        assert tag_lines == ["alpha", "middle", "zebra"]


class TestTagsCreate:
    """Tests for creating tags."""

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_create_success(self, mock_client_cls):
        """Creating a tag succeeds."""
        mock_client = AsyncMock()
        created_tag = _make_tag("new-tag", "t99")
        mock_client.create_tag = AsyncMock(return_value=created_tag)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "create", "new-tag"])
        assert result.exit_code == 0
        assert "new-tag" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_create_failure(self, mock_client_cls):
        """Creating a tag that fails shows error."""
        mock_client = AsyncMock()
        mock_client.create_tag = AsyncMock(return_value=None)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "create", "bad-tag"])
        assert result.exit_code == 1

    def test_tags_create_no_apikey(self):
        """Creating a tag without API key exits 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tags", "create", "test-tag"])
        assert result.exit_code == 4

    def test_tags_create_help(self):
        """'tags create --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tags", "create", "--help"])
        assert result.exit_code == 0


class TestTagsAdd:
    """Tests for adding tags to tickets."""

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_add_success(self, mock_client_cls):
        """Adding a tag to a ticket succeeds."""
        ticket = _make_ticket()
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=ticket)
        mock_client.add_tag = AsyncMock(return_value=ticket)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "add", "US12345", "sprint-goal"])
        assert result.exit_code == 0
        assert "sprint-goal" in result.output
        assert "US12345" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_add_ticket_not_found(self, mock_client_cls):
        """Adding a tag to a nonexistent ticket fails."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=None)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "add", "US99999", "sprint-goal"])
        assert result.exit_code == 1

    def test_tags_add_invalid_ticket_id(self):
        """Adding a tag with invalid ticket ID exits 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "add", "INVALID", "sprint-goal"])
        assert result.exit_code == 2

    def test_tags_add_no_apikey(self):
        """Adding a tag without API key exits 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tags", "add", "US12345", "sprint-goal"])
        assert result.exit_code == 4


class TestTagsRemove:
    """Tests for removing tags from tickets."""

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_remove_success(self, mock_client_cls):
        """Removing a tag from a ticket succeeds."""
        ticket = _make_ticket()
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=ticket)
        mock_client.remove_tag = AsyncMock(return_value=ticket)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "remove", "US12345", "sprint-goal"])
        assert result.exit_code == 0
        assert "sprint-goal" in result.output
        assert "US12345" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_remove_ticket_not_found(self, mock_client_cls):
        """Removing a tag from nonexistent ticket fails."""
        mock_client = AsyncMock()
        mock_client.get_ticket = AsyncMock(return_value=None)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "remove", "US99999", "sprint-goal"])
        assert result.exit_code == 1

    def test_tags_remove_invalid_ticket_id(self):
        """Removing a tag with invalid ticket ID exits 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "remove", "INVALID", "sprint-goal"])
        assert result.exit_code == 2

    def test_tags_remove_no_apikey(self):
        """Removing a tag without API key exits 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tags", "remove", "US12345", "sprint-goal"])
        assert result.exit_code == 4

    def test_tags_remove_help(self):
        """'tags remove --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tags", "remove", "--help"])
        assert result.exit_code == 0


class TestTagsErrorCases:
    """Tests for error handling in tags commands."""

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_list_api_error(self, mock_client_cls):
        """API error when listing tags shows error message."""
        mock_client = AsyncMock()
        mock_client.get_tags = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags"])
        assert result.exit_code == 1
        assert "Failed to fetch tags" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_list_auth_error(self, mock_client_cls):
        """Authentication error when listing tags shows auth message."""
        mock_client = AsyncMock()
        mock_client.get_tags = AsyncMock(side_effect=Exception("401 Unauthorized"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags"])
        assert result.exit_code == 1
        assert "Authentication failed" in result.output

    @patch("rally_tui.cli.commands.tags.AsyncRallyClient")
    def test_tags_create_exception(self, mock_client_cls):
        """Exception when creating tag shows error message."""
        mock_client = AsyncMock()
        mock_client.create_tag = AsyncMock(side_effect=Exception("Server error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tags", "create", "test-tag"])
        assert result.exit_code == 1
        assert "Failed to create tag" in result.output
