"""Search command for full-text ticket search across Rally.

This module implements the 'search' command for searching Rally work items
by text across the Name and Description fields.
"""

import asyncio
import sys

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient


@click.command("search")
@click.argument("query")
@click.option(
    "--type",
    "ticket_type",
    type=click.Choice(["UserStory", "Defect", "Task", "TestCase"], case_sensitive=False),
    default=None,
    help="Filter results by ticket type.",
)
@click.option(
    "--state",
    default=None,
    help="Filter results by workflow state.",
)
@click.option(
    "--current-iteration",
    is_flag=True,
    default=False,
    help="Limit results to the current iteration.",
)
@click.option(
    "--limit",
    type=int,
    default=50,
    show_default=True,
    help="Maximum number of results to return.",
)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@pass_context
def search(
    ctx: CLIContext,
    query: str,
    ticket_type: str | None,
    state: str | None,
    current_iteration: bool,
    limit: int,
    sub_format: str | None,
) -> None:
    """Search tickets by full-text across Name and Description.

    QUERY is the text to search for. Results are filtered across all ticket
    types unless --type is specified. Use --state to further narrow results.

    Examples:

    \b
        rally-cli search "OAuth login"
        rally-cli search "OAuth login" --type UserStory
        rally-cli search "login bug" --state "In-Progress"
        rally-cli search "payment" --current-iteration --limit 20
        rally-cli search "API" --format json
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

    async def _do_search():
        config = RallyConfig(
            server=ctx.server,
            apikey=ctx.apikey,
            workspace=ctx.workspace,
            project=ctx.project,
        )
        async with AsyncRallyClient(config) as client:
            return await client.search_tickets(
                text=query,
                ticket_type=ticket_type,
                state=state,
                current_iteration=current_iteration,
                limit=limit,
            )

    try:
        tickets = asyncio.run(_do_search())
    except Exception as exc:
        error_msg = str(exc)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            error_msg = "Authentication failed: Invalid API key"
        result = CLIResult(
            success=False,
            data=None,
            error=f"Search failed: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    result = CLIResult(success=True, data=tickets)
    click.echo(ctx.formatter.format_tickets(result))
    sys.exit(0)


# Register command with CLI
cli.add_command(search)
