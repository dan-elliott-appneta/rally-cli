"""Tests for the 'completions' command."""

from click.testing import CliRunner

from rally_tui.cli.main import cli


class TestCompletionsHelp:
    """Tests for 'completions --help' output."""

    def test_help_exits_0(self):
        """'completions --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "--help"])
        assert result.exit_code == 0

    def test_help_shows_shell_choices(self):
        """Help should list bash, zsh, fish as valid choices."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "--help"])
        assert result.exit_code == 0
        # At least one shell type should be mentioned
        assert any(shell in result.output for shell in ("bash", "zsh", "fish"))


class TestBashCompletions:
    """Tests for 'completions bash' output."""

    def test_bash_completions_exits_0(self):
        """'completions bash' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "bash"])
        assert result.exit_code == 0

    def test_bash_completions_output(self):
        """'completions bash' should output eval instruction."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "bash"])
        assert result.exit_code == 0
        assert "_RALLY_CLI_COMPLETE" in result.output
        assert "bash" in result.output.lower()


class TestZshCompletions:
    """Tests for 'completions zsh' output."""

    def test_zsh_completions_exits_0(self):
        """'completions zsh' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "zsh"])
        assert result.exit_code == 0

    def test_zsh_completions_output(self):
        """'completions zsh' should output zsh eval instruction."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "zsh"])
        assert result.exit_code == 0
        assert "_RALLY_CLI_COMPLETE" in result.output
        assert "zsh" in result.output.lower()


class TestFishCompletions:
    """Tests for 'completions fish' output."""

    def test_fish_completions_exits_0(self):
        """'completions fish' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "fish"])
        assert result.exit_code == 0

    def test_fish_completions_output(self):
        """'completions fish' should output fish source instruction."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "fish"])
        assert result.exit_code == 0
        assert "_RALLY_CLI_COMPLETE" in result.output
        assert "fish" in result.output.lower()


class TestCompletionsInvalidShell:
    """Tests for 'completions' with invalid shell argument."""

    def test_invalid_shell_exits_nonzero(self):
        """Invalid shell argument should exit non-zero."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completions", "powershell"])
        assert result.exit_code != 0
