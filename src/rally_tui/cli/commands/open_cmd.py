"""Open command for launching tickets in the web browser.

This module implements the 'open' command for opening Rally tickets
in the default web browser by constructing the correct Rally URL.
"""

import asyncio
import sys
import webbrowser

import click

from rally_tui.cli.commands._common import require_apikey, require_valid_ticket_id
from rally_tui.cli.formatters.base import CLIResult
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient


@click.command("open")
@click.argument("ticket_id")
@pass_context
def open_ticket(ctx: CLIContext, ticket_id: str) -> None:
    """Open a Rally ticket in the web browser.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890, F59625).
    The ticket is looked up to get its ObjectID, then the Rally web
    URL is constructed and opened in the default browser.

    Examples:

    \b
        rally-cli open US12345
        rally-cli open DE67890
        rally-cli open F59625
    """
    require_apikey(ctx)
    require_valid_ticket_id(ctx, ticket_id)

    async def _do_open() -> str | None:
        config = RallyConfig(
            server=ctx.server,
            apikey=ctx.apikey,
            workspace=ctx.workspace,
            project=ctx.project,
        )
        async with AsyncRallyClient(config) as client:
            ticket = await client.get_ticket(ticket_id)
            if not ticket:
                return None
            return ticket.rally_url(ctx.server)

    try:
        url = asyncio.run(_do_open())
    except Exception as exc:
        error_msg = str(exc)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            error_msg = "Authentication failed: Invalid API key"
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to open ticket: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    if url is None:
        result = CLIResult(
            success=False,
            data=None,
            error=f"Ticket {ticket_id} not found or has no ObjectID.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    click.echo(f"Opening {ticket_id}: {url}")
    webbrowser.open(url)
    sys.exit(0)


# Register command with CLI
cli.add_command(open_ticket, name="open")
