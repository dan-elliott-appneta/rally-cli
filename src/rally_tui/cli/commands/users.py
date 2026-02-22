"""Users command for listing project members.

This module implements the 'users' command for fetching and displaying
Rally project users/members with optional search filtering.
"""

import asyncio
import sys

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.models import Owner
from rally_tui.services.async_rally_client import AsyncRallyClient


@click.command("users")
@click.option(
    "--search",
    default=None,
    help="Filter users by display name (substring match).",
)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@pass_context
def users(ctx: CLIContext, search: str | None, sub_format: str | None) -> None:
    """Show project members/users.

    Without options, lists all users in the project.
    Use --search to filter by display name.

    Examples:

    \b
        rally-cli users
        rally-cli users --format json
        rally-cli users --search "Daniel"
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

    result = asyncio.run(_fetch_users(ctx, search))

    if result.success:
        output = ctx.formatter.format_users(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


async def _fetch_users(ctx: CLIContext, search: str | None) -> CLIResult:
    """Fetch users from Rally asynchronously.

    Args:
        ctx: CLI context with configuration.
        search: Optional search string for display name filtering.

    Returns:
        CLIResult with user data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            all_users = await client.get_users()

            # Apply search filter (substring match, case-insensitive)
            if search:
                search_lower = search.lower()
                filtered: list[Owner] = [
                    u for u in all_users if search_lower in u.display_name.lower()
                ]
            else:
                filtered = all_users

            # Sort by display name
            filtered.sort(key=lambda u: u.display_name.lower())

            return CLIResult(success=True, data=filtered)

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
            error=f"Failed to fetch users: {error_msg}",
        )


# Register command with CLI
cli.add_command(users)
