"""Query command for fetching tickets from Rally.

This module implements the 'tickets' command for querying Rally work items.
"""

import asyncio
import sys

import click

from rally_tui.cli.formatters.base import CLIResult
from rally_tui.cli.main import CLIContext, pass_context
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient


@click.command("tickets")
@click.option(
    "--current-iteration",
    is_flag=True,
    default=False,
    help="Show only tickets in current iteration.",
)
@click.option(
    "--my-tickets",
    is_flag=True,
    default=False,
    help="Show only tickets assigned to current user.",
)
@click.option(
    "--iteration",
    default=None,
    help="Filter by specific iteration name.",
)
@click.option(
    "--owner",
    default=None,
    help="Filter by owner display name.",
)
@click.option(
    "--state",
    default=None,
    help="Filter by workflow state.",
)
@click.option(
    "--ticket-type",
    type=click.Choice(["UserStory", "Defect", "Task", "TestCase"], case_sensitive=False),
    default=None,
    help="Filter by ticket type.",
)
@click.option(
    "--query",
    "custom_query",
    default=None,
    help="Custom Rally WSAPI query string.",
)
@click.option(
    "--fields",
    default=None,
    help="Comma-separated fields to display.",
)
@click.option(
    "--sort-by",
    default="formatted_id",
    help="Sort by field.",
)
@pass_context
def tickets(
    ctx: CLIContext,
    current_iteration: bool,
    my_tickets: bool,
    iteration: str | None,
    owner: str | None,
    state: str | None,
    ticket_type: str | None,
    custom_query: str | None,
    fields: str | None,
    sort_by: str,
) -> None:
    """Query and display tickets from Rally.

    Without flags, returns all tickets in the project (excluding Jira Migration items).
    Use --current-iteration and --my-tickets for the most common use case.

    Examples:

    \b
        # Show my tickets in current iteration
        rally-cli tickets --current-iteration --my-tickets

    \b
        # Show all tickets in a specific iteration
        rally-cli tickets --iteration "Sprint 2024.01"

    \b
        # Show all defects in current iteration
        rally-cli tickets --current-iteration --ticket-type Defect

    \b
        # Custom query with JSON output
        rally-cli tickets --query '(State = "In-Progress")' --format json
    """
    # Check for API key
    if not ctx.apikey:
        result = CLIResult(
            success=False,
            data=None,
            error="RALLY_APIKEY environment variable not set. "
            "Set RALLY_APIKEY or use --apikey flag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(4)

    # Parse fields
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",")]

    # Run async query
    result = asyncio.run(
        _fetch_tickets(
            ctx=ctx,
            current_iteration=current_iteration,
            my_tickets=my_tickets,
            iteration=iteration,
            owner=owner,
            state=state,
            ticket_type=ticket_type,
            custom_query=custom_query,
            sort_by=sort_by,
        )
    )

    # Output result
    if result.success:
        output = ctx.formatter.format_tickets(result, field_list)
        click.echo(output)
        sys.exit(0)
    else:
        output = ctx.formatter.format_error(result)
        click.echo(output, err=True)
        sys.exit(1)


async def _fetch_tickets(
    ctx: CLIContext,
    current_iteration: bool,
    my_tickets: bool,
    iteration: str | None,
    owner: str | None,
    state: str | None,
    ticket_type: str | None,
    custom_query: str | None,
    sort_by: str,
) -> CLIResult:
    """Fetch tickets from Rally asynchronously.

    Args:
        ctx: CLI context with configuration.
        current_iteration: Filter by current iteration.
        my_tickets: Filter by current user.
        iteration: Specific iteration name.
        owner: Owner display name filter.
        state: State filter.
        ticket_type: Ticket type filter.
        custom_query: Custom WSAPI query.
        sort_by: Field to sort by.

    Returns:
        CLIResult with ticket data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            # Build query based on options
            query = _build_query(
                client=client,
                current_iteration=current_iteration,
                my_tickets=my_tickets,
                iteration=iteration,
                owner=owner,
                state=state,
                ticket_type=ticket_type,
                custom_query=custom_query,
            )

            # Fetch tickets
            tickets = await client.get_tickets(query)

            # Filter by ticket type if specified (post-filter since we fetch all types)
            if ticket_type:
                type_map = {
                    "userstory": "UserStory",
                    "defect": "Defect",
                    "task": "Task",
                    "testcase": "TestCase",
                }
                normalized_type = type_map.get(ticket_type.lower(), ticket_type)
                tickets = [t for t in tickets if t.ticket_type == normalized_type]

            # Sort tickets
            reverse = False
            if sort_by.startswith("-"):
                reverse = True
                sort_by = sort_by[1:]

            def sort_key(t):
                value = getattr(t, sort_by, "")
                if value is None:
                    return ""
                return value

            tickets.sort(key=sort_key, reverse=reverse)

            return CLIResult(success=True, data=tickets)

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
            error=f"Failed to fetch tickets: {error_msg}",
        )


def _build_query(
    client: AsyncRallyClient,
    current_iteration: bool,
    my_tickets: bool,
    iteration: str | None,
    owner: str | None,
    state: str | None,
    ticket_type: str | None,
    custom_query: str | None,
) -> str | None:
    """Build Rally WSAPI query from options.

    Args:
        client: AsyncRallyClient for accessing current user/iteration.
        current_iteration: Use current iteration.
        my_tickets: Filter by current user.
        iteration: Specific iteration name.
        owner: Owner display name.
        state: State filter.
        ticket_type: Ticket type filter (not used in query, filtered post-fetch).
        custom_query: Custom query string.

    Returns:
        Rally WSAPI query string or None.
    """
    if custom_query:
        return custom_query

    conditions = []

    # Project scoping
    if client.project:
        conditions.append(f'(Project.Name = "{client.project}")')

    # Exclude Jira Migration
    conditions.append('(Owner.DisplayName != "Jira Migration")')

    # Iteration filter
    if iteration:
        conditions.append(f'(Iteration.Name = "{iteration}")')
    elif current_iteration and client.current_iteration:
        conditions.append(f'(Iteration.Name = "{client.current_iteration}")')

    # Owner filter
    if owner:
        conditions.append(f'(Owner.DisplayName = "{owner}")')
    elif my_tickets and client.current_user:
        conditions.append(f'(Owner.DisplayName = "{client.current_user}")')

    # State filter
    if state:
        conditions.append(f'(FlowState.Name = "{state}")')

    if not conditions:
        return None

    # Build nested AND query
    if len(conditions) == 1:
        return conditions[0]

    result = conditions[0]
    for condition in conditions[1:]:
        result = f"({result} AND {condition})"

    return result


# Register command with CLI
from rally_tui.cli.main import cli

cli.add_command(tickets)
