"""Tests for CLI entry point."""

from click.testing import CliRunner

from rally_tui.cli.main import cli


class TestCLIEntryPoint:
    """Tests for the main CLI entry point."""

    def test_cli_help(self):
        """Test that --help displays help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Rally CLI" in result.output
        assert "tickets" in result.output
        assert "comment" in result.output

    def test_cli_version(self):
        """Test that --version displays version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "rally-cli" in result.output

    def test_tickets_help(self):
        """Test that tickets --help displays help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--help"])
        assert result.exit_code == 0
        assert "--current-iteration" in result.output
        assert "--my-tickets" in result.output
        assert "--format" in result.output

    def test_comment_help(self):
        """Test that comment --help displays help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["comment", "--help"])
        assert result.exit_code == 0
        assert "TICKET_ID" in result.output
        assert "--message-file" in result.output

    def test_global_options(self):
        """Test that global options are recognized."""
        runner = CliRunner()
        # Test with tickets command
        result = runner.invoke(
            cli,
            [
                "--server",
                "test.server.com",
                "--format",
                "json",
                "tickets",
                "--help",
            ],
        )
        assert result.exit_code == 0

    def test_tickets_no_apikey_error(self):
        """Test that tickets command fails without API key."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})  # Empty apikey
        result = runner.invoke(cli, ["tickets"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output

    def test_comment_no_apikey_error(self):
        """Test that comment command fails without API key."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})  # Empty apikey
        result = runner.invoke(cli, ["comment", "US12345", "test message"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output

    def test_comment_invalid_ticket_id(self):
        """Test that comment command validates ticket ID format."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["comment", "INVALID123", "test message"])
        assert result.exit_code == 2
        assert "Invalid ticket ID format" in result.output

    def test_comment_missing_message(self):
        """Test that comment command requires a message."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["comment", "US12345"])
        assert result.exit_code == 2
        assert "No comment text provided" in result.output

    def test_tickets_create_help(self):
        """Test that tickets create --help shows create options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "create", "--help"])
        assert result.exit_code == 0
        assert "--description" in result.output
        assert "--points" in result.output
        assert "--type" in result.output
        assert "UserStory" in result.output or "Defect" in result.output

    def test_tickets_create_no_apikey_error(self):
        """Test that tickets create fails without API key."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets", "create", "Test"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output


class TestOutputFormat:
    """Tests for output format selection."""

    def test_text_format_default(self):
        """Test that text format is the default."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # Default should be text
        assert "text" in result.output.lower()

    def test_json_format_option(self):
        """Test that JSON format option is available."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--format", "json", "tickets", "--help"])
        assert result.exit_code == 0

    def test_csv_format_option(self):
        """Test that CSV format option is available."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--format", "csv", "tickets", "--help"])
        assert result.exit_code == 0

    def test_invalid_format_error(self):
        """Test that invalid format raises error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--format", "invalid", "tickets"])
        assert result.exit_code != 0
