"""Shared helpers for CLI command implementations."""

import re
import sys
from collections.abc import Callable

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext

# Pattern matching valid Rally ticket IDs (case-insensitive)
TICKET_ID_RE = re.compile(r"^(US|S|DE|TA|TC|F)\d+$", re.IGNORECASE)


def format_option(f: Callable) -> Callable:
    """Add the standard per-command --format override option."""
    return click.option(
        "--format",
        "sub_format",
        type=click.Choice(["text", "json", "csv"], case_sensitive=False),
        default=None,
        help="Output format (overrides global --format).",
    )(f)


def apply_format_override(ctx: CLIContext, sub_format: str | None) -> None:
    """Apply a per-command --format override, if one was given."""
    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))


def require_apikey(ctx: CLIContext) -> None:
    """Exit with a formatted error if no Rally API key is configured."""
    if ctx.apikey:
        return
    result = CLIResult(
        success=False,
        data=None,
        error="RALLY_APIKEY environment variable not set. Set RALLY_APIKEY or use --apikey flag.",
    )
    click.echo(ctx.formatter.format_error(result), err=True)
    sys.exit(4)


def require_valid_ticket_id(ctx: CLIContext, ticket_id: str) -> None:
    """Exit with a formatted error if ticket_id doesn't match TICKET_ID_RE."""
    if TICKET_ID_RE.match(ticket_id):
        return
    result = CLIResult(
        success=False,
        data=None,
        error=f"Invalid ticket ID format: {ticket_id}. "
        "Ticket ID must match pattern US/S/DE/TA/TC/F followed by digits.",
    )
    click.echo(ctx.formatter.format_error(result), err=True)
    sys.exit(2)
