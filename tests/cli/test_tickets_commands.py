"""Tests for tickets show, update, and delete subcommands, and --format override."""

from click.testing import CliRunner

from rally_tui.cli.main import cli


class TestTicketsShow:
    """Tests for the 'tickets show' subcommand."""

    def test_show_help(self):
        """'tickets show --help' should succeed and mention TICKET_ID."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "show", "--help"])
        assert result.exit_code == 0
        assert "TICKET_ID" in result.output

    def test_show_no_apikey(self):
        """'tickets show' without API key exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets", "show", "US12345"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output

    def test_show_invalid_ticket_id(self):
        """'tickets show INVALID' with a bad ID exits with code 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tickets", "show", "INVALID"])
        assert result.exit_code == 2

    def test_show_invalid_ticket_id_numeric_only(self):
        """Numeric-only ticket ID is rejected."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tickets", "show", "12345"])
        assert result.exit_code == 2

    def test_show_format_option_accepted(self):
        """--format json should be accepted (API key error is checked after format parsing)."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets", "show", "--format", "json", "US12345"])
        # Exits 4 for missing API key but the format option itself was valid
        assert result.exit_code == 4

    def test_show_format_json_option_in_help(self):
        """--format option should appear in 'tickets show --help'."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "show", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output

    def test_show_valid_prefixes_accepted(self):
        """Various valid prefixes (US, DE, TA, TC, S, F) should pass validation."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        valid_ids = ["US12345", "DE67890", "TA111", "TC222", "S333", "F444"]
        for ticket_id in valid_ids:
            result = runner.invoke(cli, ["tickets", "show", ticket_id])
            # Should fail with exit code 1 (API error) not 2 (input validation error)
            assert result.exit_code != 2, f"Ticket ID {ticket_id} was incorrectly rejected"


class TestTicketsUpdate:
    """Tests for the 'tickets update' subcommand."""

    def test_update_help(self):
        """'tickets update --help' should list key options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert result.exit_code == 0
        assert "--state" in result.output
        assert "--owner" in result.output
        assert "--notes" in result.output
        assert "--ac" in result.output
        assert "--points" in result.output
        assert "--parent" in result.output
        assert "--description" in result.output

    def test_update_no_apikey(self):
        """'tickets update' without API key exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets", "update", "US12345", "--state", "Completed"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output

    def test_update_no_options(self):
        """'tickets update US12345' with no update options exits with code 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tickets", "update", "US12345"])
        assert result.exit_code == 2

    def test_update_invalid_ticket_id(self):
        """'tickets update INVALID' with a bad ID exits with code 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tickets", "update", "INVALID", "--state", "Done"])
        assert result.exit_code == 2

    def test_update_blocked_flag(self):
        """--blocked flag should appear in help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert "--blocked" in result.output

    def test_update_ready_flag(self):
        """--ready flag should appear in help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert "--ready" in result.output

    def test_update_no_iteration_flag(self):
        """--no-iteration flag should appear in help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert "--no-iteration" in result.output

    def test_update_description_file_nonexistent(self):
        """--description-file with non-existent path causes Click to reject with exit 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(
            cli,
            ["tickets", "update", "US12345", "--description-file", "/nonexistent/path.txt"],
        )
        assert result.exit_code == 2

    def test_update_notes_file_option_in_help(self):
        """--notes-file option appears in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert "--notes-file" in result.output

    def test_update_ac_file_option_in_help(self):
        """--ac-file option appears in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert "--ac-file" in result.output

    def test_update_format_json_option_in_help(self):
        """--format option appears in 'tickets update --help'."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert "--format" in result.output

    def test_update_target_date_option_in_help(self):
        """--target-date option appears in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert "--target-date" in result.output

    def test_update_severity_priority_in_help(self):
        """--severity and --priority options appear in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "update", "--help"])
        assert "--severity" in result.output
        assert "--priority" in result.output

    def test_update_description_file_is_read(self, tmp_path):
        """--description-file reads the file content (validated via Click, exits 4 on no key)."""
        desc_file = tmp_path / "desc.txt"
        desc_file.write_text("My description content")

        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(
            cli,
            ["tickets", "update", "US12345", "--description-file", str(desc_file)],
        )
        # Without API key exits 4, not 2 (file was accepted by Click)
        assert result.exit_code == 4


class TestTicketsDelete:
    """Tests for the 'tickets delete' subcommand."""

    def test_delete_help(self):
        """'tickets delete --help' should mention --confirm."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "delete", "--help"])
        assert result.exit_code == 0
        assert "--confirm" in result.output

    def test_delete_no_confirm(self):
        """'tickets delete US12345' without --confirm exits with code 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tickets", "delete", "US12345"])
        assert result.exit_code == 2

    def test_delete_no_apikey(self):
        """'tickets delete' with --confirm but no API key exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets", "delete", "US12345", "--confirm"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output

    def test_delete_invalid_ticket_id(self):
        """'tickets delete INVALID --confirm' exits with code 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["tickets", "delete", "INVALID", "--confirm"])
        assert result.exit_code == 2

    def test_delete_format_option_in_help(self):
        """--format option appears in 'tickets delete --help'."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "delete", "--help"])
        assert "--format" in result.output

    def test_delete_ticket_id_in_help(self):
        """TICKET_ID argument appears in help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "delete", "--help"])
        assert "TICKET_ID" in result.output


class TestFormatOverride:
    """Tests for --format on the tickets group."""

    def test_format_on_tickets_group_help(self):
        """'rally-cli tickets --format json --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--format", "json", "--help"])
        assert result.exit_code == 0

    def test_format_text_on_tickets_group(self):
        """'rally-cli tickets --format text --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--format", "text", "--help"])
        assert result.exit_code == 0

    def test_format_csv_on_tickets_group(self):
        """'rally-cli tickets --format csv --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--format", "csv", "--help"])
        assert result.exit_code == 0

    def test_format_invalid_on_tickets_group(self):
        """'rally-cli tickets --format invalid' without --help should exit non-zero."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets", "--format", "invalid"])
        assert result.exit_code != 0

    def test_format_option_in_tickets_help(self):
        """--format option appears in 'tickets --help' output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--help"])
        assert "--format" in result.output

    def test_format_on_tickets_subcommand_show(self):
        """'rally-cli tickets --format json show --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--format", "json", "show", "--help"])
        assert result.exit_code == 0

    def test_format_on_tickets_subcommand_update(self):
        """'rally-cli tickets --format json update --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--format", "json", "update", "--help"])
        assert result.exit_code == 0

    def test_format_no_apikey_with_json_output(self):
        """When --format json is set on tickets group, error output is still produced."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets", "--format", "json"])
        assert result.exit_code == 4


class TestBackwardCompatibility:
    """Tests ensuring existing behaviour is not broken."""

    def test_format_on_global_still_works(self):
        """'rally-cli --format json tickets --help' should still work."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--format", "json", "tickets", "--help"])
        assert result.exit_code == 0

    def test_tickets_list_still_works(self):
        """'rally-cli tickets' without API key still exits 4 with message."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output

    def test_tickets_create_still_works(self):
        """'rally-cli tickets create Test' without API key still exits 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["tickets", "create", "Test"])
        assert result.exit_code == 4

    def test_tickets_create_help_still_works(self):
        """'rally-cli tickets create --help' should still show all original options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "create", "--help"])
        assert result.exit_code == 0
        assert "--description" in result.output
        assert "--points" in result.output
        assert "--type" in result.output
        assert "--backlog" in result.output

    def test_comment_command_still_works(self):
        """'rally-cli comment --help' should still work unaffected."""
        runner = CliRunner()
        result = runner.invoke(cli, ["comment", "--help"])
        assert result.exit_code == 0
        assert "TICKET_ID" in result.output

    def test_tickets_current_iteration_flag_still_works(self):
        """--current-iteration flag still accepted on tickets group."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--current-iteration", "--help"])
        assert result.exit_code == 0

    def test_tickets_my_tickets_flag_still_works(self):
        """--my-tickets flag still accepted on tickets group."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--my-tickets", "--help"])
        assert result.exit_code == 0

    def test_tickets_show_is_new_subcommand_in_help(self):
        """'show' subcommand appears in 'tickets --help' output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--help"])
        assert "show" in result.output

    def test_tickets_update_is_new_subcommand_in_help(self):
        """'update' subcommand appears in 'tickets --help' output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--help"])
        assert "update" in result.output

    def test_tickets_delete_is_new_subcommand_in_help(self):
        """'delete' subcommand appears in 'tickets --help' output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tickets", "--help"])
        assert "delete" in result.output
