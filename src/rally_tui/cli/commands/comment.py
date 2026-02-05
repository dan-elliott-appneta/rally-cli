"""Comment command for adding comments to Rally tickets.

This module implements the 'comment' command for posting discussion comments.
"""

import asyncio
import sys

import click

from rally_tui.cli.formatters.base import CLIResult
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient

# Rally typically allows 32000 characters for comment text
MAX_COMMENT_LENGTH = 32000


@click.command("comment")
@click.argument("ticket_id")
@click.argument("message", required=False)
@click.option(
    "--message-file",
    type=click.Path(exists=True, allow_dash=True),
    default=None,
    help="Read comment text from file (use - for stdin).",
)
@pass_context
def comment(
    ctx: CLIContext,
    ticket_id: str,
    message: str | None,
    message_file: str | None,
) -> None:
    """Add a comment to a ticket's discussion.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).
    MESSAGE is the comment text (can also use --message-file).

    Examples:

    \b
        # Add comment with inline text
        rally-cli comment US12345 "Updated the implementation"

    \b
        # Add comment from file
        rally-cli comment US12345 --message-file comment.txt

    \b
        # Add comment from stdin
        echo "Deployment complete" | rally-cli comment US12345 --message-file -
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

    # Validate ticket ID format
    if not _is_valid_ticket_id(ticket_id):
        result = CLIResult(
            success=False,
            data=None,
            error=f"Invalid ticket ID format: {ticket_id}. "
            "Ticket ID must start with US, DE, TA, or TC.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    # Get message text
    comment_text = _get_message_text(message, message_file)
    if not comment_text:
        result = CLIResult(
            success=False,
            data=None,
            error="No comment text provided. Use MESSAGE argument or --message-file option.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    # Validate comment length
    if len(comment_text) > MAX_COMMENT_LENGTH:
        result = CLIResult(
            success=False,
            data=None,
            error=f"Comment exceeds {MAX_COMMENT_LENGTH} character limit",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    # Run async comment
    result = asyncio.run(_add_comment(ctx, ticket_id, comment_text))

    # Output result
    if result.success:
        output = ctx.formatter.format_comment(result)
        click.echo(output)
        sys.exit(0)
    else:
        output = ctx.formatter.format_error(result)
        click.echo(output, err=True)
        sys.exit(1)


def _is_valid_ticket_id(ticket_id: str) -> bool:
    """Validate ticket ID format.

    Args:
        ticket_id: The ticket ID to validate.

    Returns:
        True if valid, False otherwise.
    """
    prefixes = ("US", "DE", "TA", "TC")
    ticket_upper = ticket_id.upper()
    for prefix in prefixes:
        if ticket_upper.startswith(prefix):
            # Check that remaining characters are digits
            remaining = ticket_upper[len(prefix) :]
            return remaining.isdigit() and len(remaining) > 0
    return False


def _get_message_text(message: str | None, message_file: str | None) -> str | None:
    """Get comment text from argument or file.

    Args:
        message: Inline message text.
        message_file: Path to file containing message (- for stdin).

    Returns:
        The message text, or None if not provided.
    """
    if message:
        return message

    if message_file:
        if message_file == "-":
            # Read from stdin
            return sys.stdin.read().strip()
        else:
            # Read from file
            with open(message_file) as f:
                return f.read().strip()

    return None


async def _add_comment(ctx: CLIContext, ticket_id: str, text: str) -> CLIResult:
    """Add comment to ticket asynchronously.

    Args:
        ctx: CLI context with configuration.
        ticket_id: Ticket formatted ID.
        text: Comment text.

    Returns:
        CLIResult with comment data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            # First, fetch the ticket to get object_id
            ticket = await client.get_ticket(ticket_id)

            if not ticket:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Ticket {ticket_id} not found",
                )

            # Add the comment
            discussion = await client.add_comment(ticket, text)

            if discussion:
                return CLIResult(success=True, data=discussion)
            else:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Failed to add comment to {ticket_id}",
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
            error=f"Failed to add comment: {error_msg}",
        )


# Register command with CLI
cli.add_command(comment)
