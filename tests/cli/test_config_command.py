"""Tests for the 'config' command."""

import json

from click.testing import CliRunner

from rally_tui.cli.main import cli


class TestConfigCommand:
    """Tests for the 'config' command."""

    def test_config_help_exits_0(self):
        """'config --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0

    def test_config_shows_server(self):
        """Config output includes the server hostname."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key", "RALLY_SERVER": "myserver.example.com"})
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "myserver.example.com" in result.output

    def test_config_shows_default_server(self):
        """Config shows default server when RALLY_SERVER is not set."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "rally1.rallydev.com" in result.output

    def test_config_shows_workspace(self):
        """Config output includes the workspace name."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key", "RALLY_WORKSPACE": "My Workspace"})
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "My Workspace" in result.output

    def test_config_shows_project(self):
        """Config output includes the project name."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key", "RALLY_PROJECT": "My Project"})
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "My Project" in result.output

    def test_config_shows_masked_api_key(self):
        """Config output shows masked API key (last 4 chars only)."""
        runner = CliRunner(env={"RALLY_APIKEY": "abcd1234efgh5678"})
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        # Last 4 chars should be visible
        assert "5678" in result.output
        # Full key should NOT appear
        assert "abcd1234efgh5678" not in result.output

    def test_config_format_json(self):
        """Config with --format json returns valid JSON."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key_5678", "RALLY_WORKSPACE": "Test WS"})
        result = runner.invoke(cli, ["config", "--format", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "data" in parsed
        data = parsed["data"]
        assert "server" in data
        assert "workspace" in data

    def test_config_without_api_key_shows_not_set(self):
        """Config without API key shows '(not set)' indicator."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "not set" in result.output

    def test_config_shows_configuration_header(self):
        """Config text output has a header line."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "Configuration" in result.output
