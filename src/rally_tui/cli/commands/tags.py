"""Tags command for managing Rally tags.

This module implements the 'tags' command group for listing, creating,
and managing Rally tags on tickets.
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


@click.group("tags", invoke_without_command=True)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@click.pass_context
def tags(click_ctx: click.Context, sub_format: str | None) -> None:
    """Manage Rally tags.

    Without a subcommand, lists all available tags.
    Use subcommands to create tags or add/remove tags from tickets.

    Examples:

    \b
        rally-cli tags
        rally-cli tags --format json
        rally-cli tags create "sprint-goal"
        rally-cli tags add US12345 "sprint-goal"
        rally-cli tags remove US12345 "sprint-goal"
    """
    ctx = click_ctx.obj

    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))

    if click_ctx.invoked_subcommand is not None:
        return

    # Default: list tags
    _tags_list(ctx)


def _tags_list(ctx: CLIContext) -> None:
    """Run the list-tags flow (default when no subcommand)."""
    if not ctx.apikey:
        result = CLIResult(
            success=False,
            data=None,
            error="RALLY_APIKEY environment variable not set. "
            "Set RALLY_APIKEY or use --apikey flag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(4)

    result = asyncio.run(_fetch_tags(ctx))

    if result.success:
        output = ctx.formatter.format_tags(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


async def _fetch_tags(ctx: CLIContext) -> CLIResult:
    """Fetch tags from Rally asynchronously.

    Args:
        ctx: CLI context with configuration.

    Returns:
        CLIResult with tag data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            all_tags = await client.get_tags()

            # Sort alphabetically
            all_tags.sort(key=lambda t: t.name.lower())

            return CLIResult(success=True, data=all_tags)

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
            error=f"Failed to fetch tags: {error_msg}",
        )


@tags.command("create")
@click.argument("tag_name")
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@pass_context
def tags_create(ctx: CLIContext, tag_name: str, sub_format: str | None) -> None:
    """Create a new tag in Rally.

    TAG_NAME is the name for the new tag.

    Examples:

    \b
        rally-cli tags create "sprint-goal"
        rally-cli tags create "technical-debt"
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

    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    async def _do_create():
        async with AsyncRallyClient(config) as client:
            return await client.create_tag(tag_name)

    try:
        tag = asyncio.run(_do_create())
    except Exception as exc:
        error_msg = str(exc)
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to create tag: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    if tag:
        result = CLIResult(
            success=True,
            data={"tag": tag, "action": "created"},
        )
        click.echo(ctx.formatter.format_tag_action(result))
        sys.exit(0)
    else:
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to create tag '{tag_name}'.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@tags.command("add")
@click.argument("ticket_id")
@click.argument("tag_name")
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@pass_context
def tags_add(ctx: CLIContext, ticket_id: str, tag_name: str, sub_format: str | None) -> None:
    """Add a tag to a ticket.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).
    TAG_NAME is the tag to add.

    Examples:

    \b
        rally-cli tags add US12345 "sprint-goal"
        rally-cli tags add DE67890 "technical-debt"
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

    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    async def _do_add():
        async with AsyncRallyClient(config) as client:
            ticket = await client.get_ticket(ticket_id)
            if not ticket:
                return None
            return await client.add_tag(ticket, tag_name)

    try:
        updated = asyncio.run(_do_add())
    except Exception as exc:
        error_msg = str(exc)
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to add tag: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    if updated:
        result = CLIResult(
            success=True,
            data={
                "ticket_id": ticket_id,
                "tag_name": tag_name,
                "action": "added",
            },
        )
        click.echo(ctx.formatter.format_tag_action(result))
        sys.exit(0)
    else:
        result = CLIResult(
            success=False,
            data=None,
            error=f"Ticket {ticket_id} not found or failed to add tag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@tags.command("remove")
@click.argument("ticket_id")
@click.argument("tag_name")
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@pass_context
def tags_remove(ctx: CLIContext, ticket_id: str, tag_name: str, sub_format: str | None) -> None:
    """Remove a tag from a ticket.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).
    TAG_NAME is the tag to remove.

    Examples:

    \b
        rally-cli tags remove US12345 "sprint-goal"
        rally-cli tags remove DE67890 "technical-debt"
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

    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    async def _do_remove():
        async with AsyncRallyClient(config) as client:
            ticket = await client.get_ticket(ticket_id)
            if not ticket:
                return None
            return await client.remove_tag(ticket, tag_name)

    try:
        updated = asyncio.run(_do_remove())
    except Exception as exc:
        error_msg = str(exc)
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to remove tag: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    if updated:
        result = CLIResult(
            success=True,
            data={
                "ticket_id": ticket_id,
                "tag_name": tag_name,
                "action": "removed",
            },
        )
        click.echo(ctx.formatter.format_tag_action(result))
        sys.exit(0)
    else:
        result = CLIResult(
            success=False,
            data=None,
            error=f"Ticket {ticket_id} not found or failed to remove tag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


# Register command with CLI
cli.add_command(tags)
