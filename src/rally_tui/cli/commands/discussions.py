"""Discussions command for viewing ticket discussion threads.

This module implements the 'discussions' command for fetching and displaying
discussion posts (comments) on a Rally ticket.
"""

import asyncio
import re
import sys

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient

# Pattern matching valid Rally ticket IDs (case-insensitive)
_TICKET_ID_RE = re.compile(r"^(US|S|DE|TA|TC|F)\d+$", re.IGNORECASE)


@click.command("discussions")
@click.argument("ticket_id")
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@pass_context
def discussions(ctx: CLIContext, ticket_id: str, sub_format: str | None) -> None:
    """Show discussion thread for a ticket.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).

    Examples:

    \b
        rally-cli discussions US12345
        rally-cli discussions US12345 --format json
        rally-cli discussions US12345 --format json | jq '.data[].text'
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

    if not _TICKET_ID_RE.match(ticket_id):
        result = CLIResult(
            success=False,
            data=None,
            error=f"Invalid ticket ID format: {ticket_id}. "
            "Ticket ID must match pattern US/S/DE/TA/TC/F followed by digits.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    result = asyncio.run(_fetch_discussions(ctx, ticket_id))

    if result.success:
        output = ctx.formatter.format_discussions(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


async def _fetch_discussions(ctx: CLIContext, ticket_id: str) -> CLIResult:
    """Fetch discussions for a ticket asynchronously.

    Args:
        ctx: CLI context with configuration.
        ticket_id: Ticket formatted ID.

    Returns:
        CLIResult with discussion data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            ticket = await client.get_ticket(ticket_id)
            if not ticket:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Ticket {ticket_id} not found.",
                )

            discussions_list = await client.get_discussions(ticket)

            return CLIResult(
                success=True,
                data={
                    "discussions": discussions_list,
                    "formatted_id": ticket_id,
                    "count": len(discussions_list),
                },
            )

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            return CLIResult(
                success=False,
                data=None,
                error="Authentication failed: Invalid API key",
            )
        return CLIResult(
            success=False,
            data=None,
            error=f"Failed to fetch discussions: {error_msg}",
        )


# Register command with CLI
cli.add_command(discussions)
