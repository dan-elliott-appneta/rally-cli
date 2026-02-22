"""Config command for showing current Rally CLI configuration.

This module implements the 'config' command for displaying the current
configuration values sourced from environment variables or CLI flags.
"""

import sys

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context


def _mask_apikey(apikey: str) -> str:
    """Mask an API key for display, showing only the last 4 characters.

    Args:
        apikey: The API key string to mask.

    Returns:
        Masked API key string, e.g. '****...1234', or '(not set)' if empty.
    """
    if not apikey:
        return "(not set)"
    if len(apikey) <= 4:
        return "****"
    return f"****...{apikey[-4:]}"


@click.command("config")
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@pass_context
def config(ctx: CLIContext, sub_format: str | None) -> None:
    """Show current Rally CLI configuration.

    Displays the server, workspace, project, and API key (masked) that
    are currently in use. Values are sourced from environment variables
    or command-line flags.

    Examples:

    \b
        rally-cli config
        rally-cli config --format json
        rally-cli config --format csv
    """
    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))

    # Determine the source of the API key
    apikey_display = _mask_apikey(ctx.apikey)
    if ctx.apikey:
        apikey_display = f"{apikey_display} (set via RALLY_APIKEY)"

    config_data = {
        "server": ctx.server or "rally1.rallydev.com",
        "workspace": ctx.workspace or "(not set)",
        "project": ctx.project or "(not set)",
        "apikey": apikey_display,
        "apikey_raw": ctx.apikey,
    }

    result = CLIResult(success=True, data=config_data)
    click.echo(ctx.formatter.format_config(result))
    sys.exit(0)


# Register command with CLI
cli.add_command(config)
