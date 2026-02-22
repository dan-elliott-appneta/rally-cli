"""Iterations command for viewing project sprints.

This module implements the 'iterations' command for fetching and displaying
Rally iterations (sprints) with filtering options.
"""

import asyncio
import sys
from datetime import date

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.models import Iteration
from rally_tui.services.async_rally_client import AsyncRallyClient


@click.command("iterations")
@click.option(
    "--count",
    type=int,
    default=5,
    help="Number of iterations to show (default: 5).",
)
@click.option(
    "--current",
    "show_current",
    is_flag=True,
    default=False,
    help="Show only the current iteration.",
)
@click.option(
    "--future",
    "show_future",
    is_flag=True,
    default=False,
    help="Show future iterations.",
)
@click.option(
    "--past",
    "show_past",
    is_flag=True,
    default=False,
    help="Show past iterations only.",
)
@click.option(
    "--state",
    default=None,
    help="Filter by state (Planning, Committed, Accepted).",
)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@pass_context
def iterations(
    ctx: CLIContext,
    count: int,
    show_current: bool,
    show_future: bool,
    show_past: bool,
    state: str | None,
    sub_format: str | None,
) -> None:
    """Show project iterations (sprints).

    Without flags, shows recent iterations including current and past sprints.
    Use --current, --future, or --past to filter by time period.

    Examples:

    \b
        rally-cli iterations
        rally-cli iterations --count 10
        rally-cli iterations --current
        rally-cli iterations --future
        rally-cli iterations --past
        rally-cli iterations --state "Committed"
        rally-cli iterations --format json
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
        _fetch_iterations(
            ctx=ctx,
            count=count,
            show_current=show_current,
            show_future=show_future,
            show_past=show_past,
            state=state,
        )
    )

    if result.success:
        output = ctx.formatter.format_iterations(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


async def _fetch_iterations(
    ctx: CLIContext,
    count: int,
    show_current: bool,
    show_future: bool,
    show_past: bool,
    state: str | None,
) -> CLIResult:
    """Fetch iterations from Rally asynchronously.

    Args:
        ctx: CLI context with configuration.
        count: Maximum number of iterations to fetch.
        show_current: Show only the current iteration.
        show_future: Show future iterations.
        show_past: Show past iterations only.
        state: Filter by iteration state.

    Returns:
        CLIResult with iteration data or error.
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
            needs_filter = show_current or show_future or show_past or state
            fetch_count = count * 3 if needs_filter else count
            all_iterations = await client.get_iterations(fetch_count)

            # Apply time-based filters
            filtered = _filter_iterations(
                all_iterations,
                show_current=show_current,
                show_future=show_future,
                show_past=show_past,
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
            error=f"Failed to fetch iterations: {error_msg}",
        )


def _filter_iterations(
    iterations_list: list[Iteration],
    show_current: bool,
    show_future: bool,
    show_past: bool,
    state: str | None,
) -> list[Iteration]:
    """Apply filters to the iteration list.

    Args:
        iterations_list: List of iterations to filter.
        show_current: Show only current iteration.
        show_future: Show future iterations.
        show_past: Show past iterations only.
        state: Filter by state name.

    Returns:
        Filtered list of iterations.
    """
    today = date.today()
    filtered = list(iterations_list)

    if show_current:
        filtered = [it for it in filtered if it.is_current]
    elif show_future:
        filtered = [it for it in filtered if it.start_date > today]
    elif show_past:
        filtered = [it for it in filtered if it.end_date < today]

    if state:
        state_lower = state.lower()
        filtered = [it for it in filtered if it.state.lower() == state_lower]

    return filtered


# Register command with CLI
cli.add_command(iterations)
