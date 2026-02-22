"""Summary command for sprint/iteration reporting.

This module implements the 'summary' command for generating sprint summary
reports showing ticket counts, point totals, state breakdowns, owner
breakdowns, and blocked ticket lists.
"""

import asyncio
import sys

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient


@click.command("summary")
@click.option(
    "--iteration",
    default=None,
    help="Iteration name to summarise (defaults to current iteration).",
)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@pass_context
def summary(
    ctx: CLIContext,
    iteration: str | None,
    sub_format: str | None,
) -> None:
    """Show a sprint summary report for an iteration.

    Displays total ticket counts and story points, a breakdown by workflow
    state, a breakdown by owner, and a list of any blocked tickets.

    When --iteration is not specified, the current active iteration is used.

    Examples:

    \b
        rally-cli summary
        rally-cli summary --iteration "Sprint 2024.01"
        rally-cli summary --format json
        rally-cli summary --iteration "FY26-Q1 Sprint 7" --format csv
    """
    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))

    if not ctx.apikey:
        result = CLIResult(
            success=False,
            data=None,
            error="RALLY_APIKEY environment variable not set. "
            "Set RALLY_APIKEY or use --apikey flag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(4)

    async def _do_summary():
        config = RallyConfig(
            server=ctx.server,
            apikey=ctx.apikey,
            workspace=ctx.workspace,
            project=ctx.project,
        )
        async with AsyncRallyClient(config) as client:
            return await client.get_sprint_summary(iteration_name=iteration)

    try:
        summary_data = asyncio.run(_do_summary())
    except Exception as exc:
        error_msg = str(exc)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            error_msg = "Authentication failed: Invalid API key"
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to fetch summary: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    result = CLIResult(success=True, data=summary_data)
    click.echo(ctx.formatter.format_summary(result))
    sys.exit(0)


# Register command with CLI
cli.add_command(summary)
