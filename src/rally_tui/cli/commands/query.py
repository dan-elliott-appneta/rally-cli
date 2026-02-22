"""Query command for fetching tickets from Rally.

This module implements the 'tickets' command for querying Rally work items.
"""

import asyncio
import re
import sys
from datetime import date as date_type

import click

from rally_tui.cli.formatters.base import CLIResult
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.models import Ticket
from rally_tui.services.async_rally_client import AsyncRallyClient

# Pattern matching valid Rally ticket IDs (case-insensitive)
_TICKET_ID_RE = re.compile(r"^(US|S|DE|TA|TC|F)\d+$", re.IGNORECASE)


def _sanitize_query_value(value: str) -> str:
    """Sanitize user input for Rally WSAPI query.

    Escapes quotes and backslashes to prevent query injection.

    Args:
        value: User-provided value to sanitize.

    Returns:
        Sanitized value safe for use in WSAPI query.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _validate_date(ctx: click.Context, param: click.Parameter, value: str | None) -> str | None:
    """Validate that a date string matches YYYY-MM-DD format.

    Args:
        ctx: Click context (unused).
        param: Click parameter (unused).
        value: The date string to validate.

    Returns:
        The validated date string, or None if not provided.

    Raises:
        click.BadParameter: If the date string is not valid YYYY-MM-DD.
    """
    if value is None:
        return None
    try:
        date_type.fromisoformat(value)
    except ValueError:
        raise click.BadParameter(f"'{value}' is not a valid date. Use YYYY-MM-DD format.")
    return value


def _is_valid_ticket_id(ticket_id: str) -> bool:
    """Validate that a ticket ID matches the expected Rally format.

    Args:
        ticket_id: The ticket ID string to validate.

    Returns:
        True if the format is valid, False otherwise.
    """
    return bool(_TICKET_ID_RE.match(ticket_id))


# Map CLI type names to Rally entity types
CREATE_TYPE_MAP = {
    "userstory": "HierarchicalRequirement",
    "defect": "Defect",
}


@click.group("tickets", invoke_without_command=True)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
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
@click.pass_context
def tickets(
    click_ctx: click.Context,
    sub_format: str | None,
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
    Use 'tickets create' to create a new ticket.

    Examples:

    \b
        # Show my tickets in current iteration
        rally-cli tickets --current-iteration --my-tickets

    \b
        # Show all tickets in a specific iteration
        rally-cli tickets --iteration "Sprint 2024.01"

    \b
        # Create a new ticket
        rally-cli tickets create "My Story" --description "Brief description" --points 1

    \b
        # Custom query with JSON output
        rally-cli tickets --query '(State = "In-Progress")' --format json
    """
    ctx = click_ctx.obj

    # Apply sub-format override before any subcommand or list runs so that
    # subcommands that inherit the context also see the updated formatter.
    if sub_format:
        from rally_tui.cli.formatters.base import OutputFormat
        ctx.set_format(OutputFormat(sub_format.lower()))

    if click_ctx.invoked_subcommand is not None:
        return

    _tickets_list(
        ctx=ctx,
        current_iteration=current_iteration,
        my_tickets=my_tickets,
        iteration=iteration,
        owner=owner,
        state=state,
        ticket_type=ticket_type,
        custom_query=custom_query,
        fields=fields,
        sort_by=sort_by,
    )


def _tickets_list(
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
    """Run the list-tickets flow (default when no subcommand)."""
    if not ctx.apikey:
        result = CLIResult(
            success=False,
            data=None,
            error="RALLY_APIKEY environment variable not set. "
            "Set RALLY_APIKEY or use --apikey flag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(4)

    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",")]

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

    if result.success:
        output = ctx.formatter.format_tickets(result, field_list)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@tickets.command("create")
@click.argument("name")
@click.option(
    "--description",
    default="",
    help="Ticket description.",
)
@click.option(
    "--points",
    type=float,
    default=None,
    help="Story points to set on the ticket.",
)
@click.option(
    "--type",
    "ticket_type",
    type=click.Choice(["UserStory", "Defect"], case_sensitive=False),
    default="UserStory",
    help="Ticket type (default: UserStory).",
)
@click.option(
    "--backlog",
    is_flag=True,
    default=False,
    help="Put the ticket in the backlog (do not assign to current iteration).",
)
@pass_context
def tickets_create(
    ctx: CLIContext,
    name: str,
    description: str,
    points: float | None,
    ticket_type: str,
    backlog: bool,
) -> None:
    """Create a new ticket in Rally.

    Creates a User Story or Defect with the current user as owner and
    current iteration, if available. Use --backlog to leave the ticket
    in the backlog for planning.

    Examples:

    \b
        rally-cli tickets create "Ticket Name" --description "Brief description" --points 1
        rally-cli tickets create "Bug in login" --type Defect --description "Repro steps..."
        rally-cli tickets create "Future idea" --backlog
    """
    if not ctx.apikey:
        result = CLIResult(
            success=False,
            data=None,
            error="RALLY_APIKEY environment variable not set. "
            "Set RALLY_APIKEY or use --apikey flag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(4)

    entity_type = CREATE_TYPE_MAP.get(ticket_type.lower(), "HierarchicalRequirement")
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    async def _do_create() -> Ticket | None:
        async with AsyncRallyClient(config) as client:
            return await client.create_ticket(
                title=name,
                ticket_type=entity_type,
                description=description,
                points=points,
                backlog=backlog,
            )

    created = asyncio.run(_do_create())
    if created:
        result = CLIResult(success=True, data=[created])
        click.echo(ctx.formatter.format_tickets(result))
        sys.exit(0)
    else:
        result = CLIResult(
            success=False,
            data=None,
            error="Failed to create ticket.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@tickets.command("show")
@click.argument("ticket_id")
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@pass_context
def tickets_show(ctx: CLIContext, ticket_id: str, sub_format: str | None) -> None:
    """Show detailed information for a single ticket.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).

    Examples:

    \b
        rally-cli tickets show US12345
        rally-cli tickets show DE67890 --format json
    """
    if sub_format:
        from rally_tui.cli.formatters.base import OutputFormat
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

    if not _is_valid_ticket_id(ticket_id):
        result = CLIResult(
            success=False,
            data=None,
            error=f"Invalid ticket ID format: {ticket_id}. "
            "Ticket ID must match pattern US/S/DE/TA/TC/F followed by digits.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    async def _do_show() -> Ticket | None:
        config = RallyConfig(
            server=ctx.server,
            apikey=ctx.apikey,
            workspace=ctx.workspace,
            project=ctx.project,
        )
        async with AsyncRallyClient(config) as client:
            return await client.get_ticket(ticket_id)

    try:
        ticket = asyncio.run(_do_show())
    except Exception as exc:
        error_msg = str(exc)
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to fetch ticket: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    if ticket:
        result = CLIResult(success=True, data=ticket)
        click.echo(ctx.formatter.format_ticket_detail(result))
        sys.exit(0)
    else:
        result = CLIResult(
            success=False,
            data=None,
            error=f"Ticket {ticket_id} not found.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@tickets.command("update")
@click.argument("ticket_id")
@click.option("--state", default=None, help="Workflow state.")
@click.option("--owner", "new_owner", default=None, help="Owner display name.")
@click.option("--iteration", default=None, help="Iteration name.")
@click.option(
    "--no-iteration", is_flag=True, default=False, help="Remove from iteration (backlog)."
)
@click.option("--points", type=float, default=None, help="Story points.")
@click.option("--parent", default=None, help="Parent Feature ID.")
@click.option("--name", "new_name", default=None, help="Rename ticket.")
@click.option("--description", default=None, help="Set description.")
@click.option(
    "--description-file",
    type=click.Path(exists=True),
    default=None,
    help="Set description from file.",
)
@click.option("--notes", default=None, help="Set notes.")
@click.option(
    "--notes-file",
    type=click.Path(exists=True),
    default=None,
    help="Set notes from file.",
)
@click.option("--ac", default=None, help="Set acceptance criteria.")
@click.option(
    "--ac-file",
    type=click.Path(exists=True),
    default=None,
    help="Set acceptance criteria from file.",
)
@click.option("--blocked/--no-blocked", default=None, help="Set/clear blocked status.")
@click.option("--blocked-reason", default=None, help="Reason for blocking.")
@click.option("--ready/--no-ready", default=None, help="Set/clear ready status.")
@click.option("--expedite/--no-expedite", default=None, help="Set/clear expedite flag.")
@click.option("--severity", default=None, help="Severity (Defect only).")
@click.option("--priority", default=None, help="Priority (Defect only).")
@click.option(
    "--target-date", default=None, callback=_validate_date,
    help="Target date (YYYY-MM-DD).",
)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@pass_context
def tickets_update(
    ctx: CLIContext,
    ticket_id: str,
    sub_format: str | None,
    state: str | None,
    new_owner: str | None,
    iteration: str | None,
    no_iteration: bool,
    points: float | None,
    parent: str | None,
    new_name: str | None,
    description: str | None,
    description_file: str | None,
    notes: str | None,
    notes_file: str | None,
    ac: str | None,
    ac_file: str | None,
    blocked: bool | None,
    blocked_reason: str | None,
    ready: bool | None,
    expedite: bool | None,
    severity: str | None,
    priority: str | None,
    target_date: str | None,
) -> None:
    """Update fields on an existing ticket.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).

    Examples:

    \b
        rally-cli tickets update US12345 --state "In-Progress" --points 3
        rally-cli tickets update DE67890 --owner "Jane Smith" --priority High
        rally-cli tickets update US12345 --description-file desc.txt
        rally-cli tickets update US12345 --no-iteration
    """
    if sub_format:
        from rally_tui.cli.formatters.base import OutputFormat
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

    if not _is_valid_ticket_id(ticket_id):
        result = CLIResult(
            success=False,
            data=None,
            error=f"Invalid ticket ID format: {ticket_id}. "
            "Ticket ID must match pattern US/S/DE/TA/TC/F followed by digits.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    # Read file-based options
    if description_file:
        with open(description_file) as f:
            description = f.read()
    if notes_file:
        with open(notes_file) as f:
            notes = f.read()
    if ac_file:
        with open(ac_file) as f:
            ac = f.read()

    # Build fields dict - map CLI option names to Rally field names
    fields: dict = {}
    changes: dict = {}

    if state is not None:
        fields["state"] = state
        changes["state"] = state
    if new_owner is not None:
        fields["owner"] = new_owner
        changes["owner"] = new_owner
    if no_iteration:
        fields["iteration"] = None
        changes["iteration"] = "backlog"
    elif iteration is not None:
        fields["iteration"] = iteration
        changes["iteration"] = iteration
    if points is not None:
        fields["PlanEstimate"] = points
        changes["points"] = points
    if parent is not None:
        fields["parent"] = parent
        changes["parent"] = parent
    if new_name is not None:
        fields["Name"] = new_name
        changes["name"] = new_name
    if description is not None:
        fields["Description"] = description
        changes["description"] = "(updated)"
    if notes is not None:
        fields["Notes"] = notes
        changes["notes"] = "(updated)"
    if ac is not None:
        fields["c_AcceptanceCriteria"] = ac
        changes["ac"] = "(updated)"
    if blocked is not None:
        fields["Blocked"] = blocked
        changes["blocked"] = blocked
    if blocked_reason is not None:
        fields["BlockedReason"] = blocked_reason
        changes["blocked_reason"] = blocked_reason
    if ready is not None:
        fields["Ready"] = ready
        changes["ready"] = ready
    if expedite is not None:
        fields["Expedite"] = expedite
        changes["expedite"] = expedite
    if severity is not None:
        fields["Severity"] = severity
        changes["severity"] = severity
    if priority is not None:
        fields["Priority"] = priority
        changes["priority"] = priority
    if target_date is not None:
        fields["TargetDate"] = target_date
        changes["target_date"] = target_date

    if not fields:
        result = CLIResult(
            success=False,
            data=None,
            error="No fields to update. Provide at least one update option.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    async def _do_update() -> Ticket | None:
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
            return await client.update_ticket(ticket, fields)

    try:
        updated_ticket = asyncio.run(_do_update())
    except Exception as exc:
        error_msg = str(exc)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            error_msg = "Authentication failed: Invalid API key"
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to update ticket: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    if updated_ticket:
        result = CLIResult(
            success=True,
            data={
                "formatted_id": updated_ticket.formatted_id,
                "ticket": updated_ticket,
                "changes": changes,
            },
        )
        click.echo(ctx.formatter.format_update_result(result))
        sys.exit(0)
    else:
        result = CLIResult(
            success=False,
            data=None,
            error=f"Ticket {ticket_id} not found or update failed.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@tickets.command("delete")
@click.argument("ticket_id")
@click.option(
    "--confirm",
    is_flag=True,
    required=True,
    help="Required safety flag - must be provided to confirm deletion.",
)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@pass_context
def tickets_delete(ctx: CLIContext, ticket_id: str, confirm: bool, sub_format: str | None) -> None:
    """Delete a ticket from Rally.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).
    The --confirm flag is required as a safety measure.

    Examples:

    \b
        rally-cli tickets delete US12345 --confirm
    """
    if sub_format:
        from rally_tui.cli.formatters.base import OutputFormat
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

    if not _is_valid_ticket_id(ticket_id):
        result = CLIResult(
            success=False,
            data=None,
            error=f"Invalid ticket ID format: {ticket_id}. "
            "Ticket ID must match pattern US/S/DE/TA/TC/F followed by digits.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    async def _do_delete() -> bool:
        config = RallyConfig(
            server=ctx.server,
            apikey=ctx.apikey,
            workspace=ctx.workspace,
            project=ctx.project,
        )
        async with AsyncRallyClient(config) as client:
            return await client.delete_ticket(ticket_id)

    try:
        deleted = asyncio.run(_do_delete())
    except Exception as exc:
        error_msg = str(exc)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            error_msg = "Authentication failed: Invalid API key"
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to delete ticket: {error_msg}",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)

    if deleted:
        result = CLIResult(
            success=True,
            data={"formatted_id": ticket_id, "deleted": True},
        )
        click.echo(ctx.formatter.format_delete_result(result))
        sys.exit(0)
    else:
        result = CLIResult(
            success=False,
            data=None,
            error=f"Failed to delete ticket {ticket_id}.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
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
                value = getattr(t, sort_by, None)
                if value is None:
                    return ""
                return str(value) if not isinstance(value, (str, int, float)) else value

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
        sanitized_iteration = _sanitize_query_value(iteration)
        conditions.append(f'(Iteration.Name = "{sanitized_iteration}")')
    elif current_iteration and client.current_iteration:
        sanitized_iteration = _sanitize_query_value(client.current_iteration)
        conditions.append(f'(Iteration.Name = "{sanitized_iteration}")')

    # Owner filter
    if owner:
        sanitized_owner = _sanitize_query_value(owner)
        conditions.append(f'(Owner.DisplayName = "{sanitized_owner}")')
    elif my_tickets and client.current_user:
        sanitized_user = _sanitize_query_value(client.current_user)
        conditions.append(f'(Owner.DisplayName = "{sanitized_user}")')

    # State filter
    if state:
        sanitized_state = _sanitize_query_value(state)
        conditions.append(f'(FlowState.Name = "{sanitized_state}")')

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
cli.add_command(tickets)
