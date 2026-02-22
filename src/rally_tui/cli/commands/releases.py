"""Releases command for viewing project releases.

This module implements the 'releases' command for fetching and displaying
Rally releases with filtering options.
"""

import asyncio
import sys

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.models import Release
from rally_tui.services.async_rally_client import AsyncRallyClient


@click.command("releases")
@click.option(
    "--count",
    type=int,
    default=10,
    help="Number of releases to show (default: 10).",
)
@click.option(
    "--current",
    "show_current",
    is_flag=True,
    default=False,
    help="Show only the current/active release.",
)
@click.option(
    "--state",
    default=None,
    help="Filter by state (Planning, Active, Locked).",
)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@pass_context
def releases(
    ctx: CLIContext,
    count: int,
    show_current: bool,
    state: str | None,
    sub_format: str | None,
) -> None:
    """Show project releases.

    Without flags, shows recent releases. Use --current to show only the
    active release. Use --state to filter by release state.

    Examples:

    \b
        rally-cli releases
        rally-cli releases --count 10
        rally-cli releases --current
        rally-cli releases --state "Active"
        rally-cli releases --format json
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

    result = asyncio.run(
        _fetch_releases(
            ctx=ctx,
            count=count,
            show_current=show_current,
            state=state,
        )
    )

    if result.success:
        output = ctx.formatter.format_releases(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


async def _fetch_releases(
    ctx: CLIContext,
    count: int,
    show_current: bool,
    state: str | None,
) -> CLIResult:
    """Fetch releases from Rally asynchronously.

    Args:
        ctx: CLI context with configuration.
        count: Maximum number of releases to fetch.
        show_current: Show only the current release.
        state: Filter by release state.

    Returns:
        CLIResult with release data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            # Fetch more than needed so filtering still yields results
            needs_filter = show_current or state
            fetch_count = count * 3 if needs_filter else count
            all_releases = await client.get_releases(fetch_count)

            # Apply filters
            filtered = _filter_releases(
                all_releases,
                show_current=show_current,
                state=state,
            )

            # Limit to requested count
            filtered = filtered[:count]

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
            error=f"Failed to fetch releases: {error_msg}",
        )


def _filter_releases(
    releases_list: list[Release],
    show_current: bool,
    state: str | None,
) -> list[Release]:
    """Apply filters to the release list.

    Args:
        releases_list: List of releases to filter.
        show_current: Show only the current release.
        state: Filter by state name.

    Returns:
        Filtered list of releases.
    """
    filtered = list(releases_list)

    if show_current:
        filtered = [r for r in filtered if r.is_current]

    if state:
        state_lower = state.lower()
        filtered = [r for r in filtered if r.state.lower() == state_lower]

    return filtered


# Register command with CLI
cli.add_command(releases)
